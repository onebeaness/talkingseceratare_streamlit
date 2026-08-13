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

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# 대화 기록 화면에 출력
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 입력 영역 ---
col1, col2 = st.columns([4, 1])

with col1:
    user_input = st.chat_input("메시지를 입력하거나 마이크로 말씀하세요...")

with col2:
    st.write("음성 입력")
    audio_data = mic_recorder(
        start_prompt="녹음 시작",
        stop_prompt="녹음 완료",
        key='mic'
    )

recognized_text = None

# 1. 마이크 음성 녹음 처리 (음성 -> 텍스트 인식)
if audio_data and audio_data.get('bytes'):
    current_audio_id = audio_data.get('id')
    
    if current_audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = current_audio_id
        
        audio_format = audio_data.get('format', 'webm')
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as audio_file:
            audio_file.write(audio_data['bytes'])
            audio_path = audio_file.name

        with st.spinner("음성을 인식하는 중..."):
            try:
                with open(audio_path, "rb") as f:
                    audio_bytes_data = f.read()

                mime_type = f"audio/{audio_format}" if audio_format in ['wav', 'mp3'] else "audio/webm"

                # 사용자가 말한 음성을 텍스트로 변환(인식) 요청
                stt_response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[
                        "사용자가 음성으로 말한 내용을 다른 설명 없이 한국어 텍스트로만 그대로 옮겨 적어주세요.",
                        genai.types.Part.from_bytes(data=audio_bytes_data, mime_type=mime_type)
                    ]
                )
                
                if stt_response and stt_response.text:
                    recognized_text = stt_response.text.strip()
                
                os.remove(audio_path)
            except Exception as e:
                st.error(f"음성 인식 오류: {e}")

# 2. 텍스트로 직접 입력한 경우
elif user_input:
    recognized_text = user_input

# --- 3. 인식된 텍스트 출력 및 답변 생성 처리 ---
if recognized_text:
    # 1) 내가 말한 내용을 '사용자 메시지'로 먼저 기록 및 출력 (인식 결과 확인용)
    st.session_state.chat_history.append({"role": "user", "content": recognized_text})
    with st.chat_message("user"):
        st.markdown(recognized_text)

    # 2) 인식된 내용을 바탕으로 제미나이의 답변 생성 및 출력
    with st.chat_message("assistant"):
        with st.spinner("생각 중입니다..."):
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=recognized_text
            )
            answer = response.text
            st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

            # 3) TTS 음성 합성 및 재생
            tts = gTTS(text=answer, lang='ko')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts.save(fp.name)
                st.audio(fp.name, format='audio/mp3', autoplay=True)
