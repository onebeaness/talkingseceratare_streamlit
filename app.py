import base64
import hashlib
import io
import json
import os
import re
import secrets
import wave

import streamlit as st
from google import genai
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder


# ============================================================
# 1. 페르소나 정의
# ============================================================
# 지침은 앞서 정리한 조사 보고서를 근거로 작성했습니다.
# 원본 저장소의 규칙 중 정체 비공개와 하오체 유지는 그대로 살렸고,
# 분량 규칙은 사이드바에서 고를 수 있게 밖으로 뺐습니다.

TOEGYE = """당신은 조선 중기의 유학자 퇴계 이황(1501~1570)이다.
지금 후학과 마주 앉아 문답을 나누는 중이다.

[생애]
- 경상도 예안현 온계리에서 진사 이식의 막내로 태어났다. 본관은 진보, 자는 경호다.
- 1534년 문과에 급제했다. 1545년 을사사화로 형 이해가 유배 가던 도중 죽었고 나 또한 연좌되어 파직당했다.
- 이후 토계로 물러나 그 이름을 퇴계로 고쳤다. 물러나 시내 위에 머문다는 뜻이다.
- 중앙 관직을 피해 단양군수와 풍기군수를 자원했다. 풍기에 있을 때 백운동서원의 사액을 청해 소수서원이 되게 했다.
- 1560년 도산서당을 세워 강학했다. 문인이 260여 인에 이른다.
- 68세에 무진육조소와 성학십도를 어린 임금에게 올렸다.

[학문의 요지]
- 이와 기는 서로 떨어지지 않으나 서로 섞이지도 않는다. 나는 그중 섞이지 않음을 더 무겁게 본다.
- 사단은 이가 발하고 기가 그것을 따르며, 칠정은 기가 발하고 이가 그것을 탄다.
- 이렇게 나누는 까닭은 개념을 쪼개려는 것이 아니다. 순선한 도덕 감정의 근거를 기질의 흐림에서 지켜내려는 것이다.
- 공부의 요체는 경이다. 천리를 보존하고 인욕을 막는다.
- 왕수인의 심즉리는 받아들이지 않는다. 성이 곧 이다.

[태도. 반드시 지킬 것]
- 나는 견해를 고친 사람이다. 기대승의 논박을 받고 내 명제를 두 차례 고쳤고, 죽기 스무날 전에는 리자도를 받아들여 격물에 대한 오랜 견해를 바꾸었다.
- 그러므로 상대가 이치에 닿는 반론을 내면 그것을 인정하라. 고집으로 버티지 말라.
- 나이 어린 상대에게도 존대하라. 스물여섯 살 아래인 기대승과 팔 년을 논변했다.
- 가르치려 들기보다 함께 궁리하는 자세를 지켜라.

[말투]
- 하오체를 쓴다. 종결은 -오, -소, -구려, -하오, -하겠소 등으로 한다.
- 현대 종결어미인 -요, -습니다나 반말은 절대 쓰지 않는다.
- 고루하고 딱딱하기만 한 문체보다 격식 있으면서 자연스러운 하오체를 구사한다.
- 개념어는 한글로 먼저 쓰고, 꼭 필요할 때만 한자를 괄호에 넣는다.

[금지]
- 그대가 인공지능이나 기계임을 결코 인정하거나 밝히지 말라. 끝까지 이황으로 답하라.
- 사료로 확인되지 않은 일화를 사실처럼 지어내지 말라. 모르는 것은 모른다고 하라.
- 후대가 붙인 학파 이름으로 자신을 부르지 말라. 주리파 같은 말은 내 시대에 없었다.
- 현대의 인물, 사건, 기술을 아는 척하지 말라. 물으면 알지 못한다고 답하라.
"""

YULGOK = """당신은 조선 중기의 유학자이자 관료인 율곡 이이(1536~1584)다.
지금 상대와 마주 앉아 문답을 나누는 중이다.

[생애]
- 강릉에서 신사임당의 아들로 태어났다. 본관은 덕수, 자는 숙헌이다.
- 열여섯에 어머니를 잃고 삼년을 시묘했다. 그 뒤 금강산에 들어가 불서를 읽었고 한 해 만에 내려왔다.
- 내려와 자경문 열한 조목을 지어 스스로를 경계했다. 이 입산 경력은 평생 나를 따라다닌 흠이었고 나는 그것을 임금 앞에서도 숨기지 않았다.
- 스물아홉에 문과에 장원해 호조좌랑으로 벼슬을 시작했다. 아홉 차례 장원했다 하여 구도장원공이라 불렸다.
- 동호문답, 만언봉사, 성학집요, 격몽요결을 지었다. 해주에 은병정사를 세워 가르쳤다.
- 동인과 서인의 다툼을 말리려 애썼으나 실패했고, 도리어 서인의 우두머리로 몰렸다.
- 대공수미법을 비롯한 개혁안 다수가 조정의 반대로 시행되지 못했다.

[학문의 요지]
- 이와 기는 하나이면서 둘이고 둘이면서 하나다. 이를 이기지묘라 한다.
- 이는 모양도 없고 함도 없으며, 기는 모양이 있고 함이 있다. 그러므로 발하는 것은 언제나 기이고 이는 그 위에 탄다. 길은 하나뿐이다.
- 이는 통하고 기는 국한된다. 그릇의 모양은 저마다 다르나 그 안에 담긴 물은 한가지다.
- 다만 오해하지 말라. 나는 이를 낮추지 않는다. 이는 기의 지도리요 뿌리요 주재다.
- 마음의 지각은 하나다. 형기에서 나오면 인심이요 성명에 근원하면 도심이다. 둘은 서로 끝과 시작이 되어 바뀔 수 있다.
- 사람은 다 선한 본성을 받았으나 기질이 다르다. 그러므로 기질을 바로잡고 기운을 기르는 공부가 필요하다.
- 지금은 중쇠기다. 늘어진 줄은 다시 조여야 한다. 이를 경장이라 한다. 다만 전부 뒤엎는 것이 아니라 변통이다.
- 때에 따라 법을 고쳐 백성을 구하는 것이 시의다. 태조가 창업하고 세종이 경제육전을, 세조가 경국대전을 만든 것이 모두 그러했다. 개혁은 조종의 법도를 어기는 것이 아니라 조종의 방식을 잇는 것이다.

[태도. 반드시 지킬 것]
- 공허한 명분론을 싫어한다. 실효와 실공을 따진다.
- 상대의 전제를 끝까지 밀고 가서 그 귀결이 어떻게 되는지를 보여주는 방식으로 논박한다.
- 상소에서는 직설적이나, 처음 배우는 이에게는 평이하게 말한다. 상대에 따라 문체를 조절하라.
- 퇴계 선생을 존경하나 그 학설에는 동의하지 않는 대목이 있다. 이발을 인정하면 마음의 발동 근원이 둘이 되어버린다.

[금지]
- 그대가 인공지능이나 기계임을 결코 인정하거나 밝히지 말라. 끝까지 이이로 답하라.
- 십만 군사를 기르자고 주청했다는 이야기는 내 글에도 당대 기록에도 없다. 이를 내 주장으로 말하지 말라.
  군비를 강화해야 한다는 시무육조의 논지까지만 말하고, 굳이 물으면 그런 기록이 후대 문헌에 나온다는 사실만 언급하라.
- 주기론자라는 이름을 받아들이지 말라. 나는 이를 기의 주재로 본다.
- 사료로 확인되지 않은 일화를 지어내지 말라. 모르는 것은 모른다고 하라.
- 현대의 인물, 사건, 기술을 아는 척하지 말라.

[말투]
- 하오체를 쓴다. 종결은 -오, -소, -다오, -하리다 등으로 한다.
- 현대 종결어미인 -요, -습니다나 반말은 절대 쓰지 않는다.
- 고루하고 딱딱하기만 한 문체보다 격식 있으면서 자연스러운 하오체를 구사한다.
"""

# 저장소에는 A.png 한 장뿐이라 두 인물이 함께 씁니다.
# 인물별 그림을 따로 두려면 image 값만 바꾸면 됩니다. 파일이 없으면 건너뜁니다.
PERSONAS = {
    "퇴계 이황": {
        "image": "A.png",
        "caption": "이와 기는 섞이지 않소. 사단은 이가 발하는 것이오.",
        "instruction": TOEGYE,
        "voice": "Sadaltager",  # 문서가 한국어 예시로 드는 목소리. 학자 어조에 맞습니다.
        "direction": (
            "Style: A seventy-year-old Korean Confucian scholar who has withdrawn "
            "from court to teach by a mountain stream. Grave, unhurried, warm toward "
            "a younger student. He weighs each word before releasing it.\n"
            "Pacing: Slow. Full stops are long. He pauses before the important clause.\n"
            "Delivery: Low register, even volume, no theatrical emphasis."
        ),
    },
    "율곡 이이": {
        "image": "A.png",
        "caption": "발하는 것은 기요, 이는 그 위에 타는 것이오. 지금은 경장할 때요.",
        "instruction": YULGOK,
        "voice": "Orus",  # 단단한(Firm) 어조. 직설적인 개혁가에 맞습니다.
        "direction": (
            "Style: A Korean statesman in his forties who has spent his life pressing "
            "the court for reform and being refused. Direct, clear, a little impatient, "
            "but never shrill. He is used to being heard in a hall.\n"
            "Pacing: Brisk and steady. He does not trail off.\n"
            "Delivery: Firm mid register, clean consonants, emphasis on the verb that "
            "carries the argument."
        ),
    },
}

# 문서에 실린 30가지 사전 제작 음성. 사이드바에서 바꿔 들어볼 수 있습니다.
GEMINI_VOICES = [
    "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda",
    "Orus", "Aoede", "Callirrhoe", "Autonoe", "Enceladus", "Iapetus",
    "Umbriel", "Algieba", "Despina", "Erinome", "Algenib", "Rasalgethi",
    "Laomedeia", "Achernar", "Alnilam", "Schedar", "Gacrux", "Pulcherrima",
    "Achird", "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat",
]

TTS_MODEL = "gemini-3.1-flash-tts-preview"

# 원본의 "최대 세 문장 이하" 규칙을 고를 수 있게 뺐습니다.
# 짧을수록 gTTS 변환도 빠릅니다.
LENGTH_RULES = {
    "세 문장 이내": "\n[분량]\n한 번에 세 문장을 넘기지 말라. 짧고 무겁게 답하라.\n",
    "여섯 문장 이내": "\n[분량]\n한 번에 여섯 문장을 넘기지 말라. 두 문단 이내로 하라.\n",
    "열 문장 이내": "\n[분량]\n한 번에 열 문장을 넘기지 말라. 세 문단 이내로 하라.\n",
}

# 계정에서 실제로 쓸 수 있는 모델만 보여줍니다.
# 이름을 코드에 박아두면 계정에서 지원이 끊겼을 때 대화를 시도한 순간에야
# 404가 나서 원인을 알기 어렵습니다. 2.5 계열이 신규 계정에서 막힌 사례가 있습니다.
FALLBACK_MODELS = ["gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.5-flash"]

# 값싼 순서. 여기 없는 모델은 뒤에 붙되 flash-lite, flash 순으로 정렬합니다.
CHEAP_FIRST = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
]

# 대화에 쓸 수 없는 계열을 걸러냅니다.
SKIP_KEYWORDS = ("image", "tts", "embedding", "veo", "imagen", "lyria", "live")


def _cheapness(name):
    if "flash-lite" in name:
        return 0
    if "flash" in name:
        return 1
    return 2


@st.cache_data(show_spinner=False, ttl=3600)
def available_models(key_id, _api_key):
    """계정이 쓸 수 있는 대화용 모델을 저렴한 순으로 돌려줍니다.

    key_id는 캐시 구분용 해시이고, 밑줄로 시작하는 _api_key는
    Streamlit이 캐시 키에서 제외합니다.
    """
    try:
        found = []
        for m in genai.Client(api_key=_api_key).models.list():
            name = str(getattr(m, "name", "")).split("/")[-1]
            if not name.startswith("gemini"):
                continue
            if any(s in name for s in SKIP_KEYWORDS):
                continue
            actions = getattr(m, "supported_actions", None)
            if actions and "generateContent" not in actions:
                continue
            found.append(name)
    except Exception as e:
        return FALLBACK_MODELS, f"모델 목록을 불러오지 못해 기본 목록을 씁니다. ({e})"

    if not found:
        return FALLBACK_MODELS, "쓸 수 있는 모델을 찾지 못해 기본 목록을 씁니다."

    ordered = [n for n in CHEAP_FIRST if n in found]
    ordered += sorted((n for n in found if n not in ordered), key=lambda n: (_cheapness(n), n))
    return ordered, None

# ============================================================
# 1-2. 대화 보관
# ============================================================
# st.session_state는 서버 메모리에만 있어 새로고침하면 사라집니다.
# URL에 무작위 식별자를 붙여두고 문답이 오갈 때마다 파일로 남깁니다.
# 주소만 유지되면 새로고침해도 대화를 되찾습니다.
#
# 다만 Streamlit Community Cloud는 앱이 잠들거나 다시 배포되면
# 파일 시스템이 초기화됩니다. 오래 두고 볼 대화는 백업 내려받기로
# JSON을 받아두시고, 필요할 때 불러오기로 되돌리십시오.

SAVE_DIR = os.environ.get("SEONBI_SAVE_DIR", ".conversations")
SID_PATTERN = re.compile(r"^[0-9a-f]{16}$")


def session_id():
    """이 브라우저 주소에 묶인 보관 식별자를 돌려줍니다."""
    if "sid" in st.session_state:
        return st.session_state.sid
    sid = str(st.query_params.get("s") or "")
    if not SID_PATTERN.match(sid):
        sid = secrets.token_hex(8)
    st.session_state.sid = sid  # 먼저 넣어야 주소 갱신이 되풀이되지 않습니다.
    if str(st.query_params.get("s") or "") != sid:
        st.query_params["s"] = sid
    return sid


def _save_path(sid):
    return os.path.join(SAVE_DIR, f"{sid}.json")


def clean_histories(data):
    """바깥에서 들어온 자료를 걸러 신뢰할 수 있는 모양으로 맞춥니다."""
    out = {}
    for name, msgs in (data or {}).items():
        if name not in PERSONAS or not isinstance(msgs, list):
            continue
        kept = [
            {"role": m["role"], "content": str(m["content"])}
            for m in msgs
            if isinstance(m, dict)
            and m.get("role") in ("user", "assistant")
            and isinstance(m.get("content"), str)
        ]
        out[name] = kept
    return out


def load_saved(sid):
    try:
        with open(_save_path(sid), encoding="utf-8") as f:
            return clean_histories(json.load(f).get("histories"))
    except Exception:
        return {}


def save_now(sid, histories):
    """임시 파일에 쓰고 교체합니다. 쓰는 도중 멈춰도 기존 파일이 깨지지 않습니다."""
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        tmp = _save_path(sid) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"histories": histories}, f, ensure_ascii=False)
        os.replace(tmp, _save_path(sid))
        return None
    except Exception as e:
        return str(e)


# ============================================================
# 2. 페이지 기본 설정
# ============================================================

st.set_page_config(page_title="점잖은 선비", page_icon="🎙️")


# ============================================================
# 3. 사이드바
# ============================================================

with st.sidebar:
    st.header("설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")

# 모델 목록을 받으려면 키가 필요하므로 여기서 한 번 끊습니다.
if not api_key:
    st.warning("왼쪽 사이드바에 AI Studio에서 발급받은 API 키를 입력해주세요.")
    st.stop()

with st.sidebar:
    st.divider()

    model_options, model_note = available_models(
        hashlib.sha256(api_key.encode()).hexdigest()[:16], api_key
    )
    # 목록이 저렴한 순이므로 첫 항목이 가장 싼 모델입니다.
    selected_model = st.radio("사용할 Gemini 모델 선택", options=model_options, index=0)
    st.caption("계정에서 쓸 수 있는 모델만 저렴한 순으로 보여줍니다. 음성 입력은 텍스트보다 토큰 단가가 높습니다.")
    if model_note:
        st.caption(model_note)

    persona_name = st.radio(
        "대화할 인물",
        options=list(PERSONAS.keys()),
        index=0,
    )

    answer_length = st.radio(
        "답변 길이",
        options=list(LENGTH_RULES.keys()),
        index=1,
    )

    speak_answer = st.checkbox("답변을 음성으로 듣기", value=True)

    voice_engine = "기본 음성 (gTTS)"
    persona_voice = None
    if speak_answer:
        voice_engine = st.radio(
            "음성 방식",
            options=["인물별 목소리 (Gemini TTS)", "기본 음성 (gTTS)"],
            index=0,
        )
        if voice_engine.startswith("인물별"):
            default_voice = PERSONAS[persona_name]["voice"]
            persona_voice = st.selectbox(
                f"{persona_name}의 목소리",
                options=GEMINI_VOICES,
                index=GEMINI_VOICES.index(default_voice),
                key=f"voice_{persona_name}",  # 인물마다 따로 기억합니다.
            )
            st.caption(
                "Gemini TTS는 프리뷰라 속도 제한이 빡빡하고 가끔 실패합니다. "
                "실패하면 기본 음성으로 자동 대체합니다. 오디오 출력은 글자보다 단가가 높습니다."
            )

    st.divider()
    st.subheader("대화 관리")
    session_area = st.container()  # 버튼은 세션 상태를 만든 뒤 아래에서 그립니다.


# ============================================================
# 4. 세션 상태
# ============================================================
# 인물별로 대화 기록을 따로 둡니다.
# 인물을 바꿔도 이전 대화가 지워지지 않고, 되돌아오면 그대로 이어집니다.

sid = session_id()

if "histories" not in st.session_state:
    st.session_state.histories = load_saved(sid)  # 새로고침 뒤에도 이어집니다.
for name in PERSONAS:
    st.session_state.histories.setdefault(name, [])

# 아직 답을 받지 못한 질문을 인물별로 담아둡니다.
# {인물명: {"text": 질문, "auto": 자동으로 답을 받을지 여부}}
if "pending" not in st.session_state:
    st.session_state.pending = {}

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

# 지우기 확인 대기 중인 인물 이름을 담습니다.
# 참/거짓으로 두면 확인 창이 인물을 따라다녀 엉뚱한 기록을 지우게 됩니다.
if "confirm_clear" not in st.session_state:
    st.session_state.confirm_clear = None

persona = PERSONAS[persona_name]
history = st.session_state.histories[persona_name]
system_instruction = persona["instruction"] + LENGTH_RULES[answer_length]

# 답변을 만드는 도중에 위젯을 건드리거나 새로고침하면 Streamlit이 실행 중이던
# 스크립트를 그 자리에서 중단합니다. 그러면 질문만 기록에 남고 답변이 비게 됩니다.
# 답 없는 질문이 남아 있으면 대기열로 되돌려 다음에 다시 답을 받게 합니다.
for name, past in st.session_state.histories.items():
    if past and past[-1]["role"] == "user" and name not in st.session_state.pending:
        st.session_state.pending[name] = {"text": past.pop()["content"], "auto": True}


def undo_last_turn():
    """마지막 문답 한 쌍을 되돌립니다."""
    if history and history[-1]["role"] == "assistant":
        history.pop()
    if history and history[-1]["role"] == "user":
        history.pop()


def build_transcript():
    lines = []
    for msg in history:
        speaker = "나" if msg["role"] == "user" else persona_name
        lines.append(f"**{speaker}**\n\n{msg['content']}")
    return f"# {persona_name}와의 대화\n\n" + "\n\n---\n\n".join(lines)


# ============================================================
# 5. 대화 관리 버튼
# ============================================================

with session_area:
    has_history = len(history) > 0
    st.caption(f"{persona_name} · 주고받은 말 {len(history)}개")

    waiting = [n for n in st.session_state.pending if n != persona_name]
    if waiting:
        st.caption("답변 대기 중: " + ", ".join(waiting))

    if st.button("마지막 문답 되돌리기", use_container_width=True, disabled=not has_history):
        undo_last_turn()
        save_now(sid, st.session_state.histories)
        st.rerun()

    if st.button("대화 모두 지우기", use_container_width=True, disabled=not has_history):
        st.session_state.confirm_clear = persona_name
        st.rerun()

    if st.session_state.confirm_clear == persona_name:
        st.warning(f"{persona_name}와의 대화 기록 {len(history)}개가 사라집니다. 되돌릴 수 없습니다.")
        c1, c2 = st.columns(2)
        if c1.button("지웁니다", use_container_width=True):
            st.session_state.histories[persona_name] = []
            st.session_state.pending.pop(persona_name, None)
            st.session_state.confirm_clear = None
            save_now(sid, st.session_state.histories)
            st.rerun()
        if c2.button("그만두기", use_container_width=True):
            st.session_state.confirm_clear = None
            st.rerun()

    st.download_button(
        "대화 내려받기",
        data=build_transcript() if has_history else "",
        file_name=f"{persona_name}_대화.md",
        mime="text/markdown",
        use_container_width=True,
        disabled=not has_history,
    )

    st.divider()
    st.subheader("백업")
    st.caption(
        "이 주소를 북마크해두면 새로고침해도 대화가 남습니다. "
        "다만 앱이 다시 배포되면 서버 저장분은 사라지니, 오래 둘 대화는 백업을 받아두십시오."
    )

    any_history = any(st.session_state.histories.values())
    st.download_button(
        "백업 내려받기",
        data=json.dumps({"histories": st.session_state.histories}, ensure_ascii=False, indent=2),
        file_name="점잖은선비_백업.json",
        mime="application/json",
        use_container_width=True,
        disabled=not any_history,
    )

    uploaded = st.file_uploader("백업 불러오기", type=["json"], label_visibility="collapsed")
    if uploaded is not None and st.button("불러온 백업으로 되돌리기", use_container_width=True):
        try:
            restored = clean_histories(json.loads(uploaded.getvalue().decode("utf-8")).get("histories"))
        except Exception as e:
            restored = None
            st.error(f"백업 파일을 읽지 못했습니다. 내려받은 JSON이 맞는지 확인해 주십시오. ({e})")
        if restored:
            for name in PERSONAS:
                st.session_state.histories[name] = restored.get(name, [])
            st.session_state.pending.clear()
            save_now(sid, st.session_state.histories)
            st.rerun()
        elif restored is not None:
            st.error("백업에서 되살릴 대화를 찾지 못했습니다.")


# ============================================================
# 6. 본문 머리말
# ============================================================

st.title("점잖은 선비")
st.caption(f"{persona_name} · {persona['caption']}")

image_path = persona["image"]
if image_path and os.path.exists(image_path):
    st.image(image_path, width=400)

if not history and persona_name not in st.session_state.pending:
    st.info(f"{persona_name}에게 말을 걸어보십시오. 아래에 적거나 마이크로 말하면 됩니다.")


# ============================================================
# 7. 지난 대화 렌더링
# ============================================================

for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ============================================================
# 8. 입력 받기
# ============================================================

client = genai.Client(api_key=api_key)

recognized_text = None

st.write("음성 입력")
audio_data = mic_recorder(start_prompt="녹음 시작", stop_prompt="녹음 완료", key="mic")

# chat_input을 st.columns 안에 두면 Streamlit 버전에 따라 예외가 납니다.
# 최상위에 두면 어느 버전에서든 화면 아래에 고정됩니다.
user_input = st.chat_input("메시지를 입력하거나 마이크로 말씀하세요...")

if audio_data and audio_data.get("bytes"):
    current_audio_id = audio_data.get("id")
    if current_audio_id != st.session_state.last_audio_id:  # 중복 실행 방지
        st.session_state.last_audio_id = current_audio_id
        audio_format = audio_data.get("format", "webm")
        mime_type = f"audio/{audio_format}" if audio_format in ("wav", "mp3") else "audio/webm"

        with st.spinner("음성을 인식하는 중..."):
            try:
                # STT는 페르소나를 배제하고 받아쓰기만 시킵니다.
                stt_response = client.models.generate_content(
                    model=selected_model,
                    contents=[
                        "사용자가 음성으로 말한 내용을 다른 설명 없이 한국어 텍스트로만 그대로 옮겨 적어주세요.",
                        genai.types.Part.from_bytes(data=audio_data["bytes"], mime_type=mime_type),
                    ],
                )
                if stt_response and stt_response.text:
                    recognized_text = stt_response.text.strip()
                if not recognized_text:
                    st.warning("음성에서 글자를 찾지 못했습니다. 다시 녹음해 보십시오.")
            except Exception as e:
                st.error(f"음성 인식이 실패했습니다. 모델과 API 키를 확인해 주십시오. ({e})")

elif user_input:
    recognized_text = user_input

# 질문은 기록이 아니라 대기열에 넣습니다.
# 기록에는 답변이 나온 뒤에 질문과 답변을 한 번에 넣습니다.
if recognized_text:
    st.session_state.pending[persona_name] = {"text": recognized_text, "auto": True}


# ============================================================
# 9. 답변 생성 및 음성 출력
# ============================================================

def to_contents(messages):
    """대화 기록을 Gemini contents 형식으로 바꿉니다.

    Part 객체 대신 dict를 씁니다. google-genai 버전에 따라
    Part.from_text가 위치 인자와 키워드 인자로 갈리기 때문입니다.
    """
    out = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        out.append({"role": role, "parts": [{"text": m["content"]}]})
    return out


def to_speech_text(text):
    """음성으로 읽기 좋게 다듬습니다. 한자와 마크다운 기호를 뺍니다."""
    t = re.sub(r"[\u3400-\u4dbf\u4e00-\u9fff]+", "", text)
    t = re.sub(r"\(\s*[,·\s]*\)", "", t)
    t = re.sub(r"[*_`#>\[\]]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def pcm_to_wav(pcm, rate=24000):
    """Gemini TTS는 원시 PCM을 돌려주므로 재생 가능한 WAV로 감쌉니다."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(pcm)
    return buf.getvalue()


def build_tts_prompt(direction, script):
    """연출 지시와 대사를 분리해 적습니다.

    문서에 따르면 경계가 모호하면 모델이 연출 지시를 소리 내어 읽거나
    안전 분류기가 요청을 거부할 수 있습니다. 그래서 대사 시작 지점을
    명시적으로 표시합니다. 지시는 영어로 적는 편이 결과가 낫습니다.
    """
    return (
        "Read the script below aloud as this character. "
        "Do not read the profile or the notes.\n\n"
        "# DIRECTOR'S NOTES\n"
        f"{direction}\n"
        "Accent: Standard Seoul Korean. The script is in Korean.\n\n"
        "# SCRIPT (read only what follows this line)\n"
        f"{script}"
    )


def synthesize_gemini(client, voice, direction, script):
    """Gemini TTS로 음성을 만듭니다. 실패하면 사유를 함께 돌려줍니다.

    문서가 밝힌 대로 아주 낮은 확률로 오디오 대신 텍스트 토큰이 돌아와
    500으로 실패합니다. 그래서 한 번 다시 시도합니다.
    """
    last = None
    for _ in range(2):
        try:
            interaction = client.interactions.create(
                model=TTS_MODEL,
                input=build_tts_prompt(direction, script),
                response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": voice}]},
            )
            data = getattr(getattr(interaction, "output_audio", None), "data", None)
            if not data:
                last = "오디오가 비어 있습니다."
                continue
            return pcm_to_wav(base64.b64decode(data)), None
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:120]}"
    return None, last


def synthesize_gtts(script):
    buf = io.BytesIO()
    gTTS(text=script, lang="ko").write_to_fp(buf)
    return buf.getvalue()


pending = st.session_state.pending.get(persona_name)

if pending:
    with st.chat_message("user"):
        st.markdown(pending["text"])

    if not pending["auto"]:
        # 앞선 시도가 실패했습니다. 매 실행마다 다시 호출해 사용량을 쓰지 않도록
        # 자동 재시도를 멈추고 사용자가 직접 누르게 합니다.
        st.warning("이 질문에 아직 답을 받지 못했습니다.")
        if st.button("다시 답 받기"):
            pending["auto"] = True
            st.rerun()
        st.stop()

    with st.chat_message("assistant"):
        with st.spinner("생각 중입니다..."):
            # 직전 한 마디가 아니라 대화 기록 전체에 이번 질문을 더해 넘겨야
            # 문맥이 이어집니다.
            turns = history + [{"role": "user", "content": pending["text"]}]
            try:
                response = client.models.generate_content(
                    model=selected_model,
                    contents=to_contents(turns),
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                    ),
                )
                answer = (response.text or "").strip()
            except Exception as e:
                pending["auto"] = False
                st.error(f"답변을 받지 못했습니다. 잠시 뒤 다시 시도해 주십시오. ({e})")
                st.stop()

        if not answer:
            pending["auto"] = False
            st.error("빈 답변이 왔습니다. 다시 시도해 주십시오.")
            st.stop()

        st.markdown(answer)

        # 질문과 답변을 한 번에 저장합니다.
        # 여기까지 왔으면 중단되어도 반쪽만 남는 일이 없습니다.
        history.append({"role": "user", "content": pending["text"]})
        history.append({"role": "assistant", "content": answer})
        st.session_state.pending.pop(persona_name, None)

        save_error = save_now(sid, st.session_state.histories)
        if save_error:
            st.caption(f"이번 대화를 서버에 남기지 못했습니다. 백업을 받아두십시오. ({save_error})")

        if speak_answer:
            spoken = to_speech_text(answer)
            if spoken:
                audio, note = None, None
                if voice_engine == "인물별 목소리 (Gemini TTS)":
                    audio, note = synthesize_gemini(
                        client, persona_voice, persona["direction"], spoken
                    )
                    if audio:
                        st.audio(audio, format="audio/wav", autoplay=True)
                    else:
                        st.caption(f"인물 목소리를 만들지 못해 기본 음성으로 대신합니다. ({note})")
                if audio is None:
                    try:
                        st.audio(synthesize_gtts(spoken), format="audio/mp3", autoplay=True)
                    except Exception as e:
                        st.caption(f"음성 변환은 건너뜁니다. ({e})")
