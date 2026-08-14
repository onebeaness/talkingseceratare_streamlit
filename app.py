import os
import streamlit as st
from google import genai
from gtts import gTTS
import tempfile
from streamlit_mic_recorder import mic_recorder

# 1. Streamlit 페이지 기본 설정 (웹 브라우저 탭의 제목과 아이콘, 메인 타이틀 지정)
st.set_page_config(page_title="점잖은 선비", page_icon="🎙️")
st.title("점잖은 선비")

# 헤더 영역에 선비 컨셉의 이미지를 표시 (경로 또는 URL 지정 가능)
st.image("A.png", width=400,)

# ==========================================
# 2. 사이드바 설정 (API 키 입력 및 모델 선택)
# ==========================================
with st.sidebar:
    st.header("설정")
    
    # 사용자의 Gemini API Key를 안전하게 입력받는 보안 입력 필드
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    
    st.divider()
    
    # 사용할 Gemini 모델 라인업 선택 (기본값으로 최신 플래시 모델 지정)
    selected_model = st.radio(
        "사용할 Gemini 모델 선택",
        options=["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.1-flash-lite"],
        index=0  # 기본값: 가장 최신 모델
    )

# API 키가 입력되지 않은 경우 경고를 띄우고 앱 실행 중단
if not api_key:
    st.warning("왼쪽 사이드바에 AI Studio에서 발급받은 API 키를 입력해주세요.")
    st.stop()

# ==========================================
# 3. Gemini 클라이언트 및 시스템 프롬프트 설정
# ==========================================
# 입력받은 API 키를 바탕으로 Gemini 공식 클라이언트 초기화
client = genai.Client(api_key=api_key)

# 조선시대 선비 페르소나를 부여하기 위한 시스템 프롬프트 정의
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

# Gemini API 호출 시 시스템 지시사항을 포함할 설정 객체 생성
generation_config = genai.types.GenerateContentConfig(
    system_instruction=system_instruction,
)

# 세션 상태에 대화 기록이 없으면 빈 리스트로 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 중복 음성 인식을 방지하기 위한 마지막 오디오 ID 상태 초기화
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# 웹 새로고침 시에도 기존 대화 내역이 화면에 유지되도록 순차적으로 출력
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 4. 사용자 입력 인터페이스 (텍스트 & 음성)
# ==========================================
# 화면을 4:1 비율의 두 컬럼으로 나누어 텍스트 입력과 마이크 녹음 버튼 배치
col1, col2 = st.columns([4, 1])

with col1:
    # 텍스트 채팅 입력창
    user_input = st.chat_input("메시지를 입력하거나 마이크로 말씀하세요...")

with col2:
    st.write("음성 입력")
    # 마이크 녹음 컴포넌트 호출
    audio_data = mic_recorder(
        start_prompt="녹음 시작",
        stop_prompt="녹음 완료",
        key='mic'
    )

# 사용자가 입력한 텍스트 또는 음성 인식 결과가 담길 변수
recognized_text = None

# ==========================================
# 5. 음성 입력 처리 로직 (STT: Speech-to-Text)
# ==========================================
if audio_data and audio_data.get('bytes'):
    current_audio_id = audio_data.get('id')
    
    # 새로운 오디오 입력인 경우에만 처리 (중복 실행 방지)
    if current_audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = current_audio_id
        
        audio_format = audio_data.get('format', 'webm')
        # 녹음된 바이트 데이터를 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as audio_file:
            audio_file.write(audio_data['bytes'])
            audio_path = audio_file.name

        with st.spinner("음성을 인식하는 중..."):
            try:
                with open(audio_path, "rb") as f:
                    audio_bytes_data = f.read()

                mime_type = f"audio/{audio_format}" if audio_format in ['wav', 'mp3'] else "audio/webm"

                # 순수 STT(음성->텍스트 변환) 목적이므로 시스템 프롬프트를 배제하고 텍스트 변환만 요청
                stt_response = client.models.generate_content(
                    model=selected_model,
                    contents=[
                        "사용자가 음성으로 말한 내용을 다른 설명 없이 한국어 텍스트로만 그대로 옮겨 적어주세요.",
                        genai.types.Part.from_bytes(data=audio_bytes_data, mime_type=mime_type)
                    ]
                )
                
                if stt_response and stt_response.text:
                    recognized_text = stt_response.text.strip()
                
                # 사용이 끝난 임시 오디오 파일 삭제
                os.remove(audio_path)
            except Exception as e:
                st.error(f"음성 인식 오류: {e}")

elif user_input:
    # 텍스트 입력인 경우 그대로 사용
    recognized_text = user_input

# ==========================================
# 6. 최종 답변 생성 및 음성(TTS) 출력 로직
# ==========================================
if recognized_text:
    # 사용자 메시지를 대화 기록에 추가하고 화면에 출력
    st.session_state.chat_history.append({"role": "user", "content": recognized_text})
    with st.chat_message("user"):
        st.markdown(recognized_text)

    # 어시스턴트(선비 페르소나) 응답 생성 과정
    with st.chat_message("assistant"):
        with st.spinner("생각 중입니다..."):
            # [핵심] 조선 선비 페르소나가 담긴 system_instruction(config)을 적용하여 답변 생성 요청
            response = client.models.generate_content(
                model=selected_model,
                contents=recognized_text,
                config=generation_config  # 시스템 프롬프트 적용
            )
            answer = response.text
            st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

            # 생성된 텍스트 답변을 gTTS를 이용해 음성 파일(MP3)로 변환
            tts = gTTS(text=answer, lang='ko')
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts.save(fp.name)
                # 변환된 음성 파일을 웹 화면에서 자동 재생
                st.audio(fp.name, format='audio/mp3', autoplay=True)
