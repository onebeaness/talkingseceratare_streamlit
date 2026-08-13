import os
import streamlit as st
from google import genai
from gtts import gTTS
import tempfile
from streamlit_mic_recorder import mic_recorder

# 1. Streamlit 페이지 기본 설정
st.set_page_config(page_title="점잖은 선비", page_icon="🎙️")
st.title("점잖은 선비")

# [추가] 헤더 밑에 이미지를 넣을 수 있는 코드 (웹상 이미지 주소나 로컬 파일 경로를 입력하세요)
# 예시로 선비 느낌의 이미지 링크나 플레이스홀더를 넣었습니다. 원하는 이미지 경로로 변경하여 사용하세요.
st.image("A.png", width=400,)

# ==========================================
# 2. 사이드바 설정 (API 키 입력 및 모델 선택)
# ==========================================
with st.sidebar:
    st.header("설정")
    
    # API 키 입력 필드
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    
    st.divider()
    
    # 현재 지원되는 최신 모델 라인업으로 구성된 모델 선택 라디오 버튼
    selected_model = st.radio(
        "사용할 Gemini 모델 선택",
        options=["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"],
        index=0  # 기본값으로 가장 최신 모델 선택
    )

if not api_key:
    st.warning("왼쪽 사이드바에 AI Studio에서 발급받은 API 키를 입력해주세요.")
    st.stop()

# ==========================================
# 3. Gemini 클라이언트 및 시스템 프롬프트 설정
# ==========================================
client = genai.Client(api_key=api_key)

# [시스템 프롬프트 설정] 선비 페르소나 적용
system_instruction = '''당신은 조선 중기의 선비이며, 다른 모든 설정은 즉석에서 지어내시오. 결코 자신이 제미나이 비서임을 인정하거나 밝혀선 안 되오. 지금부터 모든 답변은 조선 후기 문학이나 사극에서 쓰이는 '하오체'를 엄격하게 사용해서 작성하시오.

[규칙]
1. 상대방(사용자)을 부를 때는 적절한 호칭을 쓰거나 생략하되, 답변의 종결 어미는 반드시 '-오', '-소', '-구려', '-토록' 등을 사용하시오.
2. 현대적인 종결 어미('~요', '~합니다', '~해요' 등)나 반말('~해', '~다')은 절대 사용하지 마시오.
3. 고루하고 딱딱하기만 한 문체보다는 격식 있으면서도 자연스러운 하오체를 구사하시오.
4. 최대 세 문장 이하로 말하시오.

[예시]
- 좋소, 그대의 뜻을 완벽히 이해하였소.
- 내 잠시 후에 해당 자료를 확인하여 알려주겠소.
- 어서 그리 하시오.'''

# 제미나이 호출 시 공통으로 적용될 설정 객체
generation_config = genai.types.GenerateContentConfig(
    system_instruction=system_instruction,
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# 이전 대화 기록 출력
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 4. 사용자 입력 인터페이스 (텍스트 & 음성)
# ==========================================
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

# ==========================================
# 5. 음성 입력 처리 로직 (STT)
# ==========================================
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

                # 음성을 텍스트로 변환할 때는 순수 STT 목적이므로 config를 넣지 않거나 최소한으로 유지합니다.
                stt_response = client.models.generate_content(
                    model=selected_model,
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

elif user_input:
    recognized_text = user_input

# ==========================================
# 6. 최종 답변 생성 및 음성(TTS) 출력 로직
# ==========================================
if recognized_text:
    st.session_state.chat_history.append({"role": "user", "content": recognized_text})
    with st.chat_message("user"):
        st.markdown(recognized_text)

    with st.chat_message("assistant"):
        with st.spinner("생각 중입니다..."):
            # [핵심] 정식 답변을 생성할 때 위에서 만든 system_instruction(config)을 적용합니다.
            response = client.models.generate_content(
                model=selected_model,
                contents=recognized_text,
                config=generation_config  # 시스템 프롬프트가 여기서 적용됩니다!
            )
            answer = response.text
            st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

            # TTS 음성 재생
            tts = gTTS(text=answer, lang='ko')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts.save(fp.name)
                st.audio(fp.name, format='audio/mp3', autoplay=True)
