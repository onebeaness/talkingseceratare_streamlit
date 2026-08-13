import os
import streamlit as st
from google import genai
from gtts import gTTS
import tempfile
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="Gemini 음성 비서", page_icon="🎙️")
st.title("🎙️ Gemini 실시간 음성 비서")

# 사이드바에서 API 키 입력 받기
api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if not api_key:
    st.warning("왼쪽 사이드바에 AI Studio에서 발급받은 API 키를 입력해주세요.")
    st.stop()

# 클라이언트 초기화
client = genai.Client(api_key=api_key)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 대화 기록 화면에 출력
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 음성 입력 및 텍스트 입력 영역 ---
col1, col2 = st.columns([4, 1])

with col1:
    user_input = st.chat_input("메시지를 입력하거나 아래 마이크로 말씀하세요...")

with col2:
    st.write("음성 입력")
    # 마이크 녹음 버튼 생성
    audio_data = mic_recorder(
        start_prompt="녹음 시작",
        stop_prompt="녹음 완료",
        key='mic'
    )

processed_text = None

# 1. 마이크로 음성 녹음이 들어온 경우 처리
if audio_data:
    # 녹음된 바이트(bytes) 데이터를 임시 파일로 저장
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as audio_file:
        audio_file.write(audio_data['bytes'])
        audio_path = audio_file.name

    with st.spinner("음성을 이해하는 중..."):
        try:
            # 파일을 업로드하거나 바이트로 전달하여 제미나이에 전달
            with open(audio_path, "rb") as f:
                audio_bytes_data = f.read()

            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[
                    "사용자의 음성 입력입니다. 질문에 한국어로 친절하게 답변해주세요.",
                    genai.types.Part.from_bytes(data=audio_bytes_data, mime_type="audio/wav")
                ]
            )
            processed_text = response.text
            os.remove(audio_path)
        except Exception as e:
            st.error(f"음성 처리 오류: {e}")

# 2. 텍스트로 직접 입력한 경우 처리
elif user_input:
    processed_text = user_input

# --- 공통 답변 생성 및 음성 출력 로직 ---
if processed_text:
    # 사용자 메시지 기록 및 출력
    st.session_state.chat_history.append({"role": "user", "content": processed_text})
    with st.chat_message("user"):
        st.markdown(processed_text)

    # 제미나이 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("생각 중입니다..."):
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=processed_text
            )
            answer = response.text
            st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

            # TTS 음성 합성 및 웹 재생
            tts = gTTS(text=answer, lang='ko')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts.save(fp.name)
                st.audio(fp.name, format='audio/mp3', autoplay=True)
