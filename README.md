# YouTube 영상 요약 및 타임스탬프 네비게이터

Whisper AI 자막 추출 기술과 GPT-4 모델을 결합하여 유튜브 영상의 핵심 내용을 제품 및 장소별로 요약하고, 클릭 시 해당 시점으로 이동할 수 있는 인터랙티브 Streamlit 웹 애플리케이션입니다.

---

## 주요 기능
- **유튜브 동영상 검색**: 키워드 입력 시 YouTube Data API를 통해 가장 연관성 높은 영상을 자동으로 매칭합니다.
- **Whisper AI 자막 추출**: 영상의 오디오를 다운로드한 후 OpenAI Whisper 모델을 통해 정밀한 타임스탬프 포함 자막을 생성합니다.
- **GPT-4 기반 스마트 요약**: 자막을 분석하여 영상 속 제품이나 장소의 특징, 추천 대상, 주의사항을 일목요연하게 정리합니다.
- **인터랙티브 타임스탬프**: 요약 리포트 내의 시간 버튼을 클릭하면, 상단의 유튜브 플레이어가 해당 초(second)로 즉시 점프하여 재생됩니다.

---

## 기술 스택
- **Frontend / Web App**: Streamlit
- **AI / ML**: OpenAI Whisper (Base Model), OpenAI GPT-4-turbo
- **Data Fetching**: YouTube Data API v3, yt-dlp
- **Media Processing**: FFmpeg
- **Tunneling**: pyngrok

---

## 시작하기 (로컬 환경 실행)

### 1. 사전 필수 설치
오디오 추출을 위해 시스템에 FFmpeg가 설치되어 있어야 합니다.
- **Mac**: `brew install ffmpeg`
- **Windows**: FFmpeg 공식 홈페이지에서 다운로드 후 환경변수 등록 필수

### 2. 저장소 복제 및 라이브러리 설치
```bash
git clone [https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_GITHUB_USERNAME/YOUR_REPOSITORY_NAME.git)
cd YOUR_REPOSITORY_NAME
pip install -r requirements.txt
