# =============================================================
# pages/catalog.py  (오류 도감)
# 탐구 순서를 먼저 보여 주고, 사례마다 넓은 카드에
# 핵심 원리 · 먼저 알아 둘 용어 · 요약을 담아 보여 준다.
# 검색 조건은 다른 페이지에 다녀와도 그대로 유지된다. (상태 관리)
# =============================================================

from html import escape           # 글자 속 <, > 같은 기호를 안전하게 바꿔 주는 함수

import streamlit as st

from common import (
    CATEGORIES, CATEGORY_ICONS, CAUSE_TYPES,
    crt_frame, icon, load_cases, open_case, page_banner, render_html, search_cases,
)


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
    """검색창과 분류 선택 버튼을 한 줄에 보여 준다."""
    search_column, category_column = st.columns([3, 2], vertical_alignment="center")
    with search_column:
        # key: 입력값이 st.session_state["catalog_keyword"]에 저장된다. on_change: 값이 바뀌면 save_filters 실행
        st.text_input(
            "검색",
            key="catalog_keyword",
            placeholder="🔍 오류 이름이나 용어를 입력하세요. 예) 2의 보수, 0.1, 인코딩, 한글",
            on_change=save_filters,
            label_visibility="collapsed",
        )
    with category_column:
        st.radio(
            "분류",
            ["전체"] + CATEGORIES,       # 맨 앞에 "전체"를 붙인 분류 목록
            key="catalog_category",
            format_func=category_label,   # 화면에는 아이콘이 붙은 이름으로 보여 준다
            horizontal=True,
            on_change=save_filters,
            label_visibility="collapsed",
        )


# -------------------------------------------------------------
# 2. 탐구 순서 안내
# -------------------------------------------------------------

def show_reading_order(cases):
    """사례 5개가 어떤 질문으로 이어지는지 한 줄 흐름으로 보여 준다."""
    steps = " ▶ ".join(f"<span>BUG-{case['id']:03d} {escape(case['category'])}</span>" for case in cases)
    render_html(f"""
        <div class="bt-box bt-key">
            <div class="bt-box-label">{icon("route")} 탐구 순서 · 이 순서로 읽으면 이해가 쉬워요</div>
            <div>수업에서 배운 <b>정수(2의 보수)</b>에서 출발해 → <b>실수</b>는 어떻게 저장될까? →
            <b>글자</b>도 숫자로 저장된다면? → <b>한글</b>은 어떻게 조합될까? 로 이어집니다.</div>
            <div class="cat-flow">{steps}</div>
        </div>
    """)


# -------------------------------------------------------------
# 3. 넓은 사례 카드
# -------------------------------------------------------------

def show_case_row(case):
    """사례 하나를 넓은 카드로 보여 준다. 왼쪽: 설명과 용어 / 오른쪽: 핵심 원리와 버튼"""
    with st.container(border=True):
        info_column, key_column = st.columns([3, 2], vertical_alignment="top")
        with info_column:
            # 용어 이름표: 용어 이름 + 짧은 설명
            terms = "".join(f"<span><b>{escape(t['term'])}</b></span>" for t in case["terms"])
            render_html(f"""
                <div class="cat-head">
                    <span class="bt-badge bt-badge-on">BUG-{case['id']:03d}</span>
                    <span class="bt-badge">분류 · {escape(case['category'])}</span>
                    <span class="bt-badge">원인 유형 · {escape(case['cause_type'])}</span>
                </div>
                <div class="cat-title">{escape(case['title'])}</div>
                <div class="bt-card-nick">“{escape(case['nickname'])}”</div>
                <div class="cat-summary">{escape(case['summary'])}</div>
                <div class="bt-box-label" style="color:var(--ink)">{icon("menu_book")} 먼저 알아 둘 용어</div>
                <div class="cat-terms">{terms}</div>
            """)
        with key_column:
            render_html(f"""
                <div class="bt-box bt-key" style="margin-top:6px">
                    <div class="bt-box-label">💡 핵심 원리</div>
                    <b>{escape(case['key_point'])}</b>
                </div>
                <div style="font-size:0.9rem;color:var(--dim)">원인 유형: {escape(CAUSE_TYPES[case['cause_type']])}</div>
            """)
            if st.button("원인 추적하기 ▶", key=f"catalog_open_{case['id']}", type="primary", width="stretch"):
                open_case(case["id"])


def show_case_cards(results):
    """검색 결과를 넓은 카드로 한 줄에 하나씩 보여 준다."""
    if not results:      # 결과가 하나도 없을 때 안내 문구
        st.warning("조건에 맞는 오류가 없어요. 다른 검색어나 분류를 골라 보세요.")
        return
    for case in results:
        show_case_row(case)


# ----- 실제 실행 순서 -----
all_cases = load_cases()

with crt_frame("pages/catalog.py", "CATALOG"):
    page_banner("menu_book", "ERROR CATALOG", "오류 도감", f"비트 표현에서 출발한 {len(all_cases)}가지 디지털 오류를 탐구 순서대로 살펴봅니다.")
    show_reading_order(all_cases)        # 1) 탐구 순서
    restore_filters()                    # 2) 저장해 둔 검색 조건 되살리기
    show_filters()                       # 3) 검색창 + 분류 버튼

    # 4) 현재 검색 조건으로 오류 걸러 내고 카드로 보여 주기
    found_cases = search_cases(all_cases, st.session_state["catalog_keyword"], st.session_state["catalog_category"])
    show_case_cards(found_cases)
