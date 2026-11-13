# =============================================================
# pages/laboratory.py  (현상 실험실)
# 원인 해부실에서 설명한 원리를 직접 계산해서 확인(검증)하는 페이지
# 실험 4가지: 정수 오버플로·언더플로 → 2038년 시계 → 0.1 + 0.2 (IEEE 754 비트) → 실수 언더플로
# =============================================================

import struct                                         # 실수를 컴퓨터가 저장하는 바이트 그대로 꺼내는 모듈
from datetime import datetime, timedelta, timezone    # 날짜+시각, 시간 간격, 시간대 (2038년 실험에서 사용)
from decimal import Decimal                           # 10진수를 정확하게 계산하는 자료형
from html import escape                               # 글자 속 <, > 같은 기호를 안전하게 바꿔 주는 함수

import streamlit as st

from common import crt_frame, open_case, page_banner, render_html

# 결과 상자 종류: 종류 이름 → (상자 색 이름, 앞에 붙는 제목)
RESULT_STYLES = {
    "diff": ("bt-err", "🔎 RESULT · 오류 현상이 재현됐어요"),   # 컴퓨터가 예상과 다르게 동작함 (실험 성공!)
    "same": ("bt-ok", "✅ RESULT · 결과가 같아요"),              # 이번 값에서는 차이가 없음
    "note": ("bt-key", "💡 NOTE · 핵심"),                        # 정리 문장
    "input": ("bt-obs", "⌨️ INPUT · 입력을 확인해 주세요"),       # 입력이 비었거나 잘못됨
}

# 실험 목록: "실험 이름표": (화면에 보일 이름, 관련 사례 번호)
LABS = {
    "int_overflow": ("① 정수 오버플로·언더플로", 1),
    "y2038": ("② 2038년 시계", 1),
    "float_error": ("③ 0.1 + 0.2와 IEEE 754", 2),
    "float_underflow": ("④ 실수 언더플로", 2),
}

INT_BITS = 32                                             # 정수 실험에 쓰는 칸 수 (32비트)
INT_MAX = (1 << (INT_BITS - 1)) - 1                       # 32비트 부호 있는 정수의 최댓값  2,147,483,647
INT_MIN = -(1 << (INT_BITS - 1))                          # 32비트 부호 있는 정수의 최솟값 -2,147,483,648
UNIX_START = datetime(1970, 1, 1, tzinfo=timezone.utc)    # 유닉스 시간의 출발점 (1970-01-01 00:00:00 UTC)

# 실수 64비트를 색으로 나눠 보여 주는 디자인 (정수 비트 칸 .bits는 common.py에 있다)
#   .s = 부호 칸(빨강) / .e = 지수 칸(파랑) / .m = 가수 칸(라임) / .gap = 부분 사이 틈
BIT_STYLE = """
<style>
.fbits { display: flex; flex-wrap: wrap; gap: 2px; margin: 4px 0 6px; }
.fbits span { width: 15px; height: 24px; line-height: 20px; text-align: center; font-size: 0.8rem; border: 2px solid var(--ink);
              font-family: 'Galmuri11', monospace; font-weight: 700; }
.fbits .s { background: #F6D5CF; color: var(--red); border-color: var(--red); }
.fbits .e { background: #D6E8F7; color: var(--sky); border-color: var(--sky); }
.fbits .m { background: var(--lime-soft); color: var(--ink); }
.fbits .gap { width: 6px; border: none; }
.flegend { display: flex; flex-wrap: wrap; gap: 14px; font-size: 0.9rem; margin-bottom: 4px; }
.flegend b { padding: 0 6px; border: 2px solid var(--ink); }
.flegend .s { background: #F6D5CF; } .flegend .e { background: #D6E8F7; } .flegend .m { background: var(--lime-soft); }
.lab-guide { font-size: 0.95rem; color: var(--dim); margin: 2px 0 6px; }
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
    render_html(f'<div class="bits-label">{escape(label)}</div><div class="bits">{groups}</div>')


def show_negative_steps(positive):
    """양수 → 음수를 2의 보수로 만드는 과정: ① 원래 수 → ② 모든 칸 뒤집기(~) → ③ 1 더하기"""
    flipped = ~positive                              # ~ (NOT) : 0은 1로, 1은 0으로 모든 칸을 뒤집는다
    st.code(f"① 원래 수 {positive:>13,} : {bit_string(positive, INT_BITS)}\n"
            f"② 모든 칸 뒤집기(~)     : {bit_string(flipped, INT_BITS)}\n"
            f"③ 1 더하기              : {bit_string(flipped + 1, INT_BITS)}  = {-positive:,}")


# -------------------------------------------------------------
# 2. 실험 ① 정수 오버플로·언더플로 (BUG-001)
# -------------------------------------------------------------

def set_int_example(start, operator):
    """'최댓값 + 1', '최솟값 − 1' 버튼을 누르면 입력칸 값을 예시로 바꾼다. (on_click에서 실행)"""
    st.session_state["int_start"] = start
    st.session_state["int_operator"] = operator
    st.session_state["int_amount"] = 1


def show_int_examples():
    """입력칸을 예시 값으로 한 번에 채우는 버튼 2개"""
    over_column, under_column = st.columns(2)
    over_column.button("예시: 최댓값 + 1 (오버플로)", key="int_ex_over", width="stretch",
                       on_click=set_int_example, args=(INT_MAX, "+"))
    under_column.button("예시: 최솟값 − 1 (언더플로)", key="int_ex_under", width="stretch",
                        on_click=set_int_example, args=(INT_MIN, "−"))


def show_int_result(start, operator, amount):
    """수학 계산 결과와 32비트 정수에 담은 결과를 비트와 함께 비교한다."""
    real_result = start + amount if operator == "+" else start - amount   # 수학 계산 (Python 정수는 칸 제한이 없다)
    stored_result = to_signed(real_result, INT_BITS)                      # 32비트 칸에 담았을 때의 값
    show_bits(to_signed(start, INT_BITS), INT_BITS, f"계산 전: {to_signed(start, INT_BITS):,}")
    show_bits(stored_result, INT_BITS, f"계산 후 32비트에 저장된 값: {stored_result:,}")
    st.code(f"수학 계산     : {start:,} {operator} {amount:,} = {real_result:,}\n"
            f"32비트 저장값 : {stored_result:,}")

    if real_result > INT_MAX:          # 위쪽 끝을 넘음 → 오버플로
        result_box("diff", f"최댓값 {INT_MAX:,}을 넘어서 음수 {stored_result:,}(으)로 넘어갔어요! (정수 오버플로) "
                           "받아올림이 맨 앞 칸(부호 비트)까지 올라가 1이 됐어요.")
    elif real_result < INT_MIN:        # 아래쪽 끝을 넘음 → 정수 언더플로
        result_box("diff", f"최솟값 {INT_MIN:,}보다 작아져서 양수 {stored_result:,}(으)로 넘어갔어요! (정수 언더플로) "
                           "빌림 때문에 맨 앞 칸(부호 비트)이 0이 됐어요.")
    else:
        result_box("same", "32비트 범위 안이라 수학 계산과 같아요. 위의 예시 버튼을 눌러 보세요.")

    # 결과가 음수라면, 그 음수가 2의 보수로 어떻게 만들어졌는지 단계별로 보여 준다.
    if stored_result == INT_MIN:
        result_box("note", f"{INT_MIN:,}은 32비트에서 가장 작은 수예요. 짝이 되는 +2,147,483,648은 32비트에 담을 수 없어서 "
                           "'1 다음에 0이 31개'인 특별한 모양이에요. (음수 쪽이 하나 더 많은 이유)")
    elif stored_result < 0:
        st.markdown("**이 음수는 이렇게 만들어져요 (2의 보수: 뒤집고 1 더하기)**")
        show_negative_steps(-stored_result)


def run_int_overflow_lab():
    """32비트 정수에 더하거나 빼 보며 오버플로·언더플로와 2의 보수를 확인한다."""
    lab_title("가장 큰 수에 1을 더하면? 가장 작은 수에서 1을 빼면?",
              "가정: 부호 있는 32비트 정수에서, 칸 밖으로 넘친 비트를 그냥 버리는 경우 (C·Java의 int와 같은 방식)")
    # 처음 들어왔을 때의 입력값 (예시 버튼이 session_state로 값을 바꾸므로, 입력칸에는 value=를 따로 주지 않는다)
    st.session_state.setdefault("int_start", INT_MAX)
    st.session_state.setdefault("int_operator", "+")
    st.session_state.setdefault("int_amount", 1)
    show_int_examples()
    start_column, operator_column, amount_column = st.columns([2.2, 1, 1.2], vertical_alignment="bottom")
    # min/max: 32비트 범위 안의 수만 입력할 수 있게 막는다
    start = start_column.number_input("32비트 정수", min_value=INT_MIN, max_value=INT_MAX, step=1, key="int_start")
    operator = operator_column.selectbox("계산", ["+", "−"], key="int_operator")
    amount = amount_column.number_input("얼마나", min_value=0, max_value=INT_MAX, step=1, key="int_amount")
    show_int_result(int(start), operator, int(amount))


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
    "2038-01-19 03:14:07 UTC (부호 있는 32비트의 끝)": (1 << 31) - 1,
    "2106-02-07 06:28:15 UTC (부호 없는 32비트의 끝)": (1 << 32) - 1,
}


def seconds_to_text(seconds):
    """유닉스 시간(초)을 날짜·시각 글자로 바꾼다. 날짜로 나타낼 수 없을 만큼 크면 안내 글자를 돌려준다."""
    try:
        # timedelta(seconds=초): 출발점에 초를 더해서 날짜·시각을 계산한다 (음수면 과거로 간다)
        return f"{UNIX_START + timedelta(seconds=seconds):%Y-%m-%d %H:%M:%S} UTC"
    except OverflowError:
        return "(아주 먼 미래)"


def run_y2038_lab():
    """같은 초를 세 종류의 시계(32비트 부호 있음·없음, 64비트)에 담아 날짜가 어떻게 읽히는지 비교한다."""
    lab_title("1초가 지나면 시계는 몇 년을 가리킬까?",
              "유닉스 시간(1970-01-01 0시부터 센 초)을 서로 다른 칸에 담고, 경계 순간 앞뒤로 1초씩 움직여 보세요.")
    moment_name = st.radio("살펴볼 순간", list(MOMENTS.keys()), key="y2038_moment", horizontal=True)
    offset = st.slider("그 순간에서 몇 초 지났나요?", -3, 3, 0, key="y2038_offset")
    seconds = MOMENTS[moment_name] + offset              # 실제로 흐른 초

    st.markdown(f"**실제로 흐른 시간: {seconds:,}초 → {seconds_to_text(seconds)}**")
    lines = []
    broken = []                                          # 날짜가 틀어진 시계 이름 모음
    for clock_name, store in CLOCK_TYPES.items():
        stored = store(seconds)                          # 이 시계에 실제로 담기는 값
        mark = "✅" if stored == seconds else "❌"
        if stored != seconds:
            broken.append(clock_name)
        lines.append(f"{mark} {clock_name:<18} : {stored:>15,}초 → {seconds_to_text(stored)}")
    st.code("\n".join(lines))
    show_bits(to_signed(seconds, 32), 32, "32비트 칸에 담긴 비트 (빨간 테두리 = 부호 비트)")

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
        kind = "s" if position == 0 else ("e" if position <= 11 else "m")
        if position in (1, 12):                      # 부분이 바뀌는 곳에 작은 틈
            cells += '<span class="gap"></span>'
        cells += f'<span class="{kind}">{bit}</span>'
    render_html(f"""
        <div class="bits-label">{escape(label)}</div>
        <div class="flegend"><span><b class="s">부호 1칸</b> 0=양수</span><span><b class="e">지수 11칸</b> 2의 몇 제곱인지</span>
        <span><b class="m">가수 52칸</b> 유효숫자</span></div>
        <div class="fbits">{cells}</div>
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
    except (ValueError, ArithmeticError):
        result_box("input", "계산할 수 있는 숫자를 입력해 주세요. 예) 0.1")
        return

    # !r (repr): 숫자를 줄이지 않고 컴퓨터가 가진 값 그대로 보여 준다.
    st.code(f"컴퓨터 계산 (float)   : {first_text} + {second_text} = {computer_result!r}\n"
            f"정확한 계산 (Decimal) : {first_text} + {second_text} = {exact_result}")
    if computer_result == float(exact_result):
        result_box("same", "이번에는 두 결과가 같아요. 2진수로 딱 떨어지거나 오차가 반올림으로 사라진 경우예요. (예: 0.5 + 0.25)")
    else:
        result_box("diff", f"두 결과가 달라요! 컴퓨터 계산 결과({computer_result!r})는 정확한 값({exact_result})과 다른 수예요.")

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
    st.caption(f"0.1을 {repeat_count}번 더한 결과: {total!r} (정확한 값: {Decimal(repeat_count) / Decimal(10)})")


def draw_line_chart(values):
    """값 목록을 꺾은선 그래프(SVG 그림)로 직접 그린다. 가로축 = 더한 횟수, 세로축 = 오차"""
    width, height, margin = 1000, 220, 30         # 그림 크기와 안쪽 여백(px). 가로로 넓게 → 글자가 지나치게 커지지 않는다
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
            <text x="{margin + 4}" y="{margin - 8}" font-size="13" fill="#1F4D25">최대 오차 {largest:.1e}</text>
            <text x="{margin}" y="{height - 8}" font-size="13" fill="#1F4D25">1번</text>
            <text x="{width - margin}" y="{height - 8}" font-size="13" fill="#1F4D25" text-anchor="end">{len(values)}번 더함</text>
        </svg>
    """)


def run_float_error_lab():
    """두 소수를 더해서 컴퓨터 계산 결과와 정확한 값을 비교하고, 저장된 비트와 쌓이는 오차를 보여 준다."""
    lab_title("0.1 + 0.2는 정말 0.3일까?", "두 수를 바꿔 넣어 보세요. 0.5 + 0.25처럼 2진수로 딱 떨어지는 수는 오차가 없어요.")
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


def run_float_underflow_lab():
    """아주 작은 수를 계속 반으로 나누며 정상 수 → 비정규 수 → 0이 되는 과정을 비트로 확인한다."""
    lab_title("아주 작은 수를 계속 반으로 나누면?",
              f"{UNDERFLOW_START}을(를) 2로 계속 나눠요. 슬라이더로 나눈 횟수를 바꾸며 지수 칸(파랑)과 가수 칸(라임)을 보세요.")
    values = halving_steps(UNDERFLOW_START)
    first_subnormal = next(i for i, v in enumerate(values) if float_parts(v)[0] == 0)   # 처음으로 지수 칸이 모두 0이 된 횟수
    count = st.slider("2로 나눈 횟수", 0, len(values) - 1, first_subnormal - 1, key="uf_count")
    value = values[count]
    exponent, mantissa, state = float_parts(value)

    # 정상 수는 가수 52칸 + 숨은 1칸 = 53비트의 유효숫자, 비정규 수는 가수 칸에서 실제로 쓰는 비트만 남는다
    precision = 53 if exponent else mantissa.bit_length()
    st.code(f"{count}번 나눔 → 값 = {value!r}\n"
            f"상태          : {state}\n"
            f"지수 칸 값    : {exponent}  (0이 되면 더 작은 지수를 나타낼 수 없음)\n"
            f"남은 유효 비트 : {precision} / 53")
    show_float_bits(value, f"{count}번 나눈 값의 64비트")

    st.code(f"{first_subnormal - 1:>3}번 : 마지막 정상 수   {values[first_subnormal - 1]!r}\n"
            f"{first_subnormal:>3}번 : 첫 비정규 수     {values[first_subnormal]!r}\n"
            f"{len(values) - 2:>3}번 : 가장 작은 수     {values[-2]!r}\n"
            f"{len(values) - 1:>3}번 : 0이 되어 사라짐  {values[-1]!r}")
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
