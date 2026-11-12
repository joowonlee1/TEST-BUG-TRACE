# =============================================================
# pages/anatomy.py  (원인 해부실)
# 오류 하나를 골라 한 화면에서 분석한다.
#   왼쪽: 증상 → 직접 관찰 → 정상/실제 비교 → 처리 과정(입력 → 처리 → 출력)
#   오른쪽: 원인 추적 기록(#01~#04, 문서로 확인/추정 표시) → 핵심 원리
#   아래 탭: 자주 생기는 곳 / 해결 방법 / 출처 / 관련 사례
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
# 2. 왼쪽 칸: 증상과 처리 과정
# -------------------------------------------------------------

def show_title(case):
    """이름표(번호·분류·기술·원인 유형) + 전문용어 제목 + 쉬운 이름 + 한 줄 요약"""
    render_html(f"""
        <div>
            <span class="bt-badge bt-badge-on">BUG-{case['id']:03d}</span>
            <span class="bt-badge">분류 · {escape(case['category'])}</span>
            <span class="bt-badge">기술 · {escape(case['tech'])}</span>
            <span class="bt-badge">원인 유형 · {escape(case['cause_type'])}</span>
        </div>
        <h2>{escape(case['title'])}</h2>
        <div class="bt-card-nick">“{escape(case['nickname'])}” — {escape(case['summary'])}</div>
    """)


def show_symptom(case):
    """증상과 직접 관찰한 내용(있는 경우만)을 보여 준다."""
    render_html(f"""
        <div class="bt-box">
            <div class="bt-box-label">{icon("search")} SYMPTOM · 증상</div>
            <div>{escape(case['symptom'])}</div>
        </div>
    """)
    # observation이 null(None)이면 직접 관찰 상자는 그리지 않는다.
    if case["observation"]:
        render_html(f"""
            <div class="bt-box bt-obs">
                <div class="bt-box-label">OBSERVED · 직접 관찰</div>
                <div>{escape(case['observation'])}</div>
            </div>
        """)


def show_expected_vs_actual(case):
    """정상이라면 어떻게 되어야 하는지와 실제 결과를 나란히 비교한다."""
    render_html(f"""
        <div style="display:flex; gap:8px;">
            <div class="bt-box bt-ok" style="flex:1"><div class="bt-box-label">EXPECTED · 정상이라면</div>{escape(case['expected'])}</div>
            <div class="bt-box bt-err" style="flex:1"><div class="bt-box-label">ACTUAL · 실제로는</div>{escape(case['actual'])}</div>
        </div>
    """)


def show_flow(case):
    """오류가 생기는 흐름을 '입력 → 처리 → 출력' 세 칸 그림으로 보여 준다."""
    flow = case["flow"]       # {"input": "...", "process": "...", "output": "..."}
    # 출력 칸(bt-flow-out)은 벽돌색으로 그려서 '이상한 결과'임을 강조한다.
    render_html(f"""
        <div class="bt-box-label" style="color:var(--ink)">{icon("route")} PROCESS · 처리 과정</div>
        <div class="bt-flow">
            <div class="bt-flow-box">{icon("keyboard")}<div class="bt-flow-name">입력</div><div class="bt-flow-text">{escape(flow['input'])}</div></div>
            <div class="bt-flow-arrow">▶</div>
            <div class="bt-flow-box">{icon("settings")}<div class="bt-flow-name">처리</div><div class="bt-flow-text">{escape(flow['process'])}</div></div>
            <div class="bt-flow-arrow">▶</div>
            <div class="bt-flow-box bt-flow-out">{icon("error")}<div class="bt-flow-name">출력</div><div class="bt-flow-text">{escape(flow['output'])}</div></div>
        </div>
    """)


# -------------------------------------------------------------
# 3. 오른쪽 칸: 원인 추적 기록과 핵심 원리
# -------------------------------------------------------------

def basis_badge(basis):
    """단계마다 붙일 근거 이름표. 확인 = 공식 문서로 확인, 추정 = 아직 확인되지 않은 설명"""
    if basis == "확인":
        return '<span class="bt-basis bt-basis-ok">📘 문서로 확인</span>'
    return '<span class="bt-basis bt-basis-guess">🔎 추정</span>'


def show_steps(case):
    """오류가 생기는 원인을 #01 → #02 … 순서의 추적 기록으로 보여 준다."""
    render_html(f'<div class="bt-box-label" style="color:var(--ink)">{icon("troubleshoot")} TRACE · 원인 추적 기록</div>')
    # enumerate(목록, start=1): 번호(1, 2, 3...)와 단계 내용을 함께 꺼낸다.
    # 단계 하나는 {"basis": "확인" 또는 "추정", "text": "설명"} 형태의 딕셔너리다.
    for step_number, step in enumerate(case["steps"], start=1):
        render_html(f"""
            <div class="bt-box bt-step">
                <div class="bt-step-no">#{step_number:02d}</div>
                <div class="bt-step-text">{basis_badge(step['basis'])}<br>{escape(step['text'])}</div>
            </div>
        """)


def show_key_point(case):
    """오류의 핵심 원리를 한 문장으로 정리해서 보여 준다."""
    render_html(f"""
        <div class="bt-box bt-key">
            <div class="bt-box-label">💡 KEY POINT · 핵심 원리</div>
            <div>{escape(case['key_point'])}</div>
        </div>
    """)


# -------------------------------------------------------------
# 4. 아래 탭: 자주 생기는 곳 / 해결 방법 / 출처 / 관련 사례
# -------------------------------------------------------------

def show_bullets(items):
    """문장 목록을 글머리표 목록으로 보여 준다."""
    for item in items:
        st.markdown(f"- {item}")


def show_lab_link(case):
    """실험실에서 확인할 수 있는 오류라면 실험실로 가는 버튼을 보여 준다."""
    # case["lab"]이 null(None)이면 실험할 수 없는 오류라서 아무것도 안 보여 준다.
    if not case["lab"]:
        return
    if st.button("현상 실험실에서 직접 확인하기", icon=":material/science:", type="primary"):
        # 어떤 실험을 열지 저장해 두고 실험실로 이동한다.
        st.session_state["saved_lab"] = case["lab"]
        st.switch_page("pages/laboratory.py")


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
    """자세한 정보를 탭으로 나눠서 한 화면에 담는다. (스크롤을 줄이려고)"""
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


# ----- 실제 실행 순서 -----
all_cases = load_cases()

with crt_frame("pages/anatomy.py", "ANATOMY"):
    page_banner("layers", "ROOT CAUSE", "원인 해부실", "오류가 발생하는 내부 처리 과정을 한 단계씩 추적합니다.")
    show_case_selector(all_cases)                                               # 1) 오류 고르기
    current_case = find_case(all_cases, st.session_state["anatomy_case"])       # 고른 오류 데이터
    show_title(current_case)                                                    # 2) 제목

    left_column, right_column = st.columns([1, 1])                              # 3) 두 칸 배치
    with left_column:
        show_symptom(current_case)            # 증상 + 직접 관찰
        show_expected_vs_actual(current_case) # 정상 vs 실제
        show_flow(current_case)               # 처리 과정 그림
        show_lab_link(current_case)           # 실험실 연결 (실험 가능한 오류만)
    with right_column:
        show_steps(current_case)              # 원인 추적 기록
        show_key_point(current_case)          # 핵심 원리

    show_detail_tabs(all_cases, current_case)                                  # 4) 아래 탭
