import os
import json
import torch
import whisper
import yt_dlp
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI
from googleapiclient.discovery import build

# 1. API 키 설정 (환경 변수 또는 사이드바 입력)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

# 2. Whisper 모델 캐싱 로드 (속도 최적화)
@st.cache_resource
def load_whisper_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    # 코랩 환경을 고려해 base 모델을 사용하되, 필요시 medium 등으로 변경 가능합니다.
    return whisper.load_model("base").to(device)

model = load_whisper_model()

# 작업용 폴더 생성
os.makedirs("audios", exist_ok=True)
os.makedirs("summaries", exist_ok=True)

# 3. GPT 프롬프트 생성 함수
def make_prompt(text, video_id):
    return f"""
다음은 Whisper로 추출한 유튜브 영상 자막입니다. 각 문장에는 시작 타임스탬프가 포함되어 있습니다.
형식은 [MM:SS / 초]이며, 초 단위는 스트림릿에서 버튼 클릭 시 영상 시점 점프에 활용됩니다.

다음 조건에 따라 제품/장소 리뷰를 정리해 주세요:

1. 언급된 제품/장소별로 구분해서 영역을 나누어 정리해 주세요.
2. 각 항목에 대해 아래 내용을 포함해 주세요:
   - 제품명 또는 장소명 (유추 가능하면 유추해서 작성)
   - 주요 특징 및 장점
   - 추천 대상
   - 주의 사항
3. 각각의 언급 시점은 플레이어를 제어하는 "seekToTime(초)" 자바스크립트 함수 버튼으로 작성해 주세요.
   - 예시 HTML 코드: <button onclick="seekToTime(42)" style="padding:5px 10px; background:#ff4b4b; color:white; border:none; border-radius:4px; cursor:pointer;">⏳ 00:42 보기</button>
4. 실제 외부 유튜브 링크(https://youtu.be/... 나 <a> 태그)는 절대 사용하지 마세요.
5. HTML 형식 안에서 자연스럽고 가독성 좋게 작성해 주세요.
6. 전체 흐름 요약은 하지 말고, 오직 제품/장소별 정리에만 집중해 주세요.

--- 자막 시작 ---
{text}
"""

# 4. 유튜브 오디오 다운로드 및 자막 추출 함수
def extract_transcript(vid):
    audio_path = f"audios/{vid}.mp3"
    transcript_path = f"transcript_{vid}.json"

    if not os.path.exists(audio_path):
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f"audios/{vid}.%(ext)s",
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={vid}"])

    if not os.path.exists(transcript_path):
        result = model.transcribe(audio_path)
        with open(transcript_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
    else:
        with open(transcript_path, "r", encoding="utf-8") as f:
            result = json.load(f)

    return "\n".join([
        f"[{int(s['start']) // 60:02d}:{int(s['start']) % 60:02d} / {int(s['start'])}초] {s['text']}"
        for s in result["segments"]
    ])

# 5. GPT 요약 함수
def gpt_summarize(prompt):
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content

# 6. Streamlit 웹 UI 구성
st.set_page_config(layout="wide")
st.title("🎬 YouTube 영상 요약 & 타임스탬프 네비게이터")
st.caption("Whisper AI 자막 추출 + GPT-4 분석기")

# API 키가 환경 변수에 없을 경우를 대비한 사이드바 입력창
with st.sidebar:
    st.header("🔑 API Key 설정")
    if not OPENAI_API_KEY:
        OPENAI_API_KEY = st.text_input("OpenAI API Key", type="password")
    if not YOUTUBE_API_KEY:
        YOUTUBE_API_KEY = st.text_input("YouTube API Key", type="password")

query = st.text_input("🔍 검색할 유튜브 키워드를 입력하세요 (예: 연남동 데이트 코스)", "")

if st.button("분석 실행") and query:
    if not YOUTUBE_API_KEY or not OPENAI_API_KEY:
        st.error("오른쪽 사이드바(또는 환경변수)에 API 키를 모두 입력해주세요.")
    else:
        with st.spinner("🔎 유튜브에서 가장 알맞은 영상을 찾는 중..."):
            youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
            res = youtube.search().list(q=query, part="snippet", maxResults=1, type="video").execute()
            
            if not res.get("items"):
                st.error("검색 결과가 없습니다.")
            else:
                item = res["items"][0]
                vid = item["id"]["videoId"]
                title = item["snippet"]["title"]

                st.info(f"🎥 분석 대상 영상: {title}")
                
                # 자막 처리
                with st.spinner("🎧 Whisper AI가 영상 오디오를 분석하여 자막을 추출하고 있습니다..."):
                    try:
                        text = extract_transcript(vid)
                    except Exception as e:
                        st.error(f"자막 추출 중 오류 발생: {e}")
                        text = None
                
                # 요약 및 결과 출력
                if text:
                    with st.spinner("🤖 GPT가 핵심 정보를 정리하고 타임스탬프 버튼을 매핑하는 중..."):
                        prompt = make_prompt(text, vid)
                        summary = gpt_summarize(prompt)
                    
                    # 유튜브 플레이어 iframe API와 요약 결과를 한 화면(컴포넌트)에 빌드
                    player_html = f"""
                    <div style="display: flex; flex-direction: column; align-items: center;">
                        <div id="player"></div>
                    </div>
                    <script>
                      var tag = document.createElement('script');
                      tag.src = "https://www.youtube.com/iframe_api";
                      var firstScriptTag = document.getElementsByTagName('script')[0];
                      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

                      var player;
                      function onYouTubeIframeAPIReady() {{
                        player = new YT.Player('player', {{
                          height: '360',
                          width: '640',
                          videoId: '{vid}'
                        }});
                      }}
                      
                      function seekToTime(seconds) {{
                        if (player) {{
                          player.seekTo(seconds, true);
                          player.playVideo();
                        }}
                      }}
                    </script>
                    <div style="margin-top:25px; font-family: sans-serif; padding: 10px; border-top: 1px solid #ddd;">
                        {summary}
                    </div>
                    """
                    
                    st.markdown("### 📊 분석 결과 리포트")
                    components.html(player_html, height=1000, scrolling=True)
