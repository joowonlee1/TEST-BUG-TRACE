# =============================================================
# pages/anatomy.py  (원인 해부실)
# 오류 하나를 골라 위에서 아래로 '추적 순서'대로 분석한다.
#   ① 제목 → ② 증상 · 정상이라면 · 실제로는 (+ 직접 관찰)
#   → ③ 처리 과정(입력 → 처리 → 출력) → ④ 원인 추적 기록 #01~#04 (문서로 확인 / 추정)
#   → ⑤ 핵심 원리 → ⑥ 탭: 자주 생기는 곳 / 해결 방법 / 출처 / 관련 사례
# =============================================================

from html import escape           # 글자 속 <, > 기호를 안전하게 바꾸는 함수

import streamlit as st

from common import case_label, crt_frame, find_case, icon, load_cases, page_banner, render_html


# -------------------------------------------------------------
# 1. 선택한 오류 기억하기 (상태 관리)
# -------------------------------------------------------------

def restore_selected_case(case_ids):
    """홈이나 도감에서 고른 오류가 있으면 그 오류를 선택 상자에 넣는다."""
    # "anatomy_case"가 아직 없을 때(이 페이지에 처음 들어왔을 때)만 실행된다.
    # 저장된 번호가 없으면 첫 번째 오류(BUG-001)를 보여 준다.
    if "anatomy_case" not in st.session_state:
        st.session_state["anatomy_case"] = st.session_state.get("selected_case", case_ids[0])


def remember_case():
    """선택 상자에서 오류를 바꾸면 그 번호를 저장한다."""
    st.session_state["selected_case"] = st.session_state["anatomy_case"]


def move_to_case(case_id):
    """관련 사례 버튼을 누르면 그 오류로 바꾼다."""
    # 버튼의 on_click으로 실행되는 함수라서, 화면을 다시 그리기 전에 값이 바뀐다.
    st.session_state["anatomy_case"] = case_id
    st.session_state["selected_case"] = case_id


def show_case_selector(cases):
    """분석할 오류를 고르는 선택 상자를 보여 준다."""
    case_ids = [case["id"] for case in cases]   # [1, 2, 3, ..., 12]
    restore_selected_case(case_ids)
    # format_func: 선택지에 번호 대신 "BUG-001 · 제목"처럼 보여 준다.
    st.selectbox(
        "사례 선택",
        case_ids,
        key="anatomy_case",
        format_func=lambda case_id: case_label(find_case(cases, case_id)),
        on_change=remember_case,
        label_visibility="collapsed",
    )


# -------------------------------------------------------------
# 2. 화면 위쪽: 제목, 증상 비교, 처리 과정
# -------------------------------------------------------------

def section_label(icon_name, english, korean):
    """각 구역 위에 붙는 작은 제목. 예) ⚙ PROCESS · 처리 과정"""
    return f'<div class="sec-label">{icon(icon_name)} {english} · {korean}</div>'


def show_title(case):
    """① 이름표(번호·분류·기술·원인 유형) + 전문용어 제목 + 쉬운 이름 + 한 줄 요약"""
    render_html(f"""
        <div class="an-title">
            <div>
                <span class="bt-badge bt-badge-on">BUG-{case['id']:03d}</span>
                <span class="bt-badge">분류 · {escape(case['category'])}</span>
                <span class="bt-badge">기술 · {escape(case['tech'])}</span>
                <span class="bt-badge">원인 유형 · {escape(case['cause_type'])}</span>
            </div>
            <h2>{escape(case['title'])}</h2>
            <div class="bt-card-nick">“{escape(case['nickname'])}”</div>
            <div class="an-summary">{escape(case['summary'])}</div>
        </div>
    """)


def show_symptom_row(case):
    """② 증상 · 정상이라면 · 실제로는 → 같은 높이의 3칸으로 나란히 비교 (+ 직접 관찰은 아래 한 줄)"""
    # CSS 격자(grid)로 3칸을 만들면 글 길이가 달라도 세 상자의 높이가 똑같아진다.
    observed = ""
    # observation이 null(None)이 아닐 때만 직접 관찰 줄을 만든다.
    if case["observation"]:
        observed = f"""
            <div class="bt-box bt-obs an-observed">
                <div class="bt-box-label">{icon("visibility")} OBSERVED · 직접 관찰</div>{escape(case['observation'])}
            </div>
        """
    render_html(f"""
        {section_label("search", "SYMPTOM", "어떤 현상인가")}
        <div class="an-grid3">
            <div class="bt-box"><div class="bt-box-label">증상</div>{escape(case['symptom'])}</div>
            <div class="bt-box bt-ok"><div class="bt-box-label">EXPECTED · 정상이라면</div>{escape(case['expected'])}</div>
            <div class="bt-box bt-err"><div class="bt-box-label">ACTUAL · 실제로는</div>{escape(case['actual'])}</div>
        </div>
        {observed}
    """)


def show_flow(case):
    """③ 오류가 생기는 흐름을 '입력 → 처리 → 출력' 세 칸 그림으로 보여 준다."""
    flow = case["flow"]       # {"input": "...", "process": "...", "output": "..."}
    # 출력 칸(bt-flow-out)은 벽돌색으로 그려서 '이상한 결과'임을 강조한다.
    render_html(f"""
        {section_label("route", "PROCESS", "컴퓨터 안에서 일어난 일")}
        <div class="bt-flow">
            <div class="bt-flow-box">{icon("keyboard")}<div class="bt-flow-name">입력</div><div class="bt-flow-text">{escape(flow['input'])}</div></div>
            <div class="bt-flow-arrow">▶</div>
            <div class="bt-flow-box">{icon("settings")}<div class="bt-flow-name">처리</div><div class="bt-flow-text">{escape(flow['process'])}</div></div>
            <div class="bt-flow-arrow">▶</div>
            <div class="bt-flow-box bt-flow-out">{icon("error")}<div class="bt-flow-name">출력</div><div class="bt-flow-text">{escape(flow['output'])}</div></div>
        </div>
    """)


# -------------------------------------------------------------
# 3. 원인 추적 기록과 핵심 원리
# -------------------------------------------------------------

def basis_badge(basis):
    """단계마다 붙일 근거 이름표. 확인 = 공식 문서로 확인, 추정 = 아직 확인되지 않은 설명"""
    if basis == "확인":
        return '<span class="bt-basis bt-basis-ok">📘 문서로 확인</span>'
    return '<span class="bt-basis bt-basis-guess">🔎 추정</span>'


def show_steps(case):
    """④ 원인을 #01 → #02 … 순서의 추적 카드로 가로로 나란히 보여 준다. (타임라인)"""
    cards = ""
    # enumerate(목록, start=1): 번호(1, 2, 3...)와 단계 내용을 함께 꺼낸다.
    # 단계 하나는 {"basis": "확인" 또는 "추정", "text": "설명"} 형태의 딕셔너리다.
    for step_number, step in enumerate(case["steps"], start=1):
        cards += f"""
            <div class="an-step">
                <div class="an-step-head"><span class="bt-step-no">#{step_number:02d}</span>{basis_badge(step['basis'])}</div>
                <div class="an-step-text">{escape(step['text'])}</div>
            </div>
        """
    render_html(f"""
        {section_label("troubleshoot", "TRACE", "원인 추적 기록")}
        <div class="an-steps">{cards}</div>
    """)


def show_key_point(case):
    """⑤ 오류의 핵심 원리를 한 문장으로 정리해서 보여 준다."""
    render_html(f"""
        <div class="bt-box bt-key an-key">
            <div class="bt-box-label">💡 KEY POINT · 핵심 원리</div>
            <div>{escape(case['key_point'])}</div>
        </div>
    """)


def show_lab_link(case):
    """실험실로 가는 버튼 (실험할 수 있는 오류에서만 부른다)"""
    if st.button("현상 실험실에서 직접 확인", icon=":material/science:", type="primary", width="stretch"):
        # 어떤 실험을 열지 저장해 두고 실험실로 이동한다.
        st.session_state["saved_lab"] = case["lab"]
        st.switch_page("pages/laboratory.py")


# -------------------------------------------------------------
# 4. 아래 탭: 자주 생기는 곳 / 해결 방법 / 출처 / 관련 사례
# -------------------------------------------------------------

def show_bullets(items):
    """문장 목록을 글머리표 목록으로 보여 준다."""
    for item in items:
        st.markdown(f"- {item}")


def show_related_cases(cases, case):
    """관련 사례 버튼을 보여 주고, 누르면 그 오류로 바뀐다."""
    columns = st.columns(len(case["related"]))
    for column, related_id in zip(columns, case["related"]):
        related_case = find_case(cases, related_id)
        with column:
            # on_click=함수, args=(함수에 넘길 값,) → 버튼을 누르면 move_to_case(번호) 실행
            st.button(case_label(related_case), key=f"related_{related_id}",
                      on_click=move_to_case, args=(related_id,), width="stretch")


def show_detail_tabs(cases, case):
    """⑥ 자세한 정보를 탭으로 나눠서 한 화면에 담는다. (스크롤을 줄이려고)"""
    where_tab, fix_tab, source_tab, related_tab = st.tabs(
        ["📍 자주 생기는 곳", "🛠️ 해결 방법", "📚 출처", "🔗 관련 사례"]
    )
    with where_tab:
        show_bullets(case["where"])
    with fix_tab:
        user_column, developer_column = st.columns(2)
        with user_column:
            st.markdown("**사용자가 할 수 있는 것**")
            show_bullets(case["fix_user"])
        with developer_column:
            st.markdown("**개발자가 할 수 있는 것**")
            show_bullets(case["fix_dev"])
    with source_tab:
        st.caption("📘 문서로 확인 = 아래 공식 문서로 확인한 내용 · 🔎 추정 = 공식 설명이 없어 추정한 내용")
        for source in case["sources"]:
            # [글자](주소) → 마크다운 링크. 누르면 새 탭에서 문서가 열린다.
            st.markdown(f"- [{source['title']}]({source['url']})")
    with related_tab:
        show_related_cases(cases, case)


def apply_anatomy_style():
    """원인 해부실에만 쓰는 배치 디자인"""
    render_html("""
        <style>
        /* 구역 제목: 진한 초록 픽셀 글꼴 + 아래 점선 */
        .sec-label { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: 0.95rem;
                     border-bottom: 2px dashed rgba(31, 77, 37, .35); padding-bottom: 3px; margin: 10px 0 8px; }
        .an-title h2 { margin: 2px 0 0 !important; }
        .an-summary { color: var(--dim); font-size: 0.95rem; }
        /* 같은 높이의 3칸 격자 (증상 · 정상이라면 · 실제로는) */
        .an-grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .an-grid3 .bt-box { margin: 0; }
        .an-observed { margin-top: 10px; }
        /* 원인 추적 카드: 화면 폭에 맞춰 한 줄에 최대 4장, 높이는 모두 같게 */
        .an-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px; margin-bottom: 16px; }
        .an-step { background: var(--paper); border: 3px solid var(--ink); padding: 10px 12px; }
        .an-step-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
        .an-step-head .bt-step-no { flex: none; width: 50px; height: 32px; line-height: 28px; }
        .an-step-text { font-size: 0.92rem; line-height: 1.6; color: var(--text); }
        .an-key { margin: 0 0 14px 0; }    /* 아래 탭과 붙지 않게 여백 */
        @media (max-width: 800px) { .an-grid3 { grid-template-columns: 1fr; } }
        </style>
    """)


# ----- 실제 실행 순서 -----
all_cases = load_cases()
apply_anatomy_style()

with crt_frame("pages/anatomy.py", "ANATOMY"):
    page_banner("layers", "ROOT CAUSE", "원인 해부실", "오류가 발생하는 내부 처리 과정을 한 단계씩 추적합니다.")
    show_case_selector(all_cases)                                               # 오류 고르기
    current_case = find_case(all_cases, st.session_state["anatomy_case"])       # 고른 오류 데이터

    show_title(current_case)                  # ① 제목
    show_symptom_row(current_case)            # ② 증상 · 정상이라면 · 실제로는 (+ 직접 관찰)
    show_flow(current_case)                   # ③ 처리 과정
    show_steps(current_case)                  # ④ 원인 추적 기록

    # ⑤ 핵심 원리: 실험할 수 있는 오류(lab 값이 있음)면 오른쪽에 실험실 버튼을 붙이고, 없으면 한 줄 전체를 쓴다.
    if current_case["lab"]:
        key_column, lab_column = st.columns([4, 1], vertical_alignment="center")
        with key_column:
            show_key_point(current_case)
        with lab_column:
            show_lab_link(current_case)
    else:
        show_key_point(current_case)

    show_detail_tabs(all_cases, current_case)                                   # ⑥ 아래 탭
