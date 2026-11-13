# =============================================================
# pages/laboratory.py  (현상 실험실)
# 원인 해부실에서 설명한 원리를 실제 계산 결과로 확인(검증)하는 페이지
# 실험 6가지 (탐구 순서): 정수 오버플로 → 부동소수점 → 문자 인코딩 → 유니코드 정규화 → 한글 조합, 그리고 오류 검출(패리티·체크섬)
# =============================================================

import unicodedata                               # 유니코드 정규화(NFC, NFD) 기능
from datetime import datetime, timedelta, timezone   # 날짜+시각, 시간 간격, 시간대 (2038년 시뮬레이터에서 사용)
from decimal import Decimal                      # 10진수를 정확하게 계산하는 자료형

from html import escape                          # 글자 속 <, > 같은 기호를 안전하게 바꿔 주는 함수

import pandas as pd                              # 표 형태의 데이터를 다루는 라이브러리 (유니코드 표)
import streamlit as st

from common import crt_frame, open_case, page_banner, render_html

# 결과 상자 종류: 종류 이름 → (상자 색 이름, 앞에 붙는 제목)
RESULT_STYLES = {
    "diff": ("bt-err", "🔎 RESULT · 오류 현상이 재현됐어요"),   # 컴퓨터가 예상과 다르게 동작함 (실험 성공!)
    "same": ("bt-ok", "✅ RESULT · 결과가 같아요"),              # 이번 값에서는 차이가 없음
    "note": ("bt-key", "💡 NOTE · 핵심"),                        # 정리 문장
    "input": ("bt-obs", "⌨️ INPUT · 입력을 확인해 주세요"),       # 입력이 비었거나 잘못됨
}

# 실험 목록: "실험 이름표": ("화면에 보일 이름", 관련 오류 번호) — 특정 사례에 딸리지 않은 실험은 번호가 None
LABS = {
    "overflow": ("2의 보수와 정수 오버플로 (2038년 문제)", 1),
    "float": ("0.1 + 0.2 계산하기", 2),
    "encoding": ("글자를 바이트로 바꾸기", 3),
    "unicode": ("한글 쪼개 보기 (NFC / NFD)", 4),
    "hangul": ("한글 조합 공식과 '완완성' 재현", 5),
    "parity": ("오류 검출: 패리티 비트와 XOR 체크섬", None),
}


# -------------------------------------------------------------
# 0. 공통 함수
# -------------------------------------------------------------

def restore_lab():
    """원인 해부실에서 고른 실험이 있으면 그 실험을 먼저 보여 준다."""
    if "lab_topic" not in st.session_state:
        st.session_state["lab_topic"] = st.session_state.get("saved_lab", "overflow")


def save_lab():
    """고른 실험을 저장해서 다른 페이지에 다녀와도 유지한다."""
    st.session_state["saved_lab"] = st.session_state["lab_topic"]


def lab_label(lab):
    """선택 상자에 보여 줄 실험 이름. 관련 사례가 있으면 (BUG-002)처럼 번호를 붙인다."""
    name, case_id = LABS[lab]
    if case_id is None:
        return f"🧪 {name}"
    return f"🧪 {name}  (BUG-{case_id:03d})"


def show_lab_selector():
    """실험을 고르는 선택 상자를 보여 준다."""
    restore_lab()
    st.selectbox(
        "실험 선택",
        list(LABS.keys()),
        key="lab_topic",
        format_func=lab_label,                    # 화면용 이름 + 관련 오류 번호
        on_change=save_lab,
        label_visibility="collapsed",
    )


def run_button(key):
    """모든 실험에서 함께 쓰는 '실험 실행하기' 버튼. 누르면 True를 돌려준다."""
    # icon: 재생(▶) 아이콘, type="primary": 라임색 버튼, width="stretch": 칸 너비만큼 넓게
    return st.button("실험 실행하기", key=key, type="primary", icon=":material/play_arrow:", width="stretch")


def show_case_link(lab):
    """실험과 관련된 오류의 원인 해부실로 가는 버튼"""
    case_id = LABS[lab][1]
    if case_id is None:          # 특정 사례에 딸리지 않은 실험은 버튼 대신 안내만 보여 준다
        st.caption("오류의 '원인'이 아니라, 컴퓨터가 오류를 '찾아내는' 원리를 확인하는 실험이에요.")
        return
    if st.button(f"BUG-{case_id:03d} 원인 보기", key=f"lab_link_{lab}", icon=":material/menu_book:", width="stretch"):
        open_case(case_id)


def result_box(kind, text):
    """실험 결과를 앱 디자인에 맞는 상자로 보여 준다. (빨간 '오류' 경고창처럼 보이지 않게)"""
    box_class, label = RESULT_STYLES[kind]
    render_html(f"""
        <div class="bt-box {box_class}">
            <div class="bt-box-label">{label}</div>
            <div>{escape(text)}</div>
        </div>
    """)


def to_hex(data):
    """바이트를 사람이 읽기 쉬운 16진수 문자열로 바꾼다. 예) b'\\xed\\x95\\x9c' → 'ED 95 9C'"""
    return " ".join(f"{byte:02X}" for byte in data)


# -------------------------------------------------------------
# 2. 부동소수점 실험 (BUG-002)
# -------------------------------------------------------------

# 실험 화면은 입력 → 실행 → 결과 → 반복 오차 그래프 순서로 구성한다.
# Streamlit은 위젯을 조작할 때 파일을 다시 실행하므로 마지막 입력값은 session_state에 보관한다.

def run_float_lab():
    """두 소수를 더해서 컴퓨터 계산 결과와 정확한 값을 비교한다."""
    st.markdown("#### 🧪 0.1 + 0.2는 정말 0.3일까?")

    # 입력은 같은 높이의 두 칸, 실행 버튼은 그 아래 전체 너비에 배치한다.
    first_column, second_column = st.columns(2, gap="medium")
    with first_column:
        first_text = st.text_input("첫 번째 수", "0.1", key="float_first")
    with second_column:
        second_text = st.text_input("두 번째 수", "0.2", key="float_second")

    if run_button("float_run"):
        # 슬라이더를 움직여 재실행되더라도 마지막으로 실행한 입력값을 유지한다.
        st.session_state["float_ran"] = True
        st.session_state["float_last_inputs"] = (first_text.strip(), second_text.strip())

    st.markdown("##### 계산 결과")
    if st.session_state.get("float_ran", False):
        saved_inputs = st.session_state.get("float_last_inputs")
        # 구버전 세션에서 float_ran만 저장된 경우도 정상적으로 표시한다.
        if saved_inputs is None:
            saved_inputs = (first_text.strip(), second_text.strip())
        show_float_result(*saved_inputs)
    else:
        show_waiting()

    st.divider()
    st.markdown("##### 반복 덧셈 오차 분석")
    # 그래프와 슬라이더를 같은 수직 영역에 묶고 전체 너비를 사용한다.
    show_float_error_chart()


def show_waiting():
    """아직 실행하기 전: 결과가 나올 자리에 안내 상자를 보여 준다."""
    render_html("""
        <div class="lab-waiting">
            <div class="lab-waiting-icon">▶</div>
            <div>위의 <b>실험 실행하기</b>를 누르면<br>컴퓨터 계산 결과와 실제로 저장된 값이 여기에 나와요.</div>
        </div>
    """)


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

    # 두 결과가 같은지 비교
    if computer_result == float(exact_result):
        result_box("same", "이번에는 두 결과가 같아요. 2진수로 딱 떨어지거나 오차가 반올림으로 사라진 경우예요.")
    else:
        result_box("diff", f"두 결과가 달라요! 컴퓨터 계산 결과({computer_result!r})는 정확한 값({exact_result})과 다른 수예요.")

    # Decimal(float값): 컴퓨터 안에 '실제로' 저장된 값을 끝까지 보여 준다.
    st.markdown("**컴퓨터 안에 실제로 저장된 값**")
    st.code(f"{first_text} → {Decimal(first_number)}\n"
            f"{second_text} → {Decimal(second_number)}")


def show_float_error_chart():
    """0.1을 여러 번 더할수록 오차가 어떻게 쌓이는지 그래프로 보여 준다."""
    repeat_count = st.slider("📈 0.1을 계속 더하면 오차는? (더하는 횟수)", 10, 1000, 100, step=10)

    total = 0.0
    errors = []
    for count in range(1, repeat_count + 1):
        total += 0.1                                   # 컴퓨터 방식으로 0.1을 더한다
        exact = Decimal(count) / Decimal(10)           # 정확한 값 (count × 0.1)
        error = abs(Decimal(total) - exact)            # 둘의 차이 = 오차
        errors.append(float(error))

    draw_line_chart(errors)
    st.caption(f"0.1을 {repeat_count}번 더한 결과: {total!r} (정확한 값: {Decimal(repeat_count) / Decimal(10)})")


def draw_line_chart(values):
    """값 목록을 꺾은선 그래프(SVG 그림)로 직접 그린다. 가로축 = 더한 횟수, 세로축 = 오차"""
    width, height, margin = 600, 220, 30          # 그림 크기와 안쪽 여백(px)
    largest = max(values) or 1                    # 가장 큰 오차 (0이면 나눗셈을 못 하니 1로)
    last_index = len(values) - 1

    # 각 값을 그림 위의 (x, y) 좌표로 바꾼다.
    #   x: 왼쪽 여백에서 시작해 오른쪽 끝까지 고르게 나눈다.
    #   y: 값이 클수록 위로 (SVG는 위쪽이 0이라서 높이에서 빼 준다).
    points = []
    for index, value in enumerate(values):
        x = margin + index / last_index * (width - 2 * margin)
        y = height - margin - value / largest * (height - 2 * margin)
        points.append(f"{x:.1f},{y:.1f}")

    # 가로 눈금선 4개 (0%, 33%, 66%, 100% 높이)
    grid = ""
    for step in range(4):
        y = margin + step * (height - 2 * margin) / 3
        grid += f'<line x1="{margin}" y1="{y:.1f}" x2="{width - margin}" y2="{y:.1f}" stroke="#C9D9A6" stroke-width="1"/>'

    # polyline: 점들을 순서대로 이은 꺾은선
    render_html(f"""
        <svg class="lab-chart" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
            {grid}
            <line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#1F4D25" stroke-width="3"/>
            <line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#1F4D25" stroke-width="3"/>
            <polyline points="{' '.join(points)}" fill="none" stroke="#A23A2E" stroke-width="3" stroke-linejoin="bevel"/>
            <text x="{margin + 4}" y="{margin - 8}" font-size="13" fill="#1F4D25">최대 오차 {largest:.1e}</text>
            <text x="{margin}" y="{height - 8}" font-size="13" fill="#1F4D25">1번</text>
            <text x="{width - margin}" y="{height - 8}" font-size="13" fill="#1F4D25" text-anchor="end">{len(values)}번 더함</text>
        </svg>
    """)


# -------------------------------------------------------------
# 4. 유니코드 정규화 실험 (BUG-004)
# -------------------------------------------------------------

def make_code_table(text):
    """글자 하나하나와 유니코드 번호를 표로 만든다."""
    rows = []
    for order, character in enumerate(text, start=1):
        # ord(): 글자의 유니코드 번호(정수) → 16진수로 표시 (예: U+D55C)
        rows.append({"순서": order, "글자": character, "유니코드 번호": f"U+{ord(character):04X}"})
    return pd.DataFrame(rows)


def run_unicode_lab():
    """같은 글자를 NFC(완성형)와 NFD(조합형)로 바꿔서 비교한다."""
    st.markdown("#### 🧪 똑같이 보이는데 왜 다른 글자일까?")
    input_text = st.text_input("한글을 입력하세요", "한글", key="unicode_input")

    if run_button("unicode_run"):
        if not input_text:
            result_box("input", "글자를 입력해 주세요.")
            return

        nfc_text = unicodedata.normalize("NFC", input_text)   # 완성형: '한' = 1개
        nfd_text = unicodedata.normalize("NFD", input_text)   # 조합형: 'ㅎ'+'ㅏ'+'ㄴ' = 3개

        nfc_column, nfd_column = st.columns(2)
        with nfc_column:
            st.markdown(f"**NFC (완성형: 글자 단위)** · 글자 수 {len(nfc_text)}")
            st.dataframe(make_code_table(nfc_text), hide_index=True, width="stretch")
        with nfd_column:
            st.markdown(f"**NFD (조합형: 자음·모음 조각 단위)** · 글자 수 {len(nfd_text)}")
            st.dataframe(make_code_table(nfd_text), hide_index=True, width="stretch")

        # == 로 비교하면 컴퓨터가 두 글자를 같은 글자로 보는지 알 수 있다.
        if nfc_text == nfd_text:
            result_box("same", "두 방식의 결과가 같아요. 한글이 아닌 글자는 쪼개지지 않을 수 있어요.")
        else:
            result_box("diff", f"화면에는 똑같이 '{input_text}'로 보이지만, 컴퓨터는 두 글자를 다른 글자로 판단해요. (NFC == NFD → False)")


# -------------------------------------------------------------
# 3. 문자 인코딩 실험 (BUG-003)
# -------------------------------------------------------------

def run_encoding_lab():
    """글자를 UTF-8과 CP949 바이트로 바꾸고, 다른 규칙으로 잘못 읽어 본다."""
    st.markdown("#### 🧪 글자는 왜 �로 깨질까?")
    input_text = st.text_input("글자를 입력하세요", "한글", key="encoding_input")

    if run_button("encoding_run"):
        if not input_text:
            result_box("input", "글자를 입력해 주세요.")
            return

        # encode(): 글자 → 바이트(숫자). errors="replace"는 바꿀 수 없는 글자를 ?로 바꾼다.
        utf8_bytes = input_text.encode("utf-8")
        cp949_bytes = input_text.encode("cp949", errors="replace")

        st.markdown("**① 같은 글자, 다른 규칙 → 다른 숫자(바이트)**")
        st.code(f"UTF-8 ({len(utf8_bytes)}바이트) : {to_hex(utf8_bytes)}\n"
                f"CP949 ({len(cp949_bytes)}바이트) : {to_hex(cp949_bytes)}")

        # decode(): 바이트 → 글자. 저장한 규칙과 다른 규칙으로 읽으면 글자가 깨진다.
        st.markdown("**② 다른 규칙으로 잘못 읽으면?**")
        st.code(f"CP949로 저장 → UTF-8로 읽기   : {cp949_bytes.decode('utf-8', errors='replace')}\n"
                f"UTF-8로 저장 → CP949로 읽기   : {utf8_bytes.decode('cp949', errors='replace')}\n"
                f"UTF-8로 저장 → Latin-1로 읽기 : {utf8_bytes.decode('latin-1')}")

        st.markdown("**③ 같은 규칙으로 읽으면?**")
        st.code(f"UTF-8로 저장 → UTF-8로 읽기   : {utf8_bytes.decode('utf-8')}")
        result_box("note", "저장할 때와 읽을 때 같은 규칙(인코딩)을 써야 글자가 제대로 보여요.")


# -------------------------------------------------------------
# 1. 정수 오버플로 실험 (BUG-001): 2의 보수와 2038년 문제
# -------------------------------------------------------------

INT_BITS = 32                                         # 실험에 쓰는 정수 칸 수 (32비트)
UNIX_START = datetime(1970, 1, 1, tzinfo=timezone.utc)   # 시간 카운터의 출발점 (1970-01-01 00:00:00 UTC)

# 0과 1을 픽셀 칸으로 보여 주는 디자인. 맨 앞 칸(부호 비트)은 빨간 테두리로 표시한다.
BIT_STYLE = """
<style>
.bits-label { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); margin: 8px 0 4px; }
.bits { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 6px; }
.bits .byte { display: flex; gap: 2px; }
.bits span { width: 20px; height: 28px; line-height: 24px; text-align: center; border: 2px solid var(--ink);
             font-family: 'Galmuri11', monospace; font-weight: 700; color: var(--ink); }
.bits .one { background: var(--lime); }
.bits .zero { background: var(--paper); }
.bits .sign { outline: 3px solid var(--red); outline-offset: 1px; }
</style>
"""


def to_signed(value, bits):
    """정수를 bits칸짜리 '부호 있는 정수'에 담았을 때의 값으로 바꾼다. (2의 보수 규칙)"""
    mask = (1 << bits) - 1        # << : 1을 bits칸 왼쪽으로 민 뒤 1을 빼면 → 모든 칸이 1인 수 (32비트면 0xFFFFFFFF)
    value = value & mask          # & (AND) : 칸 밖으로 넘친 비트를 잘라 내고 bits칸만 남긴다
    if value >= 1 << (bits - 1):  # 맨 앞 칸(부호 비트)이 1이면
        value -= 1 << bits        # 음수로 읽는다 → 이것이 2의 보수 해석
    return value


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
    st.code(f"① {positive:>13,} : {bit_string(positive, INT_BITS)}\n"
            f"② 모든 칸 뒤집기(~)  : {bit_string(flipped, INT_BITS)}\n"
            f"③ 1 더하기           : {bit_string(flipped + 1, INT_BITS)}  = {-positive:,}")


def show_overflow_result(start_number, add_amount):
    """수학으로 더한 값과 32비트 정수에 담은 값을 비교한다."""
    real_sum = start_number + add_amount                 # 수학 계산 (Python 정수는 칸 제한이 없다)
    stored_sum = to_signed(real_sum, INT_BITS)           # 32비트 칸에 담았을 때의 값
    show_bits(to_signed(start_number, INT_BITS), INT_BITS, f"더하기 전: {to_signed(start_number, INT_BITS):,}")
    show_bits(stored_sum, INT_BITS, f"더한 뒤 32비트에 저장된 값: {stored_sum:,}")
    st.code(f"수학 계산     : {start_number:,} + {add_amount:,} = {real_sum:,}\n"
            f"32비트 저장값 : {stored_sum:,}")
    if real_sum != stored_sum:
        result_box("diff", f"32비트 범위를 넘어서 {stored_sum:,}(으)로 넘어갔어요! 맨 앞 칸(부호 비트)이 바뀌었는지 보세요.")
    else:
        result_box("same", "32비트 범위 안이라 수학 계산과 같아요. 2147483647에 1을 더해 보세요.")
    # 결과가 음수라면, 그 음수가 2의 보수로 어떻게 만들어졌는지 단계별로 보여 준다.
    smallest = -(1 << (INT_BITS - 1))                    # 32비트에서 가장 작은 수: -2,147,483,648
    if stored_sum == smallest:
        result_box("note", "-2,147,483,648은 32비트에서 가장 작은 수예요. 짝이 되는 +2,147,483,648은 32비트에 담을 수 없어서, "
                           "1 다음에 0이 31개인 특별한 모양이에요. (양수 쪽보다 음수 쪽이 하나 더 많은 이유)")
    elif stored_sum < 0:
        st.markdown("**이 음수는 이렇게 만들어져요 (2의 보수)**")
        show_negative_steps(-stored_sum)


def show_y2038_simulator():
    """1970년부터 센 '초'를 32비트 정수에 담으면, 2038년 1월 19일 03:14:07(UTC) 다음 순간 어떻게 되는지 보여 준다."""
    st.markdown("##### ⏰ 2038년 시뮬레이터")
    st.caption("많은 시스템은 시간을 1970-01-01 00:00:00(UTC)부터 흐른 '초'로 세요. 이 초 카운터가 32비트라면?")
    offset = st.slider("2038-01-19 03:14:07(UTC)에서 몇 초 지났나요?", -3, 3, 0, key="y2038_offset")
    seconds = (1 << (INT_BITS - 1)) - 1 + offset         # 32비트 최댓값(2,147,483,647초)에서 offset초 이동
    stored = to_signed(seconds, INT_BITS)                # 32비트 카운터에 실제로 담기는 값
    # timedelta(seconds=초): 출발점에 초를 더해서 날짜·시각을 계산한다 (음수면 과거로 간다)
    real_time = UNIX_START + timedelta(seconds=seconds)
    stored_time = UNIX_START + timedelta(seconds=stored)
    show_bits(stored, INT_BITS, f"32비트 시간 카운터: {stored:,}초")
    st.code(f"실제로 흐른 시간    : {seconds:>14,}초 → {real_time:%Y-%m-%d %H:%M:%S} UTC\n"
            f"32비트로 읽은 시간  : {stored:>14,}초 → {stored_time:%Y-%m-%d %H:%M:%S} UTC")
    if stored != seconds:
        result_box("diff", "1초가 지나는 순간 카운터가 음수가 되어 날짜가 1901년으로 돌아갔어요!")
    else:
        result_box("same", "아직 32비트 범위 안이라 날짜가 정확해요. 슬라이더를 오른쪽으로 움직여 보세요.")


def run_overflow_lab():
    """32비트 정수에 수를 더해 보며 오버플로와 2의 보수를 확인하고, 2038년 문제를 시뮬레이션한다."""
    render_html(BIT_STYLE)
    st.markdown("#### 🧪 가장 큰 수에 1을 더하면?")
    number_column, add_column, run_column = st.columns([2, 1, 1.4], vertical_alignment="bottom")
    start_number = number_column.number_input("32비트 정수", value=2147483647, step=1, key="of_number")
    add_amount = add_column.number_input("더할 수", value=1, step=1, key="of_add")
    with run_column:
        if run_button("of_run"):
            st.session_state["of_ran"] = True            # 한 번 실행하면 결과를 계속 보여 준다
    if st.session_state.get("of_ran", False):
        show_overflow_result(int(start_number), int(add_amount))
    st.divider()
    show_y2038_simulator()


# -------------------------------------------------------------
# 5. 오류 검출 실험: 패리티 비트와 XOR 체크섬
#    (오류의 '원인'이 아니라, 컴퓨터가 데이터가 망가졌는지 '알아채는' 방법)
# -------------------------------------------------------------

# 뒤집힌 칸(빨강)과 패리티 칸(파랑)을 구분하는 디자인. 0과 1 칸 모양은 BIT_STYLE을 함께 쓴다.
PARITY_STYLE = """
<style>
.bits .flip { background: var(--red); color: #FFFFFF; }
.bits .par { background: #D6E8F7; border-color: var(--sky); color: var(--sky); margin-left: 6px; }
.byte-row { display: flex; align-items: center; gap: 10px; margin: 3px 0; }
.byte-name { width: 54px; font-family: 'Galmuri11', monospace; font-weight: 700; color: var(--ink); }
.byte-check { font-family: 'Galmuri11', sans-serif; font-weight: 700; }
</style>
"""


def parity_bit(byte):
    """짝수 패리티: 1의 개수가 홀수면 1, 짝수면 0 → 패리티까지 합친 1의 개수가 항상 짝수가 되게 만든다."""
    # bin(수) : 2진수 글자로 바꾼다. .count("1") : 그 안의 1의 개수. % 2 : 2로 나눈 나머지(0 또는 1)
    return bin(byte).count("1") % 2


def xor_checksum(data):
    """모든 바이트를 XOR(^)로 차례로 접어서 확인값 1바이트를 만든다."""
    checksum = 0
    for byte in data:
        checksum ^= byte          # ^ (XOR) : 두 칸이 다르면 1, 같으면 0
    return checksum


def flip_bit(data, position):
    """position번째 비트(1부터 셈)를 뒤집은 새 데이터를 돌려준다. 0이면 그대로 돌려준다."""
    if position == 0:
        return data
    byte_index = (position - 1) // 8              # 몇 번째 바이트인가
    bit_index = 7 - (position - 1) % 8            # 그 바이트의 몇 번째 칸인가 (왼쪽 칸부터 1번)
    changed = bytearray(data)                     # bytes는 고칠 수 없어서, 고칠 수 있는 bytearray로 복사
    changed[byte_index] ^= 1 << bit_index         # ^ 와 << 로 그 칸 하나만 뒤집는다 (0↔1)
    return bytes(changed)


def byte_row_html(name, byte, parity, flipped_bit=None, check=""):
    """바이트 하나를 '이름 + 8칸 + 패리티 칸 + 확인 결과' 한 줄로 그린다. 뒤집힌 칸은 빨간색."""
    text = format(byte, "08b")                    # 8칸짜리 2진수 글자
    cells = ""
    for index, bit in enumerate(text):
        kind = "flip" if index == flipped_bit else ("one" if bit == "1" else "zero")
        cells += f'<span class="{kind}">{bit}</span>'
    cells += f'<span class="par">{parity}</span>'
    return f'<div class="byte-row"><span class="byte-name">{escape(name)}</span><div class="bits"><div class="byte">{cells}</div></div><span class="byte-check">{check}</span></div>'


def show_transmission(data, received, position):
    """보낸 데이터와 받은 데이터를 바이트마다 나란히 보여 주고, 패리티로 오류를 찾는다."""
    flipped_byte = (position - 1) // 8 if position else None   # 뒤집힌 칸이 들어 있는 바이트 번호
    flipped_bit = (position - 1) % 8 if position else None     # 그 바이트 안에서 왼쪽부터 몇 번째 칸
    sent_rows, received_rows = "", ""
    error_count = 0
    for index, (sent_byte, got_byte) in enumerate(zip(data, received)):
        sent_parity = parity_bit(sent_byte)        # 보낼 때 붙인 패리티
        # 받는 쪽: 받은 바이트로 패리티를 다시 계산해서, 함께 온 패리티(sent_parity)와 비교한다
        ok = parity_bit(got_byte) == sent_parity
        error_count += 0 if ok else 1
        check = "✅ 일치" if ok else "❌ 패리티 불일치"
        sent_rows += byte_row_html(f"#{index + 1}", sent_byte, sent_parity)
        received_rows += byte_row_html(f"#{index + 1}", got_byte, sent_parity,
                                       flipped_bit if index == flipped_byte else None, check)
    send_column, receive_column = st.columns(2)
    with send_column:
        render_html(f'<div class="bits-label">📤 보낸 데이터 (8칸 + 패리티)</div>{sent_rows}')
    with receive_column:
        render_html(f'<div class="bits-label">📥 받은 데이터 → 패리티 다시 계산</div>{received_rows}')
    return error_count


def run_parity_lab():
    """글자를 비트로 바꿔 보내는 중에 비트 하나를 뒤집고, 패리티와 XOR 체크섬이 알아채는지 확인한다."""
    render_html(BIT_STYLE + PARITY_STYLE)
    st.markdown("#### 🧪 비트 하나가 바뀌면 컴퓨터는 알아챌까?")
    text_column, flip_column = st.columns([2, 1])
    message = text_column.text_input("보낼 글자 (영어·숫자 추천, 8글자까지)", "BUG", max_chars=8, key="parity_text")
    data = message.encode("utf-8")                # 글자 → 바이트 (BUG → 66 85 71)
    if not data:
        result_box("input", "보낼 글자를 입력해 주세요.")
        return
    total_bits = len(data) * 8
    # 글자를 줄이면 전에 고른 비트 번호가 범위를 넘을 수 있어서, 입력칸을 그리기 전에 최댓값으로 맞춘다
    if st.session_state.get("parity_flip", 0) > total_bits:
        st.session_state["parity_flip"] = total_bits
    position = flip_column.number_input(f"뒤집을 비트 번호 (1~{total_bits}, 0 = 안 뒤집기)",
                                        min_value=0, max_value=total_bits, value=min(3, total_bits), key="parity_flip")

    received = flip_bit(data, position)          # 전송 중 비트 하나가 뒤집혔다고 가정
    error_count = show_transmission(data, received, position)

    # XOR 체크섬: 보낼 때 만든 확인값과, 받은 데이터로 다시 만든 확인값을 비교한다
    sent_sum, received_sum = xor_checksum(data), xor_checksum(received)
    st.code(f"XOR 체크섬 (보낼 때)  : {format(sent_sum, '08b')}  ({sent_sum})\n"
            f"XOR 체크섬 (받은 뒤)  : {format(received_sum, '08b')}  ({received_sum})")

    if position == 0:
        result_box("same", "아무 비트도 뒤집히지 않아서 패리티와 체크섬이 모두 일치해요.")
    elif error_count > 0 and sent_sum != received_sum:
        result_box("diff", f"{position}번 비트가 뒤집히자 패리티는 #{(position - 1) // 8 + 1} 바이트에서, "
                           "XOR 체크섬은 전체 확인값에서 오류를 잡아냈어요!")
    result_box("note", "패리티는 한 바이트 안에서 두 칸이 동시에 뒤집히면 1의 개수가 다시 짝수가 되어 알아채지 못해요. "
                       "그래서 실제 통신과 저장 장치는 CRC처럼 더 강한 검사 방법을 함께 써요.")


# -------------------------------------------------------------
# 6. 한글 조합 실험 (BUG-005): 유니코드 한글 조합 공식과 '완완성' 재현
# -------------------------------------------------------------

# 유니코드가 정해 둔 자모 순서. 리스트에서의 위치(0부터)가 공식에 들어가는 번호가 된다.
CHOSEONG = ["ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]  # 초성 19개
JUNGSEONG = ["ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ", "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ"]  # 중성 21개
JONGSEONG = ["(없음)", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ",
             "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]  # 종성 28개 (0번 = 받침 없음)
HANGUL_START = 0xAC00          # '가'의 유니코드 번호 (44032). 한글 11,172자는 여기서부터 빈틈없이 이어진다.


def compose(cho, jung, jong):
    """초성·중성·종성 번호로 완성된 한글 한 글자를 계산한다. (유니코드 한글 조합 공식)"""
    # 초성 하나마다 (중성 21 × 종성 28 = 588)자가 붙으므로, 번호 = 0xAC00 + (초성×21 + 중성)×28 + 종성
    return chr(HANGUL_START + (cho * 21 + jung) * 28 + jong)


def decompose(syllable):
    """완성된 한글 한 글자를 다시 초성·중성·종성 번호로 쪼갠다. (조합 공식을 거꾸로)"""
    offset = ord(syllable) - HANGUL_START          # '가'에서 몇 번째 글자인가
    cho = offset // 588                            # // : 몫. 588자씩 묶음이 몇 개인가 → 초성
    jung = (offset % 588) // 28                    # % : 나머지. 남은 것을 28로 나눈 몫 → 중성
    jong = offset % 28                             # 28로 나눈 나머지 → 종성
    return cho, jung, jong


def show_formula_lab():
    """초성·중성·종성을 골라서 공식으로 글자를 계산하고, 거꾸로 쪼개서 확인한다."""
    st.markdown("#### 🧪 한글은 계산식으로 만들어진다")
    cho_column, jung_column, jong_column = st.columns(3)
    # index=: 처음에 골라 둘 위치 → ㅇ(11) + ㅘ(9) + ㄴ(4) = '완'
    cho = cho_column.selectbox("초성", range(len(CHOSEONG)), index=11, format_func=lambda i: f"{CHOSEONG[i]} ({i})", key="hg_cho")
    jung = jung_column.selectbox("중성", range(len(JUNGSEONG)), index=9, format_func=lambda i: f"{JUNGSEONG[i]} ({i})", key="hg_jung")
    jong = jong_column.selectbox("종성", range(len(JONGSEONG)), index=4, format_func=lambda i: f"{JONGSEONG[i]} ({i})", key="hg_jong")

    syllable = compose(cho, jung, jong)
    number = ord(syllable)
    st.code(f"번호 = 44032 + ({cho} × 21 + {jung}) × 28 + {jong}\n"
            f"     = 44032 + {(cho * 21 + jung) * 28 + jong}\n"
            f"     = {number}  (16진수 U+{number:04X})\n"
            f"chr({number}) → '{syllable}'")
    back = decompose(syllable)
    result_box("note", f"거꾸로 쪼개면 ({back[0]}, {back[1]}, {back[2]}) → {CHOSEONG[back[0]]} + {JUNGSEONG[back[1]]} + {JONGSEONG[back[2]]}. "
                       "이렇게 조각으로 나눠 저장하는 방식이 BUG-004의 NFD예요.")


# '완선 → ⌫ → ㅅ ㅓ ㅇ' 재현 장면. 글자는 모두 compose()로 계산해서 만든다.
WAN = compose(11, 9, 4)     # ㅇ+ㅘ+ㄴ = 완
SEON = compose(9, 4, 4)     # ㅅ+ㅓ+ㄴ = 선
SEO = compose(9, 4, 0)      # ㅅ+ㅓ    = 서
SEONG = compose(9, 4, 21)   # ㅅ+ㅓ+ㅇ = 성

# 장면 하나 = (누른 키, 입력기가 조합 중인 글자, 정상 화면, 오류 화면, 설명, 근거)
REPLAY_FRAMES = [
    ("완 선", SEON, WAN + SEON, WAN + SEON,
     "'완선'까지 입력했어요. 입력기는 마지막 글자 '선'을 '조합 중' 상태로 들고 있어요.", "확인"),
    ("⌫", WAN, WAN, WAN,
     "'선'을 지웠어요. 이때 입력기가 앞 글자 '완'을 다시 조합 중으로 끌어와요. 프로그램은 '완'을 이미 완성된 글자로 기억해요.", "추정"),
    ("ㅅ", "ㅅ", WAN + "ㅅ", WAN + WAN + "ㅅ",
     "'완'에는 ㅅ을 받침으로 붙일 수 없어서 입력기는 '완'을 확정해서 보내고 ㅅ으로 새 글자를 시작해요. "
     "프로그램에는 이미 '완'이 있어서 '완'이 하나 더 생겨요.", "추정"),
    ("ㅓ", SEO, WAN + SEO, WAN + WAN + SEO,
     "ㅅ에 ㅓ가 붙어 조합 중인 글자가 '서'가 돼요.", "확인"),
    ("ㅇ", SEONG, WAN + SEONG, WAN + WAN + SEONG,
     "ㅇ이 받침으로 붙어 '성'이 돼요. 정상이라면 '완성', 오류가 나면 '완완성'이에요.", "확인"),
]


def show_replay():
    """'완선 → ⌫ → ㅅ ㅓ ㅇ'을 한 단계씩 넘기며 정상 화면과 오류 화면을 비교한다. (재현 화면)"""
    st.markdown("#### 🎞️ '완완성' 재현 (실제 녹화 아님)")
    step = st.slider("단계", 1, len(REPLAY_FRAMES), 1, key="hg_step")
    key, composing, normal, bug, explanation, basis = REPLAY_FRAMES[step - 1]
    keys_pressed = " → ".join(frame[0] for frame in REPLAY_FRAMES[:step])      # 지금까지 누른 키
    st.code(f"누른 키        : {keys_pressed}\n"
            f"입력기 조합 중 : '{composing}'  (U+{ord(composing[-1]):04X})\n"
            f"정상 화면      : {normal}\n"
            f"오류 화면      : {bug}")
    result_box("diff" if normal != bug else "same", f"[{basis}] {explanation}")
    st.caption("단계 2·3의 '입력기가 앞 글자를 다시 끌어온다'는 설명은 공식 문서로 확인되지 않은 추정이에요. "
               "실제로 겪은 현상(BUG-005 직접 관찰)을 원리에 맞춰 다시 그려 본 재현 화면이에요.")


def run_hangul_lab():
    """한글 조합 공식 계산기와 '완완성' 재현 화면을 차례로 보여 준다."""
    show_formula_lab()
    st.divider()
    show_replay()


# ----- 실제 실행 순서 -----
# 고른 실험에 맞는 함수를 실행하기 위한 표 (딕셔너리: 이름표 → 함수)
lab_functions = {
    "overflow": run_overflow_lab,
    "float": run_float_lab,
    "encoding": run_encoding_lab,
    "unicode": run_unicode_lab,
    "hangul": run_hangul_lab,
    "parity": run_parity_lab,
}

with crt_frame("pages/laboratory.py", "LAB"):
    page_banner("science", "PHENOMENON LAB", "현상 실험실", "직접 실행하며 컴퓨터의 처리 원리를 확인합니다.")
    selector_column, link_column = st.columns([3, 1], vertical_alignment="center")   # 1) 실험 고르기 + 관련 오류로 가기 버튼을 한 줄에 (세로 가운데 맞춤)
    with selector_column:
        show_lab_selector()
    selected_lab = st.session_state["lab_topic"]
    with link_column:
        show_case_link(selected_lab)
    with st.container(border=True):                        # 2) 실험 내용을 테두리 상자(실험대) 안에 담는다
        lab_functions[selected_lab]()
