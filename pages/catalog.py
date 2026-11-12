# =============================================================
# pages/catalog.py  (오류 도감)
# 전체 오류 목록을 검색어와 분류로 걸러서 카드로 보여 주고,
# 아래쪽에 오류 로그와 그래프 2개(분류별, 원인 유형별)를 보여 준다.
# 검색 조건은 다른 페이지에 다녀와도 그대로 유지된다. (상태 관리)
# =============================================================

from html import escape           # 글자 속 <, > 같은 기호를 안전하게 바꿔 주는 함수

import streamlit as st

from common import (
    CATEGORIES, CATEGORY_ICONS, CAUSE_TYPES,
    case_card, count_values, crt_frame, load_cases, open_case, page_banner, render_html, search_cases, terminal_log,
)

CARDS_PER_ROW = 4                 # 한 줄에 보여 줄 카드 수 (한 화면에 많이 보이도록 4개)


# -------------------------------------------------------------
# 1. 검색 조건 (상태 관리)
# -------------------------------------------------------------

def restore_filters():
    """저장해 둔 검색 조건을 검색창과 분류 버튼에 다시 넣는다."""
    # Streamlit은 다른 페이지로 이동하면 그 페이지의 입력값(위젯 값)을 지운다.
    # 그래서 검색 조건을 "saved_..."라는 별도 이름으로 저장해 두었다가, 돌아왔을 때 다시 넣어 준다.
    if "catalog_keyword" not in st.session_state:
        st.session_state["catalog_keyword"] = st.session_state.get("saved_keyword", "")
    if "catalog_category" not in st.session_state:
        st.session_state["catalog_category"] = st.session_state.get("saved_category", "전체")


def save_filters():
    """검색어나 분류가 바뀔 때마다 별도 이름으로 저장한다."""
    st.session_state["saved_keyword"] = st.session_state["catalog_keyword"]
    st.session_state["saved_category"] = st.session_state["catalog_category"]


def category_label(category):
    """분류 버튼에 아이콘을 붙인다. 예) "입력" → ":material/keyboard: 입력" """
    return f":material/{CATEGORY_ICONS[category]}: {category}"


def show_filters():
    """검색창과 분류 선택 버튼을 보여 준다."""
    # key: 입력값이 st.session_state["catalog_keyword"]에 저장된다.
    # on_change: 값이 바뀌면 save_filters 함수를 실행한다.
    st.text_input(
        "검색",
        key="catalog_keyword",
        placeholder="🔍 오류 이름이나 키워드를 입력하세요. 예) 한글, 엑셀, 사진, 캐시",
        on_change=save_filters,
        label_visibility="collapsed",   # "검색" 글자는 숨겨서 공간을 아낀다
    )
    st.radio(
        "분류",
        ["전체"] + CATEGORIES,       # 맨 앞에 "전체"를 붙인 분류 목록
        key="catalog_category",
        format_func=category_label,   # 화면에는 아이콘이 붙은 이름으로 보여 준다
        horizontal=True,              # 버튼을 가로로 나열
        on_change=save_filters,
        label_visibility="collapsed",
    )


# -------------------------------------------------------------
# 2. 오류 카드
# -------------------------------------------------------------

def show_case_cards(results):
    """검색 결과를 한 줄에 4개씩 카드로 보여 준다."""
    # 결과가 하나도 없을 때 안내 문구
    if not results:
        st.warning("조건에 맞는 오류가 없어요. 다른 검색어나 분류를 골라 보세요.")
        return

    # range(0, 개수, 4) → 0, 4, 8 ... 처럼 4개씩 건너뛰며 한 줄씩 만든다.
    for start in range(0, len(results), CARDS_PER_ROW):
        row_cases = results[start:start + CARDS_PER_ROW]   # 이번 줄에 들어갈 오류들
        columns = st.columns(CARDS_PER_ROW)
        for column, case in zip(columns, row_cases):
            with column:
                with st.container(border=True):
                    case_card(case)
                    if st.button("원인 추적 ▶", key=f"catalog_open_{case['id']}", width="stretch"):
                        open_case(case["id"])


# -------------------------------------------------------------
# 3. 아래쪽: 오류 로그 + 그래프 2개
# -------------------------------------------------------------

def show_error_log(results, total_count):
    """현재 검색 상태를 터미널 로그처럼 보여 준다."""
    keyword = st.session_state["catalog_keyword"].strip() or "(없음)"
    terminal_log([
        ("INFO", f"{total_count} CASES LOADED"),
        ("INFO", f"분류 = {st.session_state['catalog_category']}"),
        ("INFO", f"검색어 = {keyword}"),
        ("ANALYZE", f"결과 {len(results)}건 / 전체 {total_count}건"),
    ])


def pixel_bar_chart(title, names, counts):
    """이름 목록과 개수 목록으로 '픽셀 막대그래프'를 HTML로 그린다. (데이터 시각화)"""
    largest = max(counts)                     # 가장 큰 값 → 이 막대가 100% 길이가 된다
    rows = ""
    # zip(): 이름과 개수를 하나씩 짝지어 반복한다.
    for name, count in zip(names, counts):
        percent = count / largest * 100       # 막대 길이(%) = 개수 ÷ 가장 큰 값 × 100
        rows += f"""
            <div class="pxbar-row">
                <span class="pxbar-name">{escape(name)}</span>
                <span class="pxbar-track"><span class="pxbar-fill" style="width:{percent:.0f}%"></span></span>
                <span class="pxbar-count">{count}</span>
            </div>
        """
    render_html(f'<div class="pxbar"><div class="pxbar-title">{escape(title)}</div>{rows}</div>')


def show_charts(cases):
    """분류별 오류 수, 원인 유형별 오류 수 그래프 2개를 나란히 보여 준다."""
    category_column, cause_column = st.columns(2)
    with category_column:
        pixel_bar_chart("📊 분류별 오류 수", CATEGORIES, count_values(cases, "category", CATEGORIES))
    with cause_column:
        cause_names = list(CAUSE_TYPES.keys())
        pixel_bar_chart("📊 원인 유형별 오류 수", cause_names, count_values(cases, "cause_type", cause_names))


# ----- 실제 실행 순서 -----
all_cases = load_cases()

with crt_frame("pages/catalog.py", "CATALOG"):
    page_banner("menu_book", "ERROR CATALOG", "오류 도감", "일상에서 마주치는 12가지 디지털 오류를 검색하고 분류별로 살펴봅니다.")
    restore_filters()                    # 1) 저장해 둔 검색 조건 되살리기
    show_filters()                       # 2) 검색창 + 분류 버튼

    # 3) 현재 검색 조건으로 오류 걸러 내기
    found_cases = search_cases(all_cases, st.session_state["catalog_keyword"], st.session_state["catalog_category"])
    show_case_cards(found_cases)         # 4) 결과 카드

    # 5) 아래쪽: 왼쪽 오류 로그 / 오른쪽 그래프 2개
    log_column, chart_column = st.columns([1, 2])
    with log_column:
        show_error_log(found_cases, len(all_cases))
    with chart_column:
        show_charts(all_cases)
