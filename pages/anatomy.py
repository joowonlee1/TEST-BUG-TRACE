# =============================================================
# pages/anatomy.py  (원인 해부실)
# 오류 하나를 골라 증상 → 정상/실제 비교 → 발생 과정 → 핵심 →
# 자주 생기는 곳 → 해결 방법 → 관련 사례 순서로 자세히 보여 준다.
# =============================================================

from html import escape           # 글자 속 <, > 기호를 안전하게 바꾸는 함수

import streamlit as st

from common import case_label, find_case, icon, load_cases, page_header, render_html


# -------------------------------------------------------------
# 1. 선택한 오류 기억하기 (상태 관리)
# -------------------------------------------------------------

def restore_selected_case(case_ids):
    """홈이나 도감에서 고른 오류가 있으면 그 오류를 선택 상자에 넣는다."""
    # "anatomy_case"가 아직 없을 때(이 페이지에 처음 들어왔을 때)만 실행된다.
    # 저장된 번호가 없으면 첫 번째 오류(CASE 01)를 보여 준다.
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

    # format_func: 선택지에 번호 대신 "CASE 01 · 제목"처럼 보여 준다.
    st.selectbox(
        "사례 선택",
        case_ids,
        key="anatomy_case",
        format_func=lambda case_id: case_label(find_case(cases, case_id)),
        on_change=remember_case,
    )


# -------------------------------------------------------------
# 2. 오류 설명 화면 그리기
# -------------------------------------------------------------

def show_title(case):
    """번호, 분류, 기술, 원인 유형 이름표와 제목, 한 줄 요약을 보여 준다."""
    render_html(f"""
        <div style="margin-top: 14px;">
            <span class="bt-badge bt-badge-on">BUG-{case['id']:03d}</span>
            <span class="bt-badge">분류 · {escape(case['category'])}</span>
            <span class="bt-badge">기술 · {escape(case['tech'])}</span>
            <span class="bt-badge">원인 유형 · {escape(case['cause_type'])}</span>
        </div>
    """)
    st.markdown(f"## {case['title']}")
    st.markdown(f"> {case['summary']}")       # > 는 인용문(강조 상자) 표시


def show_symptom(case):
    """어떤 현상이 생기는지(증상)를 보여 준다."""
    st.markdown("### 🔍 증상")
    st.markdown(case["symptom"])


def show_expected_vs_actual(case):
    """정상이라면 어떻게 되어야 하는지와 실제 결과를 나란히 비교한다."""
    expected_column, actual_column = st.columns(2)
    with expected_column:                     # 왼쪽: 정상 동작 (초록)
        render_html(f"""
            <div class="bt-box bt-ok">
                <div class="bt-box-label">EXPECTED · 정상이라면</div>
                <div>{escape(case['expected'])}</div>
            </div>
        """)
    with actual_column:                       # 오른쪽: 실제 동작 (빨강)
        render_html(f"""
            <div class="bt-box bt-err">
                <div class="bt-box-label">ACTUAL · 실제로는</div>
                <div>{escape(case['actual'])}</div>
            </div>
        """)


def show_observation(case):
    """직접 관찰한 내용이 있으면 따로 보여 준다. (관찰과 추정을 구분하기 위해)"""
    # observation이 null(None)이면 아무것도 보여 주지 않는다.
    if not case["observation"]:
        return
    render_html(f"""
        <div class="bt-box bt-obs">
            <div class="bt-box-label">OBSERVED · 직접 관찰</div>
            <div>{escape(case['observation'])}</div>
        </div>
    """)


def show_flow(case):
    """오류가 생기는 흐름을 '입력 → 처리 → 출력' 세 칸 그림으로 보여 준다."""
    st.markdown("### 🧭 처리 과정")
    flow = case["flow"]       # {"input": "...", "process": "...", "output": "..."}
    # 화살표(→)로 세 칸을 이어서 컴퓨터 안에서 데이터가 지나가는 길을 표현한다.
    # 출력 칸(bt-flow-out)은 빨간색으로 그려서 '이상한 결과'임을 강조한다.
    render_html(f"""
        <div class="bt-flow">
            <div class="bt-flow-box">
                {icon("keyboard")}
                <div class="bt-flow-name">입력</div>
                <div class="bt-flow-text">{escape(flow['input'])}</div>
            </div>
            <div class="bt-flow-arrow">→</div>
            <div class="bt-flow-box">
                {icon("settings")}
                <div class="bt-flow-name">처리</div>
                <div class="bt-flow-text">{escape(flow['process'])}</div>
            </div>
            <div class="bt-flow-arrow">→</div>
            <div class="bt-flow-box bt-flow-out">
                {icon("description")}
                <div class="bt-flow-name">출력</div>
                <div class="bt-flow-text">{escape(flow['output'])}</div>
            </div>
        </div>
    """)


def basis_badge(basis):
    """단계마다 붙일 근거 이름표를 만든다. 확인 = 공식 문서로 확인, 추정 = 아직 확인되지 않은 설명"""
    if basis == "확인":
        return '<span class="bt-basis bt-basis-ok">📘 문서로 확인</span>'
    return '<span class="bt-basis bt-basis-guess">🔎 추정</span>'


def show_steps(case):
    """오류가 생기는 과정을 01 → 02 → 03 순서의 흐름으로 보여 준다."""
    st.markdown("### ⚙️ 원인 추적: 단계별 기록")
    st.caption("📘 문서로 확인 = 아래 출처의 공식 문서로 확인한 내용 · 🔎 추정 = 공식 설명이 없어 추정한 내용")
    steps = case["steps"]
    # enumerate(목록, start=1): 번호(1, 2, 3...)와 단계 내용을 함께 꺼낸다.
    # 단계 하나는 {"basis": "확인" 또는 "추정", "text": "설명"} 형태의 딕셔너리다.
    for step_number, step in enumerate(steps, start=1):
        render_html(f"""
            <div class="bt-box bt-step">
                <div class="bt-step-no">#{step_number:02d}</div>
                <div class="bt-step-text">{basis_badge(step['basis'])}<br>{escape(step['text'])}</div>
            </div>
        """)
        # 마지막 단계가 아니면 다음 단계로 가는 화살표를 그린다.
        if step_number < len(steps):
            render_html('<div class="bt-arrow">▼</div>')


def show_key_point(case):
    """오류의 핵심 원리를 한 문장으로 정리해서 보여 준다."""
    render_html(f"""
        <div class="bt-box bt-key">
            <div class="bt-box-label">💡 KEY POINT · 핵심 원리</div>
            <div>{escape(case['key_point'])}</div>
        </div>
    """)


def show_where(case):
    """이 오류가 자주 생기는 곳을 목록으로 보여 준다."""
    st.markdown("### 📍 어디서 자주 생기나")
    for place in case["where"]:
        st.markdown(f"- {place}")              # - 는 글머리표 목록


def show_fixes(case):
    """해결 방법을 '사용자'와 '개발자' 탭으로 나누어 보여 준다."""
    st.markdown("### 🛠️ 해결 방법")
    user_tab, developer_tab = st.tabs(["사용자가 할 수 있는 것", "개발자가 할 수 있는 것"])
    with user_tab:
        for fix in case["fix_user"]:
            st.markdown(f"- {fix}")
    with developer_tab:
        for fix in case["fix_dev"]:
            st.markdown(f"- {fix}")


def show_lab_link(case):
    """실험실에서 확인할 수 있는 오류라면 실험실로 가는 버튼을 보여 준다."""
    # case["lab"]이 null(None)이면 실험할 수 없는 오류라서 아무것도 안 보여 준다.
    if not case["lab"]:
        return
    st.info("이 오류는 현상 실험실에서 실제 계산 결과로 확인할 수 있어요.")
    if st.button("🧪 현상 실험실에서 확인하기"):
        # 어떤 실험을 열지 저장해 두고 실험실로 이동한다.
        st.session_state["saved_lab"] = case["lab"]
        st.switch_page("pages/laboratory.py")


def show_sources(case):
    """설명의 근거가 된 공식 문서 목록을 링크로 보여 준다."""
    st.markdown("### 📚 출처")
    for source in case["sources"]:
        # [글자](주소) → 마크다운 링크. 누르면 새 탭에서 문서가 열린다.
        st.markdown(f"- [{source['title']}]({source['url']})")


def show_related_cases(cases, case):
    """관련 사례 버튼을 보여 주고, 누르면 그 오류로 바뀐다."""
    st.markdown("### 🔗 관련 사례")
    columns = st.columns(len(case["related"]))
    for column, related_id in zip(columns, case["related"]):
        related_case = find_case(cases, related_id)
        with column:
            # on_click=함수, args=(함수에 넘길 값,) → 버튼을 누르면 move_to_case(번호) 실행
            st.button(
                case_label(related_case),
                key=f"related_{related_id}",
                on_click=move_to_case,
                args=(related_id,),
                width="stretch",
            )


# ----- 실제 실행 순서 -----
all_cases = load_cases()
page_header("layers", "원인 해부실", "오류가 발생하는 내부 처리 과정을 한 단계씩 추적합니다.")
show_case_selector(all_cases)                                    # 1) 오류 고르기

current_case = find_case(all_cases, st.session_state["anatomy_case"])  # 고른 오류 데이터

show_title(current_case)                 # 2) 제목과 요약
show_symptom(current_case)               # 3) 증상
show_observation(current_case)           # 4) 직접 관찰 (있는 경우만)
show_expected_vs_actual(current_case)    # 5) 정상 vs 실제
show_flow(current_case)                  # 5-1) 처리 과정 그림 (입력 → 처리 → 출력)
show_steps(current_case)                 # 6) 단계별 추적 기록 (확인 / 추정 표시)
show_key_point(current_case)             # 7) 핵심 정리
show_where(current_case)                 # 8) 자주 생기는 곳
show_fixes(current_case)                 # 9) 해결 방법
show_lab_link(current_case)              # 10) 실험실 연결
show_sources(current_case)               # 11) 출처
show_related_cases(all_cases, current_case)   # 12) 관련 사례
