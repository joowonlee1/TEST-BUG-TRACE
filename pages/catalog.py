# =============================================================
# pages/catalog.py  (오류 도감)
# 전체 오류 목록을 검색어와 분류로 걸러서 카드로 보여 준다.
# 검색 조건은 다른 페이지에 다녀와도 그대로 유지된다. (상태 관리)
# =============================================================

import altair as alt
import pandas as pd               # 표 형태의 데이터를 다루는 라이브러리 (그래프용)
import streamlit as st

from common import (
    CATEGORIES, CATEGORY_ICONS, case_card, load_cases, open_case, page_header, search_cases,
)

CARDS_PER_ROW = 3                 # 한 줄에 보여 줄 카드 수


def restore_filters():
    """저장해 둔 검색 조건을 검색창과 분류 버튼에 다시 넣는다."""
    # Streamlit은 다른 페이지로 이동하면 그 페이지의 입력값(위젯 값)을 지운다.
    # 그래서 검색 조건을 "saved_..."라는 별도 이름으로 저장해 두었다가,
    # 이 페이지로 돌아왔을 때 다시 넣어 준다.
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
        placeholder="🔍 오류 제목이나 키워드를 검색하세요. 예) 한글, 엑셀, 사진",
        on_change=save_filters,
    )
    st.radio(
        "분류",
        ["전체"] + CATEGORIES,       # 맨 앞에 "전체"를 붙인 분류 목록
        key="catalog_category",
        format_func=category_label,   # 화면에는 아이콘이 붙은 이름으로 보여 준다
        horizontal=True,              # 버튼을 가로로 나열
        on_change=save_filters,
    )


def show_case_cards(results, total_count):
    """검색 결과를 한 줄에 3개씩 카드로 보여 준다."""
    st.caption(f"검색 결과 {len(results)}건 / 전체 {total_count}건")

    # 결과가 하나도 없을 때 안내 문구
    if not results:
        st.warning("조건에 맞는 오류가 없어요. 다른 검색어나 분류를 골라 보세요.")
        return

    # range(0, 개수, 3) → 0, 3, 6, 9 ... 처럼 3개씩 건너뛰며 한 줄씩 만든다.
    for start in range(0, len(results), CARDS_PER_ROW):
        row_cases = results[start:start + CARDS_PER_ROW]   # 이번 줄에 들어갈 오류들
        columns = st.columns(CARDS_PER_ROW)
        for column, case in zip(columns, row_cases):
            with column:
                with st.container(border=True):
                    case_card(case)
                    if st.button("원인 추적하기 →", key=f"catalog_open_{case['id']}", width="stretch"):
                        open_case(case["id"])


def count_by_category(cases):
    """분류마다 오류가 몇 개인지 세서 리스트로 돌려준다."""
    counts = []
    for category in CATEGORIES:
        count = 0
        for case in cases:
            if case["category"] == category:
                count += 1
        counts.append(count)
    return counts


def show_category_chart(cases):
    """분류별 오류 수를 막대그래프로 보여 준다. (데이터 시각화)"""
    st.markdown("### 분류별 오류 수")
    # index: 막대 옆에 쓸 이름(분류), 값: 막대 길이(오류 수)
    chart_data = pd.DataFrame({"오류 수": count_by_category(cases)}, index=CATEGORIES)
    # horizontal=True: 막대를 가로로 눕혀서 분류 이름을 똑바로 읽을 수 있게 한다.
    plot_data = chart_data.reset_index().rename(columns={"index": "분류"})
    chart = alt.Chart(plot_data).mark_bar(color="#51743C", cornerRadiusEnd=5).encode(
        x=alt.X("오류 수:Q", title="오류 수", axis=alt.Axis(tickMinStep=1)),
        y=alt.Y("분류:N", title=None, sort=CATEGORIES),
        tooltip=["분류:N", "오류 수:Q"],
    ).properties(height=285)
    st.altair_chart(chart, width="stretch")


# ----- 실제 실행 순서 -----
all_cases = load_cases()
page_header("menu_book", "오류 도감", "일상에서 마주치는 12가지 디지털 오류를 살펴봅니다.")
restore_filters()                       # 1) 저장해 둔 검색 조건 되살리기
show_filters()                          # 2) 검색창 + 분류 버튼

# 3) 현재 검색 조건으로 오류 걸러 내기
found_cases = search_cases(
    all_cases,
    st.session_state["catalog_keyword"],
    st.session_state["catalog_category"],
)

show_case_cards(found_cases, len(all_cases))   # 4) 결과 카드
st.divider()
show_category_chart(all_cases)                 # 5) 분류별 막대그래프
