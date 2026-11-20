# =============================================================
# pages/laboratory.py  (현상 실험실)
# 원인 해부실에서 설명한 원리를 직접 계산해서 확인(검증)하는 페이지
# 실험 4가지: 정수 오버플로·언더플로 → 2038년 시계 → 0.1 + 0.2 (IEEE 754 비트) → 실수 언더플로
# =============================================================

import math
import re
import struct                                         # 실수를 컴퓨터가 저장하는 바이트 그대로 꺼내는 모듈
from datetime import datetime, timedelta, timezone    # 날짜+시각, 시간 간격, 시간대 (2038년 실험에서 사용)
from decimal import Decimal                           # 10진수를 정확하게 계산하는 자료형
from html import escape                               # 글자 속 <, > 같은 기호를 안전하게 바꿔 주는 함수

import streamlit as st

from common import crt_frame, open_case, page_banner, render_html

# 결과 상자 종류: 종류 이름 → (상자 색 이름, 앞에 붙는 제목)
RESULT_STYLES = {
    "diff": ("bt-err", "🔎 오류 현상이 재현됐어요"),   # 컴퓨터가 예상과 다르게 동작함 (실험 성공!)
    "same": ("bt-ok", "✅ 결과가 같아요"),              # 이번 값에서는 차이가 없음
    "note": ("bt-key", "💡 핵심 정리"),                        # 정리 문장
    "input": ("bt-obs", "⌨️ 입력을 확인해 주세요"),       # 입력이 비었거나 잘못됨
}

# 실험 목록: "실험 이름표": (화면에 보일 이름, 관련 사례 번호)
LABS = {
    "int_overflow": ("① 정수 오버플로·언더플로", 1),
    "y2038": ("② 2038년 시계", 1),
    "float_error": ("③ 0.1 + 0.2와 IEEE 754", 2),
    "float_underflow": ("④ 실수 언더플로", 2),
}

UNIX_START = datetime(1970, 1, 1, tzinfo=timezone.utc)    # 유닉스 시간의 출발점 (1970-01-01 00:00:00 UTC)

# 실수 64비트를 색으로 나눠 보여 주는 디자인 (정수 비트 칸 .bits는 common.py에 있다)
#   .s = 부호 칸(빨강) / .e = 지수 칸(파랑) / .m = 가수 칸(라임) / .gap = 부분 사이 틈
BIT_STYLE = """
<style>
/* 정수 비트 32칸이 한 줄에 다 들어가게 */
.bits.b32 { flex-wrap: nowrap; gap: 6px; }
.bits.b32 span { width: 27px; height: 38px; line-height: 33px; font-size: 1.1rem; }
/* 64칸을 16칸씩 4줄로 크게 놓는다. 맨 앞 칸은 '몇 번째 비트부터인지' 줄 번호 */
.fbits { display: grid; grid-template-columns: 74px repeat(16, 36px); gap: 4px; width: max-content; margin: 8px 0 12px; }
.fbits .bit { box-sizing: border-box; width: 36px; height: 46px; line-height: 41px; text-align: center; font-size: 1.3rem; border: 2px solid var(--ink);
              font-family: 'Galmuri11', monospace; font-weight: 700; }
.fbits .row-no { align-self: center; font-size: 0.85rem; font-weight: 700; color: var(--dim); white-space: nowrap; }
.fbits-scroll { max-width: 100%; overflow-x: auto; padding: 2px 3px 8px; }
.fbits .s { background: #F6D5CF; color: var(--red); border-color: var(--red); }
.fbits .e { background: #D6E8F7; color: var(--sky); border-color: var(--sky); }
.fbits .m { background: var(--lime-soft); color: var(--ink); }
.fbits .gap { display: none; }
.flegend { display: flex; flex-wrap: wrap; gap: 14px; font-size: 0.9rem; margin-bottom: 4px; }
.flegend b { padding: 0 6px; border: 2px solid var(--ink); }
.flegend .s { background: #F6D5CF; } .flegend .e { background: #D6E8F7; } .flegend .m { background: var(--lime-soft); }
.lab-guide { font-size: 0.95rem; color: var(--dim); margin: 2px 0 6px; }
</style>
"""


# 위첨자 숫자표: 일반 숫자를 위첨자 글자로 바꾼다. 예) "-308" → "⁻³⁰⁸"
SUPERSCRIPT = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def readable_number(value, in_code=False):
    """컴퓨터식 표기(2.2e-308)를 교과서식 표기(2.2 × 10⁻³⁰⁸)로 바꾼다.
    in_code=True: 코드 상자의 글꼴에는 위첨자 ³ 글자가 없어서, '10의 -308제곱'처럼 글로 풀어 쓴다."""
    raw = str(value)
    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))[eE]([+-]?\d+)", raw)
    if not match:
        return raw
    coefficient, exponent = match.groups()
    exponent = int(exponent)                         # int()로 앞의 + 기호와 0을 정리한다 (예: "+05" → 5)
    if in_code:
        return f"{coefficient} × 10의 {exponent}제곱"
    return f"{coefficient} × 10{str(exponent).translate(SUPERSCRIPT)}"


LAB_FLOAT_STYLE = """
<style>
/* 현상 실험실 ③에만 적용되는 조밀한 실험 레이아웃 */
.st-key-float_experiment [data-testid="stVerticalBlock"] { gap: .65rem !important; }
.st-key-float_experiment [data-testid="stMarkdownContainer"] p { margin: 0 0 .25rem !important; }
.st-key-float_experiment [data-testid="stRadio"] > div[role="radiogroup"] {
  display: flex; flex-wrap: wrap; flex-direction: row; gap: 10px;
}
.st-key-float_experiment [data-testid="stRadio"] label {
  border: 1px solid #6D8A66; background: #F4F7E9;
  border-radius: 4px; padding: 9px 13px; margin: 0 !important;
}
.st-key-float_experiment [data-testid="stRadio"] label:has(input:checked) {
  background: #DCEBB4; border: 2px solid #1F4D25;
}
.st-key-float_experiment [data-testid="stCode"] { max-width: 880px; }
.float-compare { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 6px 0 12px; }
.float-compare > div { border: 1px solid #98AB8E; background: #F6F8EE; padding: 12px; min-width: 0; }
.float-compare strong { display: block; font-size: 1rem; color: #1F4D25; background: none !important; }
.float-compare .value { display: block; margin: 6px 0; font-size: 1.08rem; font-weight: 750; overflow-wrap: anywhere; }
.float-compare small { color: #415946; line-height: 1.45; }
@media (max-width: 750px) { .float-compare { grid-template-columns: 1fr; } }
/* 예측 선택지 + 실행 버튼 한 줄: 각 요소가 내용만큼만 차지하고 왼쪽부터 붙는다 */
.st-key-float_prediction_row { justify-content: flex-start !important; gap: 10px; flex-wrap: wrap; }
.st-key-float_prediction_row > [data-testid="stElementContainer"] { width: auto !important; flex: 0 0 auto !important; }
.st-key-float_prediction_row div.stButton { padding-top: 0; }
</style>
"""


# -------------------------------------------------------------
# 0. 공통 함수
# -------------------------------------------------------------

def restore_lab():
    """원인 해부실에서 고른 실험이 있으면 그 실험을 먼저 보여 준다."""
    saved = st.session_state.get("saved_lab", "int_overflow")
    if saved not in LABS:                       # 예전 버전에서 저장된 이름이면 첫 실험으로
        saved = "int_overflow"
    if "lab_topic" not in st.session_state:
        st.session_state["lab_topic"] = saved


def save_lab():
    """고른 실험을 저장해서 다른 페이지에 다녀와도 유지한다."""
    st.session_state["saved_lab"] = st.session_state["lab_topic"]


def show_lab_selector():
    """실험 4개를 한 줄짜리 버튼(라디오)으로 보여 준다. 무엇이 있는지 한눈에 보이게"""
    restore_lab()
    st.radio(
        "실험 선택",
        list(LABS.keys()),
        key="lab_topic",
        format_func=lambda lab: LABS[lab][0],    # 화면에는 이름표 대신 실험 이름을 보여 준다
        horizontal=True,
        on_change=save_lab,
        label_visibility="collapsed",
    )


def show_case_link(lab):
    """실험과 관련된 사례의 원인 해부실로 가는 버튼"""
    case_id = LABS[lab][1]
    if st.button(f"BUG-{case_id:03d} 원인 설명 보기", key=f"lab_link_{lab}", icon=":material/menu_book:", width="stretch"):
        open_case(case_id)


def lab_title(title, guide):
    """실험 제목과 '무엇을 해 보는지' 안내 한 줄을 보여 준다."""
    st.markdown(f"#### 🧪 {title}")
    render_html(f'<div class="lab-guide">{escape(guide)}</div>')


def result_box(kind, text):
    """실험 결과를 앱 디자인에 맞는 상자로 보여 준다."""
    box_class, label = RESULT_STYLES[kind]
    render_html(f"""
        <div class="bt-box {box_class}">
            <div class="bt-box-label">{label}</div>
            <div>{escape(text)}</div>
        </div>
    """)


# -------------------------------------------------------------
# 1. 정수 비트 다루기 (2의 보수)
# -------------------------------------------------------------

def to_signed(value, bits):
    """정수를 bits칸짜리 '부호 있는 정수'에 담았을 때의 값으로 바꾼다. (2의 보수 규칙)"""
    mask = (1 << bits) - 1        # << : 1을 bits칸 왼쪽으로 민 뒤 1을 빼면 → 모든 칸이 1인 수 (32비트면 0xFFFFFFFF)
    value = value & mask          # & (AND) : 칸 밖으로 넘친 비트를 잘라 내고 bits칸만 남긴다
    if value >= 1 << (bits - 1):  # 맨 앞 칸(부호 비트)이 1이면
        value -= 1 << bits        # 음수로 읽는다 → 이것이 2의 보수 해석
    return value


def to_unsigned(value, bits):
    """정수를 bits칸짜리 '부호 없는 정수'(0과 양수만)에 담았을 때의 값. 넘친 비트만 잘라 낸다."""
    return value & ((1 << bits) - 1)


def bit_string(value, bits):
    """정수를 bits칸짜리 0과 1 글자로 바꾼다. 음수도 2의 보수 모양 그대로 보인다."""
    # format(수, "032b") : 32칸짜리 2진수 글자로 바꾼다. 앞의 빈 칸은 0으로 채운다.
    return format(value & ((1 << bits) - 1), f"0{bits}b")


def show_bits(value, bits, label):
    """0과 1을 픽셀 칸으로 그린다. 8칸(1바이트)마다 띄우고, 맨 앞 칸(부호 비트)은 빨간 테두리로 표시한다."""
    text = bit_string(value, bits)
    groups = ""
    for start in range(0, bits, 8):                  # 8칸씩 묶는다
        cells = ""
        for position in range(start, start + 8):
            kind = "one" if text[position] == "1" else "zero"
            if position == 0:
                kind += " sign"                      # 맨 앞 칸 = 부호 비트
            cells += f'<span class="{kind}">{text[position]}</span>'
        groups += f'<div class="byte">{cells}</div>'
    # b32: 32칸일 때 한 줄에 다 들어가는 크기로 그린다
    render_html(f'<div class="bits-label">{escape(label)}</div><div class="bits b{bits}">{groups}</div>')


def show_negative_steps(positive, bits):
    """양수 → 음수를 2의 보수로 만드는 과정: ① 원래 수 → ② 모든 칸 뒤집기(~) → ③ 1 더하기"""
    flipped = ~positive                              # ~ (NOT) : 0은 1로, 1은 0으로 모든 칸을 뒤집는다
    st.code(f"① 원래 수 {positive:>13,} : {bit_string(positive, bits)}\n"
            f"② 모든 칸 뒤집기(~)     : {bit_string(flipped, bits)}\n"
            f"③ 1 더하기              : {bit_string(flipped + 1, bits)}  = {-positive:,}")


# -------------------------------------------------------------
# 2. 실험 ① 정수 오버플로·언더플로 (BUG-001)
# -------------------------------------------------------------

# 정수 실험의 칸 수: 실제 사례(유튜브 조회수, 2038년 문제, 보잉 787)가 모두 부호 있는 32비트에서 생겼다
INT_BITS = 32

# 자동차 주행 거리계처럼 '계산 전 → 계산 후'를 큰 숫자로 보여 주는 디자인
ODOMETER_STYLE = """
<style>
.odo { display: flex; align-items: center; flex-wrap: wrap; gap: 12px; margin: 10px 0 6px; }
.odo-box { background: #1E2B21; border: 4px solid #0F1A12; padding: 8px 16px; min-width: 190px; text-align: center; box-shadow: inset 0 0 10px rgba(198,234,78,.3); }
.odo-box small { display: block; color: #CFE3A0; font-size: 0.85rem; margin-bottom: 2px; }
.odo-box b { font-family: 'Press Start 2P', monospace; color: #C6EA4E; font-size: 1.35rem; letter-spacing: 1px; }
.odo-box.bad { border-color: var(--red); animation: cal-shake .5s ease 1; }
.odo-box.bad b { color: #FF8A7A; }
.odo-op { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: 1.2rem; }
.odo-math { color: var(--dim); font-size: 0.95rem; }
@keyframes cal-shake { 0%, 100% { transform: translateX(0); } 20%, 60% { transform: translateX(-6px); } 40%, 80% { transform: translateX(6px); } }
</style>
"""


def int_limits(bits):
    """bits칸짜리 부호 있는 정수의 (최솟값, 최댓값). 예) 8비트 → (-128, 127)"""
    return -(1 << (bits - 1)), (1 << (bits - 1)) - 1


def set_int_example(start, operator):
    """'최댓값 + 1', '최솟값 − 1' 버튼을 누르면 입력칸 값을 예시로 바꾼다. (on_click에서 실행)"""
    st.session_state["int_start"] = start
    st.session_state["int_operator"] = operator
    st.session_state["int_amount"] = 1


def show_int_examples(bits):
    """예시 버튼 2개를 한 줄에 작게 놓는다. (보조 버튼이라 크게 만들지 않는다)"""
    smallest, largest = int_limits(bits)
    # key가 compact_로 시작하는 상자 안의 버튼은 작은 크기로 그려진다 (common.py의 '작은 크기' 디자인)
    with st.container(key="compact_int_examples", horizontal=True, vertical_alignment="center"):
        render_html('<div class="compact-label">바로 해 보기</div>')
        st.button("최댓값 + 1", key="int_ex_over", on_click=set_int_example, args=(largest, "+"))
        st.button("최솟값 − 1", key="int_ex_under", on_click=set_int_example, args=(smallest, "−"))


def show_odometer(start, operator, amount, real_result, stored_result, bits):
    """계산 전 → 계산 후를 주행 거리계처럼 큰 숫자로 보여 준다. 넘쳐서 값이 바뀌면 빨갛게 흔들린다."""
    bad = " bad" if real_result != stored_result else ""
    render_html(f"""
        <div class="odo">
            <div class="odo-box"><small>계산 전</small><b>{start:,}</b></div>
            <div class="odo-op">{operator} {amount:,} →</div>
            <div class="odo-box{bad}"><small>{bits}비트에 저장된 값</small><b>{stored_result:,}</b></div>
            <div class="odo-math">수학으로 계산하면 {real_result:,}</div>
        </div>
    """)


def show_int_result(start, operator, amount, bits):
    """수학 계산 결과와 bits칸 정수에 담은 결과를 큰 숫자와 비트로 비교한다."""
    smallest, largest = int_limits(bits)
    real_result = start + amount if operator == "+" else start - amount   # 수학 계산 (Python 정수는 칸 제한이 없다)
    stored_result = to_signed(real_result, bits)                          # bits칸에 담았을 때의 값
    # 비트가 주인공: 비트 칸을 먼저 크게 보여 주고, 숫자 계기판은 그 아래에 요약으로 놓는다
    show_bits(start, bits, f"계산 전: {start:,}")
    show_bits(stored_result, bits, f"계산 후 {bits}비트에 저장된 값: {stored_result:,}")
    show_odometer(start, operator, amount, real_result, stored_result, bits)

    if real_result > largest:          # 위쪽 끝을 넘음 → 오버플로
        result_box("diff", f"최댓값 {largest:,}을 넘어서 음수 {stored_result:,}(으)로 넘어갔어요! (정수 오버플로) "
                           "받아올림이 맨 앞 칸(부호 비트)까지 올라가 1이 되어 음수로 읽혀요.")
    elif real_result < smallest:       # 아래쪽 끝을 넘음 → 정수 언더플로
        result_box("diff", f"최솟값 {smallest:,}보다 작아져서 양수 {stored_result:,}(으)로 넘어갔어요! (정수 언더플로) "
                           "빌림 때문에 맨 앞 칸(부호 비트)이 0이 되어 양수로 읽혀요.")
    else:
        result_box("same", f"{bits}비트 범위 안이라 수학 계산과 같아요. 위의 예시 버튼을 눌러 보세요.")

    # 결과가 음수라면, 그 음수가 2의 보수로 어떻게 만들어졌는지 단계별로 보여 준다.
    if stored_result == smallest:
        result_box("note", f"{smallest:,}은 {bits}비트에서 가장 작은 수예요. 짝이 되는 +{-smallest:,}은 {bits}비트에 담을 수 없어서 "
                           "'1 다음에 0만 이어지는' 특별한 모양이에요. (음수 쪽이 하나 더 많은 이유)")
    elif stored_result < 0:
        st.markdown("**이 음수는 이렇게 만들어져요 (2의 보수: 뒤집고 1 더하기)**")
        show_negative_steps(-stored_result, bits)


def run_int_overflow_lab():
    """32비트 정수에 더하거나 빼 보며 오버플로·언더플로와 2의 보수를 확인한다."""
    lab_title("가장 큰 수에 1을 더하면? 가장 작은 수에서 1을 빼면?",
              "가정: 부호 있는 32비트 정수에서, 칸 밖으로 넘친 비트를 그냥 버리는 경우 (조회수·2038년 문제와 같은 조건)")
    render_html(ODOMETER_STYLE)
    # 처음 들어왔을 때의 값 (버튼이 session_state로 값을 바꾸므로, 입력칸에는 value=를 따로 주지 않는다)
    bits = INT_BITS
    smallest, largest = int_limits(bits)
    st.session_state.setdefault("int_start", largest)
    st.session_state.setdefault("int_operator", "+")
    st.session_state.setdefault("int_amount", 1)
    show_int_examples(bits)                                     # 예시 버튼 (한 줄, 작게)
    start_column, operator_column, amount_column, _ = st.columns([1.6, 0.7, 1.1, 1.6], vertical_alignment="bottom")
    # min/max: 고른 칸 수의 범위 안의 수만 입력할 수 있게 막는다
    start = start_column.number_input(f"{bits}비트 정수", min_value=smallest, max_value=largest, step=1, key="int_start")
    operator = operator_column.selectbox("계산", ["+", "−"], key="int_operator")
    amount = amount_column.number_input("얼마나", min_value=0, max_value=largest, step=1, key="int_amount")
    show_int_result(int(start), operator, int(amount), bits)


# -------------------------------------------------------------
# 3. 실험 ② 2038년 시계 (BUG-001)
# -------------------------------------------------------------

# 시계 종류: 이름 → 32비트 칸에 담는 함수 (None = 64비트라 넘치지 않음)
CLOCK_TYPES = {
    "부호 있는 32비트 (옛 방식)": lambda seconds: to_signed(seconds, 32),
    "부호 없는 32비트": lambda seconds: to_unsigned(seconds, 32),
    "부호 있는 64비트 (요즘 방식)": lambda seconds: to_signed(seconds, 64),
}

# 살펴볼 순간: 이름 → 그 시계가 담을 수 있는 마지막 초
MOMENTS = {
    "2038년 1월 19일 · 옛 방식 시계가 셀 수 있는 마지막 1초": (1 << 31) - 1,
    "2106년 2월 7일 · 부호 없는 32비트 시계가 셀 수 있는 마지막 1초": (1 << 32) - 1,
}


def seconds_to_text(seconds):
    """유닉스 시간(초)을 날짜·시각 글자로 바꾼다. 날짜로 나타낼 수 없을 만큼 크면 안내 글자를 돌려준다."""
    try:
        # timedelta(seconds=초): 출발점에 초를 더해서 날짜·시각을 계산한다 (음수면 과거로 간다)
        return f"{UNIX_START + timedelta(seconds=seconds):%Y-%m-%d %H:%M:%S} UTC"
    except OverflowError:
        return "(아주 먼 미래)"


# 탁상 달력 + 디지털 시계 디자인. 날짜가 틀어진 시계(.bad)는 빨갛게 바뀌고 한 번 흔들린다.
CALENDAR_STYLE = """
<style>
.cal-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin: 12px 0; }
.cal-card { border: 3px solid var(--ink); background: #FAFBEF; padding: 10px 12px 12px; text-align: center; min-width: 0; }
.cal-name { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: 0.95rem; margin-bottom: 8px; }
.cal-page { position: relative; margin: 0 auto; max-width: 210px; background: #FFFFFF; border: 3px solid var(--ink); box-shadow: 5px 5px 0 rgba(31,77,37,.25); }
.cal-page::before, .cal-page::after { content: ""; position: absolute; top: -10px; width: 12px; height: 18px; border: 3px solid var(--ink); border-radius: 6px; background: #E8DDC4; }
.cal-page::before { left: 28%; } .cal-page::after { right: 28%; }
.cal-year { background: var(--ink); color: #F4F8E8; font-family: 'Galmuri11', sans-serif; font-weight: 700; font-size: 1.15rem; padding: 6px 0 4px; }
.cal-month { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: 1.05rem; margin-top: 6px; }
.cal-day { font-family: 'Press Start 2P', monospace; color: var(--ink); font-size: 2.6rem; line-height: 1.3; }
.cal-week { color: var(--dim); font-size: 0.9rem; margin-bottom: 8px; }
.cal-clock { display: inline-block; margin-top: 12px; padding: 6px 14px; background: #1E2B21; color: #C6EA4E; border: 3px solid #0F1A12;
             font-family: 'Press Start 2P', monospace; font-size: 1.05rem; letter-spacing: 2px; box-shadow: inset 0 0 8px rgba(198,234,78,.35); }
.cal-stamp { margin-top: 10px; font-family: 'Galmuri11', sans-serif; font-weight: 700; font-size: 1rem; color: #2F6B2A; }
.cal-card.bad { border-color: var(--red); background: #FBE7DF; animation: cal-shake .5s ease 1; }
.cal-card.bad .cal-year { background: var(--red); }
.cal-card.bad .cal-day, .cal-card.bad .cal-month { color: var(--red); }
.cal-card.bad .cal-clock { color: #FF8A7A; }
.cal-card.bad .cal-stamp { color: var(--red); font-size: 1.08rem; }
@keyframes cal-shake { 0%, 100% { transform: translateX(0); } 20%, 60% { transform: translateX(-6px); } 40%, 80% { transform: translateX(6px); } }
.cal-now { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: 1.05rem; }
@media (max-width: 700px) { .cal-grid { grid-template-columns: 1fr; } }
</style>
"""
WEEKDAYS = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]   # datetime.weekday(): 월요일 = 0


def calendar_card_html(clock_name, real_seconds, stored_seconds):
    """시계 하나를 탁상 달력 + 디지털 시계 모양의 HTML로 만든다. 날짜가 틀어지면 빨간 카드가 된다."""
    try:
        moment = UNIX_START + timedelta(seconds=stored_seconds)       # 이 시계가 읽은 날짜·시각
    except OverflowError:                                              # 날짜로 나타낼 수 없을 만큼 먼 미래
        return f'<div class="cal-card"><div class="cal-name">{escape(clock_name)}</div><div class="cal-stamp">아주 먼 미래</div></div>'
    real_year = (UNIX_START + timedelta(seconds=real_seconds)).year
    if stored_seconds == real_seconds:
        css, stamp = "cal-card", "✅ 정상"
    else:
        css, stamp = "cal-card bad", f"❌ {real_year - moment.year}년 전으로 돌아감!"
    return f"""
        <div class="{css}">
            <div class="cal-name">{escape(clock_name)}</div>
            <div class="cal-page">
                <div class="cal-year">{moment.year}년</div>
                <div class="cal-month">{moment.month}월</div>
                <div class="cal-day">{moment.day}</div>
                <div class="cal-week">{WEEKDAYS[moment.weekday()]}</div>
            </div>
            <div class="cal-clock">{moment:%H:%M:%S}</div>
            <div class="cal-stamp">{stamp}</div>
        </div>
    """


def run_y2038_lab():
    """같은 초를 세 종류의 시계(32비트 부호 있음·없음, 64비트)에 담아, 달력과 시계로 날짜가 어떻게 읽히는지 비교한다."""
    lab_title("1초가 지나면 시계는 몇 년을 가리킬까?",
              "유닉스 시간(1970-01-01 0시부터 센 초)을 서로 다른 칸에 담았어요. 슬라이더를 1칸씩 움직여 달력이 어떻게 바뀌는지 보세요.")
    render_html(CALENDAR_STYLE)
    moment_name = st.radio("살펴볼 순간", list(MOMENTS.keys()), key="y2038_moment", horizontal=True)
    offset = st.slider("그 순간에서 몇 초 지났나요?", -3, 3, 0, key="y2038_offset")
    seconds = MOMENTS[moment_name] + offset              # 실제로 흐른 초

    render_html(f'<div class="cal-now">⏱️ 실제로 흐른 시간: {seconds:,}초 → {escape(seconds_to_text(seconds))}</div>')
    # 비트가 주인공: 32비트 칸을 달력보다 먼저 보여 준다 → 비트가 바뀌는 순간 아래 달력이 어떻게 되는지 이어서 본다
    show_bits(to_signed(seconds, 32), 32, "부호 있는 32비트 칸에 담긴 비트 (빨간 테두리 = 부호 비트)")
    cards = ""
    broken = []                                          # 날짜가 틀어진 시계 이름 모음
    for clock_name, store in CLOCK_TYPES.items():
        stored = store(seconds)                          # 이 시계에 실제로 담기는 값
        if stored != seconds:
            broken.append(clock_name)
        cards += calendar_card_html(clock_name, seconds, stored)
    render_html('<div class="cal-grid">' + cards + '</div>')

    if broken:
        result_box("diff", f"{', '.join(broken)} 시계가 끝을 넘어 엉뚱한 날짜로 돌아갔어요!")
    else:
        result_box("same", "아직 모든 시계가 정확해요. 슬라이더를 오른쪽으로 1칸 움직여 보세요.")
    result_box("note", "부호 없는 32비트로 바꾸면 2106년까지 버티지만 1970년 이전 날짜(음수)를 담을 수 없어요. "
                       "64비트는 약 2,920억 년을 담을 수 있어서 요즘 운영체제가 쓰는 해결 방법이에요.")


# -------------------------------------------------------------
# 4. 실수 비트 다루기 (IEEE 754, 64비트)
# -------------------------------------------------------------

def float_bits(number):
    """실수를 컴퓨터에 저장된 64칸짜리 0과 1 글자로 바꾼다."""
    # struct.pack(">d", 수): 실수를 8바이트(64비트)로 저장한 모양 그대로 꺼낸다.
    # struct.unpack(">Q", ...): 그 8바이트를 '부호 없는 64비트 정수'로 다시 읽는다 → 2진수 글자로 바꿀 수 있다.
    raw = struct.unpack(">Q", struct.pack(">d", number))[0]
    return format(raw, "064b")


def show_float_bits(number, label):
    """64비트를 부호(1칸, 빨강)·지수(11칸, 파랑)·가수(52칸, 라임)로 색을 나눠 그린다."""
    text = float_bits(number)
    cells = ""
    for position, bit in enumerate(text):
        if position % 16 == 0:                       # 16칸마다 새 줄: 줄 앞에 '1~16번'처럼 번호를 붙인다
            cells += f'<span class="row-no">{position + 1}~{position + 16}번</span>'
        kind = "s" if position == 0 else ("e" if position <= 11 else "m")
        cells += f'<span class="bit {kind}">{bit}</span>'
    render_html(f"""
        <div class="bits-label">{escape(label)}</div>
        <div class="flegend"><span><b class="s">부호 1칸</b> 0=양수</span><span><b class="e">지수 11칸</b> 2의 몇 제곱인지</span>
        <span><b class="m">가수 52칸</b> 유효숫자</span></div>
        <div class="fbits-scroll"><div class="fbits">{cells}</div></div>
    """)


def float_parts(number):
    """64비트를 나눠 (지수 칸 값, 가수 칸 값, 상태 이름)을 돌려준다."""
    text = float_bits(number)
    exponent = int(text[1:12], 2)                    # int(글자, 2): 2진수 글자를 정수로
    mantissa = int(text[12:], 2)
    if number == 0:
        state = "0 (모든 칸이 0)"
    elif exponent == 0:
        state = "비정규 수 (지수 칸이 모두 0 → 정밀도를 깎아 가며 저장)"
    else:
        state = "정상 수"
    return exponent, mantissa, state


# -------------------------------------------------------------
# 5. 실험 ③ 0.1 + 0.2와 IEEE 754 (BUG-002)
# -------------------------------------------------------------

def show_float_result(first_text, second_text):
    """입력한 두 수를 컴퓨터 방식과 정확한 방식으로 더해서 결과를 비교한다."""
    # 숫자가 아닌 값을 넣으면 계산 중에 오류가 나므로 try로 미리 막는다.
    # (ValueError: float() 변환 실패, ArithmeticError: Decimal 계산 실패)
    try:
        first_number = float(first_text)
        second_number = float(second_text)
        computer_result = first_number + second_number                # 컴퓨터 방식(2진수) 계산
        exact_result = Decimal(first_text) + Decimal(second_text)     # 10진수로 정확히 계산
    except (ValueError, ArithmeticError, OverflowError):
        result_box("input", "계산할 수 있는 숫자를 입력해 주세요. 예) 0.1")
        return

    # !r (repr): 숫자를 줄이지 않고 컴퓨터가 가진 값 그대로 보여 준다.
    st.code(f"컴퓨터 계산 (float)   : {first_text} + {second_text} = {readable_number(repr(computer_result), in_code=True)}\n"
            f"정확한 계산 (Decimal) : {first_text} + {second_text} = {exact_result}")
    if Decimal(computer_result) == exact_result:
        result_box("same", "이번 계산 결과는 정확한 10진수 값과 일치해요. (예: 0.5 + 0.25)")
    elif computer_result == float(exact_result):
        result_box("note", "출력은 자연스러워 보여도 내부 값은 정확한 10진수 결과와 달라요. 저장·계산 중 반올림이 일어날 수 있어요.")
    else:
        result_box("diff", f"두 결과가 달라요! 컴퓨터 계산 결과({readable_number(repr(computer_result))})는 정확한 값({exact_result})과 다른 수예요.")

    # Decimal(float값): 컴퓨터 안에 '실제로' 저장된 값을 끝까지 보여 준다.
    st.markdown("**컴퓨터 안에 실제로 저장된 값** (저장하는 순간 이미 조금 달라요)")
    st.code(f"{first_text} → {Decimal(first_number)}\n"
            f"{second_text} → {Decimal(second_number)}")
    show_float_bits(first_number, f"'{first_text}'을(를) 저장한 64비트 (IEEE 754)")
    result_box("note", "0.1의 가수 칸을 보면 1001 1001 …이 되풀이되다가 52칸 끝에서 잘려 반올림돼요. "
                       "끝없는 2진 소수를 52칸에 담을 수 없어서 생기는 오차예요.")


def show_float_error_chart():
    """0.1을 여러 번 더할수록 오차가 어떻게 쌓이는지 그래프로 보여 준다."""
    repeat_count = st.slider("📈 0.1을 계속 더하면 오차는? (더하는 횟수)", 10, 1000, 100, step=10, key="float_repeat")
    total = 0.0
    errors = []
    for count in range(1, repeat_count + 1):
        total += 0.1                                   # 컴퓨터 방식으로 0.1을 더한다
        exact = Decimal(count) / Decimal(10)           # 정확한 값 (count × 0.1)
        errors.append(float(abs(Decimal(total) - exact)))   # 둘의 차이 = 오차
    draw_line_chart(errors)
    st.caption(f"0.1을 {repeat_count}번 더한 결과: {readable_number(repr(total))} (정확한 값: {Decimal(repeat_count) / Decimal(10)})")


def draw_line_chart(values):
    """값 목록을 꺾은선 그래프(SVG 그림)로 직접 그린다. 가로축 = 더한 횟수, 세로축 = 오차"""
    width, height, margin = 1000, 145, 27         # 그림 크기와 안쪽 여백(px). 가로로 넓게 → 글자가 지나치게 커지지 않는다
    largest = max(values) or 1                    # 가장 큰 오차 (0이면 나눗셈을 못 하니 1로)
    last_index = len(values) - 1
    # 각 값을 그림 위의 (x, y) 좌표로 바꾼다. SVG는 위쪽이 0이라서 y는 높이에서 빼 준다.
    points = []
    for index, value in enumerate(values):
        x = margin + index / last_index * (width - 2 * margin)
        y = height - margin - value / largest * (height - 2 * margin)
        points.append(f"{x:.1f},{y:.1f}")
    # polyline: 점들을 순서대로 이은 꺾은선
    render_html(f"""
        <svg class="lab-chart" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
            <line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#1F4D25" stroke-width="3"/>
            <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#1F4D25" stroke-width="3"/>
            <polyline points="{' '.join(points)}" fill="none" stroke="#A23A2E" stroke-width="3" stroke-linejoin="bevel"/>
            <text x="{margin + 4}" y="{margin - 8}" font-size="13" fill="#1F4D25">최대 오차 {readable_number(format(largest, '.1e'))}</text>
            <text x="{margin}" y="{height - 8}" font-size="13" fill="#1F4D25">1번</text>
            <text x="{width - margin}" y="{height - 8}" font-size="13" fill="#1F4D25" text-anchor="end">{len(values)}번 더함</text>
        </svg>
    """)


def reset_float_prediction():
    """선택지가 바뀌면 이전에 공개한 정답을 숨긴다."""
    st.session_state["float_prediction_shown"] = False
    st.session_state.pop("float_prediction_answer", None)


def show_float_prediction():
    """예측 → 결과 확인 → 세 가지 계산 비교를 한 화면에 배치한다."""
    st.markdown("#### 01 · 먼저 결과를 예상해 보세요")
    st.caption("일반 계산기에는 0.3으로 보이지만, Python으로 계산하면 어떨까요?")
    options = ["0.3", "0.30000000000000004", "계산할 수 없음"]
    # 선택지 3개와 '계산 실행' 버튼을 한 줄에 놓아서 오른쪽 빈 공간을 쓴다
    with st.container(key="float_prediction_row", horizontal=True, vertical_alignment="center"):
        choice = st.radio(
            "0.1 + 0.2의 Python 출력 결과는?", options,
            key="float_prediction_choice", index=None, horizontal=True,
            label_visibility="collapsed",
            on_change=reset_float_prediction,
        )
        if st.button("계산 실행 · 정답 확인", key="float_prediction_reveal", type="primary", disabled=choice is None):
            st.session_state["float_prediction_shown"] = True
            st.session_state["float_prediction_answer"] = choice
    if st.session_state.get("float_prediction_shown", False):
        answer = st.session_state.get("float_prediction_answer")
        if answer == options[1]:
            st.success("정확해요! Python에서는 0.30000000000000004로 표시돼요.")
        else:
            st.info("실제 출력은 0.30000000000000004예요. 계산기가 고장 난 것이 아니라 저장 방식의 차이예요.")
        st.code("print(0.1 + 0.2)  # 0.30000000000000004\nprint(0.1 + 0.2 == 0.3)  # False", language="python")
    st.markdown("#### 02 · 같은 덧셈인데 왜 다르게 보일까요?")
    comparison = [
        ("0.5 + 0.25", "0.75", "두 수 모두 2진수로 정확하게 저장돼요."),
        ("0.1 + 0.3", "0.4", "저장 오차는 있지만 출력에서는 드러나지 않아요."),
        ("0.1 + 0.2", "0.30000000000000004", "작은 오차가 출력에도 나타나요."),
    ]
    cards = "".join(
        f'<div><strong>{escape(expr)}</strong><span class="value">{escape(result)}</span><small>{escape(note)}</small></div>'
        for expr, result, note in comparison
    )
    render_html(f'<div class="float-compare">{cards}</div>')
    st.caption("정상적으로 표시돼도 내부 저장값에는 오차가 있을 수 있어요. 모든 소수 계산에서 오차가 보이는 것은 아니에요.")
    st.markdown("#### 03 · 직접 숫자를 바꿔 계산하기")


def run_float_error_lab():
    """두 소수를 더해서 컴퓨터 계산 결과와 정확한 값을 비교하고, 저장된 비트와 쌓이는 오차를 보여 준다."""
    render_html(LAB_FLOAT_STYLE)
    with st.container(key="float_experiment"):
        lab_title("0.1 + 0.2는 정말 0.3일까?", "결과를 예상한 다음, 실제 계산과 비교해 보세요.")
        show_float_prediction()
    first_column, second_column = st.columns(2, gap="medium")
    first_text = first_column.text_input("첫 번째 수", "0.1", key="float_first").strip()
    second_text = second_column.text_input("두 번째 수", "0.2", key="float_second").strip()
    show_float_result(first_text, second_text)
    st.divider()
    st.markdown("##### 반복할수록 쌓이는 오차")
    show_float_error_chart()


# -------------------------------------------------------------
# 6. 실험 ④ 실수 언더플로 (BUG-002)
# -------------------------------------------------------------

UNDERFLOW_START = 1e-300          # 출발값: 이미 아주 작지만 '정상 수'인 수


def halving_steps(start):
    """start를 0이 될 때까지 계속 2로 나눈 값들을 목록으로 돌려준다. (마지막 값은 0.0)"""
    values = [start]
    while values[-1] != 0.0:          # 0이 될 때까지 반복
        values.append(values[-1] / 2)
    return values


# 언더플로 단계 표시 디자인: 3단계 칸(지금 단계만 켜짐) + 남은 유효 비트 53칸(하나씩 꺼짐)
UNDERFLOW_STYLE = """
<style>
/* 64비트 그림 오른쪽 좁은 칸에 들어가도록 단계 3개를 세로로 쌓는다 */
.uf-stages { display: flex; flex-direction: column; gap: 4px; margin: 4px 0 8px; }
.uf-arrow { text-align: center; line-height: 1; }
/* 지금 값: 작은 이름 아래에 숫자 한 줄. 유효숫자 5자리로 줄이고 nowrap으로 '× 10⁻³⁰⁸'이 다음 줄로 떨어지지 않게 */
.uf-value small { display: block; font-size: 0.85rem; font-weight: 700; color: var(--dim); }
.uf-value span { white-space: nowrap; font-size: 1.15rem; }
.uf-value { font-family: 'SupFix', 'Noto Sans KR', sans-serif; font-weight: 800; color: var(--ink); font-size: 1rem; margin-bottom: 6px; }
.uf-stage { border: 3px solid #9DB98F; background: #F4F7E9; color: #7C8F78; text-align: center; padding: 5px 6px; font-family: 'Galmuri11', sans-serif; font-weight: 700; }
.uf-stage small { display: block; font-family: 'SupFix', 'Noto Sans KR', sans-serif; font-weight: 500; font-size: 0.82rem; margin-top: 2px; }
.uf-stage.on { border-color: var(--ink); background: var(--lime); color: var(--ink); }
.uf-stage.on.zero { border-color: var(--red); background: #FBE7DF; color: var(--red); }
.uf-arrow { font-weight: 800; color: var(--ink); }
.uf-precision { display: flex; flex-wrap: wrap; gap: 2px; margin: 4px 0 2px; }
.uf-precision i { width: 9px; height: 16px; border: 2px solid var(--ink); background: var(--lime); }
.uf-precision i.off { background: transparent; border-color: #B9C5AA; }
.uf-precision-label { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: 0.95rem; margin-top: 4px; }
</style>
"""


def show_underflow_stage(value, exponent, precision):
    """지금 값이 '정상 수 → 비정규 수 → 0' 중 어디인지 칸으로 켜 주고, 남은 유효 비트를 53칸 막대로 보여 준다."""
    stage = "zero" if value == 0 else ("subnormal" if exponent == 0 else "normal")
    on = lambda name: " on" if stage == name else ""                 # 지금 단계에만 'on' 이름표를 붙인다
    blocks = "".join('<i></i>' if index < precision else '<i class="off"></i>' for index in range(53))
    render_html(UNDERFLOW_STYLE + f"""
        <div class="uf-value"><small>지금 값</small><span>{escape(readable_number(format(value, '.4e')))}</span></div>
        <div class="uf-stages">
            <div class="uf-stage{on('normal')}">① 정상 수<small>53비트 정밀도 그대로</small></div><div class="uf-arrow">▼</div>
            <div class="uf-stage{on('subnormal')}">② 비정규 수<small>지수 칸이 바닥, 정밀도가 줄어듦</small></div><div class="uf-arrow">▼</div>
            <div class="uf-stage zero{on('zero')}">③ 0이 되어 사라짐<small>더 담을 칸이 없음</small></div>
        </div>
        <div class="uf-precision-label">남은 유효 비트 {precision}칸 / 53칸</div>
        <div class="uf-precision">{blocks}</div>
    """)


def run_float_underflow_lab():
    """아주 작은 수를 계속 반으로 나누며 정상 수 → 비정규 수 → 0이 되는 과정을 비트로 확인한다."""
    lab_title("아주 작은 수를 계속 반으로 나누면?",
              f"{readable_number(UNDERFLOW_START)}을(를) 2로 계속 나눠요. 슬라이더로 나눈 횟수를 바꾸며 지수 칸(파랑)과 가수 칸(라임)을 보세요.")
    values = halving_steps(UNDERFLOW_START)
    first_subnormal = next(i for i, v in enumerate(values) if float_parts(v)[0] == 0)   # 처음으로 지수 칸이 모두 0이 된 횟수
    count = st.slider("2로 나눈 횟수", 0, len(values) - 1, first_subnormal - 1, key="uf_count")
    value = values[count]
    exponent, mantissa, _ = float_parts(value)          # _ = 상태 이름 (여기서는 단계 칸으로 보여 줘서 쓰지 않는다)

    # 정상 수는 가수 52칸 + 숨은 1칸 = 53비트의 유효숫자, 비정규 수는 가수 칸에서 실제로 쓰는 비트만 남는다
    precision = 53 if exponent else mantissa.bit_length()
    # 슬라이더 바로 아래에 '64비트 그림(왼쪽) + 지금 단계(오른쪽)'를 나란히 놓아 한 화면에서 함께 보이게 한다
    bits_column, stage_column = st.columns([2.6, 1], vertical_alignment="top")
    with bits_column:
        show_float_bits(value, f"{count}번 나눈 값의 64비트 · 지수 칸 값 {exponent}")
    with stage_column:
        show_underflow_stage(value, exponent, precision)
    st.caption("읽는 법: 10⁻³⁰⁸은 '10의 -308제곱'이에요. 소수점 아래로 0이 307개 이어진 뒤에야 1이 나오는, 아주 작은 수예요. "
               "지수 칸 값이 0이 되면 더 작은 지수를 나타낼 수 없어요.")

    st.code(f"{first_subnormal - 1:>3}번 : 마지막 정상 수   {readable_number(repr(values[first_subnormal - 1]), in_code=True)}\n"
            f"{first_subnormal:>3}번 : 첫 비정규 수     {readable_number(repr(values[first_subnormal]), in_code=True)}\n"
            f"{len(values) - 2:>3}번 : 가장 작은 수     {readable_number(repr(values[-2]), in_code=True)}\n"
            f"{len(values) - 1:>3}번 : 0이 되어 사라짐  {readable_number(repr(values[-1]), in_code=True)}")
    if value == 0.0:
        result_box("diff", "더 작은 수를 담을 칸이 없어서 값이 0이 되어 사라졌어요! (부동소수점 언더플로)")
    elif exponent == 0:
        result_box("diff", "지수 칸이 바닥(모두 0)이라 가수 칸의 앞자리를 0으로 채우며 버티고 있어요. 유효 비트가 줄어드는 중이에요.")
    else:
        result_box("same", "아직 정상 수라 53비트의 정밀도를 그대로 가지고 있어요. 슬라이더를 오른쪽으로 움직여 보세요.")
    result_box("note", "같은 '언더플로'라도 정수는 가장 작은 수 아래로 넘쳐서 가장 큰 수로 '넘어가고', "
                       "실수는 0에 너무 가까워져서 '사라져요'. 실험 ①의 '최솟값 − 1'과 비교해 보세요.")


# ----- 실제 실행 순서 -----
# 고른 실험에 맞는 함수를 실행하기 위한 표 (딕셔너리: 이름표 → 함수)
lab_functions = {
    "int_overflow": run_int_overflow_lab,
    "y2038": run_y2038_lab,
    "float_error": run_float_error_lab,
    "float_underflow": run_float_underflow_lab,
}

with crt_frame("pages/laboratory.py", "LAB"):
    page_banner("science", "PHENOMENON LAB", "현상 실험실", "원인 해부실에서 읽은 원리를 직접 계산해서 확인합니다.")
    render_html(BIT_STYLE)
    show_lab_selector()                                    # 1) 실험 4개 중 고르기
    selected_lab = st.session_state["lab_topic"]
    with st.container(border=True):                        # 2) 실험 내용을 테두리 상자(실험대) 안에 담는다
        lab_functions[selected_lab]()
    show_case_link(selected_lab)                           # 3) 실험이 끝나면 관련 사례의 원인 설명으로
