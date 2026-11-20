
# =============================================================
# pages/catalog.py  (오류 도감)
# 탐구 순서를 먼저 보여 주고, 사례마다 넓은 카드에
# 핵심 원리 · 먼저 알아 둘 용어 · 요약을 담아 보여 준다.
# 두 사례를 필터 없이 모두 보여 주고, 기존 상세 카드의 정보와 이동 기능은 유지한다.
# =============================================================

from html import escape

import streamlit as st

from common import (
    CAUSE_TYPES,
    crt_frame, icon, load_cases, open_case, page_banner, render_html,
)


# -------------------------------------------------------------
# 1. 탐구 순서 안내
# -------------------------------------------------------------

def show_reading_order(cases):
    """사례들이 어떤 질문으로 이어지는지 한 줄 흐름으로 보여 준다."""
    steps = " ▶ ".join(f"<span>BUG-{case['id']:03d} {escape(case['category'])}</span>" for case in cases)
    render_html(f"""
        <div class="bt-box bt-key">
            <div class="bt-box-label">{icon("route")} 탐구 순서 · 이 순서로 읽으면 이해가 쉬워요</div>
            <div>① 수업에서 배운 <b>정수(2의 보수)</b>는 칸이 정해져 있으면 끝을 넘을 때 어떻게 될까?<br>
            ② 소수점이 있는 <b>실수</b>는 같은 칸 안에 어떻게 저장되고, 어디서 한계가 생길까?<br>
            ③ 망가진 데이터를 컴퓨터는 어떻게 <b>알아챌까?</b></div>
            <div class="cat-flow">{steps} ▶ <span>오류 검출</span></div>
        </div>
    """)


# -------------------------------------------------------------
# 2. 넓은 사례 카드
# -------------------------------------------------------------

def show_case_row(case):
    """사례 하나를 넓은 카드로 보여 준다. 왼쪽: 설명과 용어 / 오른쪽: 핵심 원리와 버튼"""
    with st.container(border=True):
        info_column, key_column = st.columns([3, 2], vertical_alignment="top")
        with info_column:
            # 용어 이름표: title= 에 설명을 넣으면 마우스를 올렸을 때 짧은 설명이 뜬다
            terms = "".join(f'<span title="{escape(t["desc"])}"><b>{escape(t["term"])}</b></span>' for t in case["terms"])
            render_html(f"""
                <div class="cat-head">
                    <span class="bt-badge bt-badge-on">BUG-{case['id']:03d}</span>
                    <span class="bt-badge">분류 · {escape(case['category'])}</span>
                    <span class="bt-badge">원인 유형 · {escape(case['cause_type'])}</span>
                </div>
                <div class="cat-title">{escape(case['title'])}</div>
                <div class="bt-card-nick">“{escape(case['nickname'])}”</div>
                <div class="cat-summary">{escape(case['summary'])}</div>
                <div class="bt-box-label" style="color:var(--ink)">{icon("menu_book")} 먼저 알아 둘 용어 (마우스를 올리면 설명이 보여요)</div>
                <div class="cat-terms">{terms}</div>
            """)
        with key_column:
            render_html(f"""
                <div class="bt-box bt-key" style="margin-top:6px">
                    <div class="bt-box-label">💡 핵심 원리</div>
                    <b>{escape(case['key_point'])}</b>
                </div>
                <div style="font-size:0.9rem;color:var(--dim)">{escape(case['cause_type'])}: {escape(CAUSE_TYPES[case['cause_type']])}</div>
            """)
            if st.button("원인 추적하기 ▶", key=f"catalog_open_{case['id']}", type="primary", width="stretch"):
                open_case(case["id"])


def show_case_cards(results):
    """오류 사례를 넓은 카드로 한 줄에 하나씩 보여 준다."""
    if not results:
        st.info("등록된 오류 사례가 아직 없어요.")
        return
    for case in results:
        show_case_row(case)


# ----- 실제 실행 순서 -----
all_cases = load_cases()

with crt_frame("pages/catalog.py", "CATALOG"):
    page_banner("menu_book", "ERROR CATALOG", "오류 도감", f"숫자를 정해진 개수의 비트에 저장해서 생기는 {len(all_cases)}가지 오류를 깊이 살펴봅니다.")
    show_reading_order(all_cases)
    render_html(f'''<div class="cat-guide"><b>총 {len(all_cases)}가지 오류</b> · 정수와 실수의 저장 방식에서 생기는 한계를 차례로 살펴보세요.</div>''')
    show_case_cards(all_cases)
