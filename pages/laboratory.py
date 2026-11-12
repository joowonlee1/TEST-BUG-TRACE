# =============================================================
# pages/laboratory.py  (현상 실험실)
# 원인 해부실에서 설명한 원리를 실제 계산 결과로 확인(검증)하는 페이지
# 실험 5가지: 부동소수점, 문자열 정렬, 유니코드 정규화, 문자 인코딩, 시간대
# =============================================================

import re                                        # 정규표현식: 글자 속에서 숫자 부분을 찾을 때 사용
import unicodedata                               # 유니코드 정규화(NFC, NFD) 기능
from datetime import date, datetime, time, timezone   # 날짜, 날짜+시각, 시각, 시간대
from decimal import Decimal                      # 10진수를 정확하게 계산하는 자료형
from zoneinfo import ZoneInfo                    # 지역 이름으로 시간대를 정하는 도구 (서머타임 자동 반영)

import altair as alt
import pandas as pd
import streamlit as st

from common import open_case, page_header

# 실험 목록: "실험 이름표": ("화면에 보일 이름", 관련 오류 번호)
LABS = {
    "float": ("0.1 + 0.2 계산하기", 2),
    "sort": ("숫자 정렬하기", 9),
    "unicode": ("한글 쪼개 보기 (NFC / NFD)", 10),
    "encoding": ("글자를 바이트로 바꾸기", 3),
    "timezone": ("시간대 바꿔 보기", 8),
}

# 시간대: 숫자(+9, -5)로 고정하지 않고 '지역 이름'으로 정한다.
# → 미국처럼 서머타임이 있는 지역도 날짜에 맞는 시간 차이가 자동으로 계산된다.
KOREA_TIME = ZoneInfo("Asia/Seoul")              # 한국 (항상 UTC+9)
NEW_YORK_TIME = ZoneInfo("America/New_York")     # 미국 뉴욕 (겨울 UTC-5, 여름 UTC-4)


# -------------------------------------------------------------
# 0. 공통 함수
# -------------------------------------------------------------

def restore_lab():
    """원인 해부실에서 고른 실험이 있으면 그 실험을 먼저 보여 준다."""
    if "lab_topic" not in st.session_state:
        st.session_state["lab_topic"] = st.session_state.get("saved_lab", "float")


def save_lab():
    """고른 실험을 저장해서 다른 페이지에 다녀와도 유지한다."""
    st.session_state["saved_lab"] = st.session_state["lab_topic"]


def show_lab_selector():
    """실험을 고르는 선택 상자를 보여 준다."""
    restore_lab()
    st.selectbox(
        "실험 선택",
        list(LABS.keys()),
        key="lab_topic",
        format_func=lambda lab: LABS[lab][0],     # 이름표 대신 화면용 이름을 보여 준다
        on_change=save_lab,
    )


def run_button(key):
    """모든 실험에서 함께 쓰는 '실험 실행하기' 버튼. 누르면 True를 돌려준다."""
    # icon: 재생(▶) 아이콘, type="primary": 라임색 버튼, width="stretch": 칸 너비만큼 넓게
    return st.button("실험 실행하기", key=key, type="primary", icon=":material/play_arrow:", width="stretch")


def show_case_link(lab):
    """실험과 관련된 오류의 원인 해부실로 가는 버튼"""
    case_id = LABS[lab][1]
    if st.button(f"📖 CASE {case_id:02d} 원인 설명 보러 가기", key=f"lab_link_{lab}"):
        open_case(case_id)


def to_hex(data):
    """바이트를 사람이 읽기 쉬운 16진수 문자열로 바꾼다. 예) b'\\xed\\x95\\x9c' → 'ED 95 9C'"""
    return " ".join(f"{byte:02X}" for byte in data)


# -------------------------------------------------------------
# 1. 부동소수점 실험 (CASE 02)
# -------------------------------------------------------------

def run_float_lab():
    """두 소수를 더해서 컴퓨터 계산 결과와 정확한 값을 비교한다."""
    st.markdown("#### 🧪 0.1 + 0.2는 정말 0.3일까?")
    first_column, second_column = st.columns(2)
    first_text = first_column.text_input("첫 번째 수", "0.1", key="float_first")
    second_text = second_column.text_input("두 번째 수", "0.2", key="float_second")

    if run_button("float_run"):
        show_float_result(first_text.strip(), second_text.strip())

    show_float_error_chart()


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
        st.error("계산할 수 있는 숫자를 입력해 주세요. 예) 0.1")
        return

    # !r (repr): 숫자를 줄이지 않고 컴퓨터가 가진 값 그대로 보여 준다.
    st.code(f"컴퓨터 계산 (float)   : {first_text} + {second_text} = {computer_result!r}\n"
            f"정확한 계산 (Decimal) : {first_text} + {second_text} = {exact_result}")

    # 두 결과가 같은지 비교
    if computer_result == float(exact_result):
        st.success("이번에는 두 결과가 같아요. 2진수로 딱 떨어지거나 오차가 반올림으로 사라진 경우예요.")
    else:
        st.error(f"두 결과가 달라요! 컴퓨터 계산 결과({computer_result!r})는 정확한 값({exact_result})과 다른 수예요.")

    # Decimal(float값): 컴퓨터 안에 '실제로' 저장된 값을 끝까지 보여 준다.
    st.markdown("**컴퓨터 안에 실제로 저장된 값**")
    st.code(f"{first_text} → {Decimal(first_number)}\n"
            f"{second_text} → {Decimal(second_number)}")


def show_float_error_chart():
    """0.1을 여러 번 더할수록 오차가 어떻게 쌓이는지 그래프로 보여 준다."""
    st.markdown("#### 📈 0.1을 계속 더하면 오차는 어떻게 될까?")
    repeat_count = st.slider("0.1을 더하는 횟수", 10, 1000, 100, step=10)

    total = 0.0
    errors = []
    for count in range(1, repeat_count + 1):
        total += 0.1                                   # 컴퓨터 방식으로 0.1을 더한다
        exact = Decimal(count) / Decimal(10)           # 정확한 값 (count × 0.1)
        error = abs(Decimal(total) - exact)            # 둘의 차이 = 오차
        errors.append(float(error))

    # 가로축: 더한 횟수, 세로축: 오차
    chart_data = pd.DataFrame({"오차": errors}, index=range(1, repeat_count + 1))
    plot_data = chart_data.reset_index().rename(columns={"index": "더한 횟수"})
    chart = alt.Chart(plot_data).mark_line(color="#B15C3A", strokeWidth=3).encode(
        x=alt.X("더한 횟수:Q", title="0.1을 더한 횟수"),
        y=alt.Y("오차:Q", title="절대 오차"),
        tooltip=["더한 횟수:Q", alt.Tooltip("오차:Q", format=".12g")],
    ).properties(height=300)
    st.altair_chart(chart, width="stretch")
    st.caption(f"0.1을 {repeat_count}번 더한 결과: {total!r} (정확한 값: {Decimal(repeat_count) / Decimal(10)})")


# -------------------------------------------------------------
# 2. 문자열 정렬 실험 (CASE 09)
# -------------------------------------------------------------

def natural_key(text):
    """자연 정렬용 기준을 만든다. '사진10' → ['사진', 10, ''] 처럼 숫자 부분을 수로 바꾼다."""
    # re.split(r"(\d+)", ...) : 숫자 덩어리를 기준으로 글자를 나눈다.
    parts = re.split(r"(\d+)", text)
    key = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))        # 숫자 부분은 수(int)로 바꿔서 크기로 비교
        else:
            key.append(part)             # 나머지는 글자 그대로
    return key


def run_sort_lab():
    """같은 목록을 '글자 정렬'과 '자연 정렬'로 각각 정렬해서 비교한다."""
    st.markdown("#### 🧪 10은 왜 2보다 앞에 올까?")
    st.caption("쉼표(,)로 구분해서 입력하세요. 예) 사진1, 사진10, 사진2")
    input_text = st.text_input("정렬할 목록", "10, 2, 1, 20, 3", key="sort_input")

    if run_button("sort_run"):
        # 쉼표로 나누고, 앞뒤 공백을 지우고, 빈 항목은 뺀다.
        items = [item.strip() for item in input_text.split(",") if item.strip()]
        if not items:
            st.error("정렬할 항목을 입력해 주세요.")
            return

        text_sorted = sorted(items)                       # 글자(사전식) 정렬
        natural_sorted = sorted(items, key=natural_key)   # 자연 정렬

        input_column, text_column, natural_column = st.columns(3)
        with input_column:
            st.markdown("**입력한 순서**")
            st.code("\n".join(items))
        with text_column:
            st.markdown("**글자로 정렬 (컴퓨터 기본)**")
            st.code("\n".join(text_sorted))
        with natural_column:
            st.markdown("**자연 정렬 (사람의 기대)**")
            st.code("\n".join(natural_sorted))

        if text_sorted != natural_sorted:
            st.error("두 결과가 달라요! 글자 정렬은 첫 글자부터 하나씩 비교하기 때문이에요.")
        else:
            st.success("이번에는 두 결과가 같아요. 자릿수가 다른 숫자를 섞어 보세요.")


# -------------------------------------------------------------
# 3. 유니코드 정규화 실험 (CASE 10)
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
            st.error("글자를 입력해 주세요.")
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
            st.success("두 방식의 결과가 같아요. 한글이 아닌 글자는 쪼개지지 않을 수 있어요.")
        else:
            st.error(f"화면에는 똑같이 '{input_text}'로 보이지만, 컴퓨터는 두 글자를 다른 글자로 판단해요. (NFC == NFD → False)")


# -------------------------------------------------------------
# 4. 문자 인코딩 실험 (CASE 03)
# -------------------------------------------------------------

def run_encoding_lab():
    """글자를 UTF-8과 CP949 바이트로 바꾸고, 다른 규칙으로 잘못 읽어 본다."""
    st.markdown("#### 🧪 글자는 왜 �로 깨질까?")
    input_text = st.text_input("글자를 입력하세요", "한글", key="encoding_input")

    if run_button("encoding_run"):
        if not input_text:
            st.error("글자를 입력해 주세요.")
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
        st.info("저장할 때와 읽을 때 같은 규칙(인코딩)을 써야 글자가 제대로 보여요.")


# -------------------------------------------------------------
# 5. 시간대 실험 (CASE 08)
# -------------------------------------------------------------

def run_timezone_lab():
    """한국 시간을 UTC와 미국 동부 시간으로 바꿔서 날짜가 달라지는지 확인한다."""
    st.markdown("#### 🧪 같은 순간인데 왜 날짜가 다를까?")
    date_column, time_column = st.columns(2)
    korea_date = date_column.date_input("한국 날짜", date(2026, 11, 12), key="tz_date")
    korea_clock = time_column.time_input("한국 시각", time(8, 0), key="tz_time")

    if run_button("tz_run"):
        # 날짜 + 시각 + 한국 시간대를 합쳐서 '한국 기준 시간'을 만든다.
        korea_moment = datetime.combine(korea_date, korea_clock, tzinfo=KOREA_TIME)
        # astimezone(): 같은 순간을 다른 시간대 기준으로 바꾼다.
        utc_moment = korea_moment.astimezone(timezone.utc)
        new_york_moment = korea_moment.astimezone(NEW_YORK_TIME)

        # %z: UTC와의 시간 차이 (+0900, -0500처럼 표시)
        time_format = "%Y-%m-%d %H:%M (UTC%z)"
        st.code(f"한국 서울   : {korea_moment.strftime(time_format)}\n"
                f"UTC 기준    : {utc_moment.strftime(time_format)}\n"
                f"미국 뉴욕   : {new_york_moment.strftime(time_format)}")

        # .date(): 시각을 버리고 날짜만 비교한다.
        if utc_moment.date() != korea_moment.date():
            st.error("UTC 기준으로는 날짜가 하루 전이에요! 날짜만 잘라서 보여 주면 하루 차이가 나요.")
        else:
            st.success("이 시각은 UTC로 바꿔도 날짜가 같아요. 한국 시간 오전 0시~9시 사이로 바꿔 보세요.")

        # 뉴욕은 서머타임 때문에 계절마다 시간 차이가 달라진다.
        new_york_offset = new_york_moment.utcoffset().total_seconds() / 3600   # 초 → 시간
        st.caption(f"이 날짜의 뉴욕은 UTC{new_york_offset:+.0f}시간이에요. "
                   "여름(서머타임)에는 -4시간, 겨울에는 -5시간으로 바뀌어요. 날짜를 7월로 바꿔서 확인해 보세요.")


# ----- 실제 실행 순서 -----
page_header("science", "현상 실험실", "직접 실행하며 컴퓨터의 처리 원리를 확인합니다.")
show_lab_selector()                       # 1) 실험 고르기

selected_lab = st.session_state["lab_topic"]

# 2) 고른 실험에 맞는 함수를 실행한다. (딕셔너리: 이름표 → 함수)
lab_functions = {
    "float": run_float_lab,
    "sort": run_sort_lab,
    "unicode": run_unicode_lab,
    "encoding": run_encoding_lab,
    "timezone": run_timezone_lab,
}
with st.container(border=True):           # 실험 내용을 테두리 상자(실험대) 안에 담는다
    lab_functions[selected_lab]()

st.divider()
show_case_link(selected_lab)              # 3) 관련 오류 설명으로 가기
