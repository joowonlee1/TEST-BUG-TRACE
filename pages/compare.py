# =============================================================
# pages/compare.py  (오류 비교실)
# 두 오류를 골라 증상과 원리를 나란히 비교하고,
# 원인 유형·분류·키워드로 공통점과 차이점을 찾아 준다.
# =============================================================

from html import escape

import streamlit as st

from common import CAUSE_TYPES, case_label, crt_frame, find_case, load_cases, open_case, page_banner, render_html

# 처음 들어왔을 때 비교할 두 오류: 같은 '표현의 한계' 유형인 BUG-001(정수)과 BUG-002(실수)
# → "정수에서 배운 비트 표현이 실수에서는 어떻게 될까?"라는 탐구 출발점을 바로 비교한다
DEFAULT_LEFT_ID = 1
DEFAULT_RIGHT_ID = 2


# -------------------------------------------------------------
# 1. 비교할 오류 고르기 (상태 관리)
# -------------------------------------------------------------

def restore_choices():
    """저장해 둔 비교 대상을 선택 상자에 다시 넣는다."""
    if "compare_left" not in st.session_state:
        st.session_state["compare_left"] = st.session_state.get("saved_left", DEFAULT_LEFT_ID)
    if "compare_right" not in st.session_state:
        st.session_state["compare_right"] = st.session_state.get("saved_right", DEFAULT_RIGHT_ID)


def save_choices():
    """비교 대상이 바뀔 때마다 저장한다."""
    st.session_state["saved_left"] = st.session_state["compare_left"]
    st.session_state["saved_right"] = st.session_state["compare_right"]


def choose_pair(left_id, right_id):
    """추천 조합 버튼을 누르면 두 선택 상자의 값을 바꾼다."""
    st.session_state["compare_left"] = left_id
    st.session_state["compare_right"] = right_id
    save_choices()


def show_selectors(cases):
    """비교할 두 오류를 고르는 선택 상자를 보여 준다."""
    restore_choices()
    case_ids = [case["id"] for case in cases]

    def label(case_id):
        """선택지에 보여 줄 이름"""
        return case_label(find_case(cases, case_id))

    left_column, right_column = st.columns(2)
    with left_column:
        st.selectbox("사례 A", case_ids, key="compare_left", format_func=label, on_change=save_choices)
    with right_column:
        st.selectbox("사례 B", case_ids, key="compare_right", format_func=label, on_change=save_choices)


# -------------------------------------------------------------
# 2. 나란히 비교하기
# -------------------------------------------------------------

def case_header(case):
    """비교 칸 맨 위: 이름표 + 전문용어 제목 + 쉬운 이름"""
    return f"""
        <div class="bt-box">
            <span class="bt-badge bt-badge-on">BUG-{case['id']:03d}</span>
            <span class="bt-badge">{escape(case['category'])}</span>
            <span class="bt-badge">{escape(case['cause_type'])}</span>
            <h3>{escape(case['title'])}</h3>
            <div class="bt-card-nick">“{escape(case["nickname"])}” · {escape(case['tech'])}</div>
        </div>
    """


def show_side_by_side(left_case, right_case):
    """두 오류를 왼쪽·오른쪽에 나란히 보여 준다. 같은 줄의 상자는 높이가 똑같이 맞춰진다."""
    # CSS 격자(grid) 2칸: 제목 → 증상 → 핵심 원리를 한 줄씩 쌓으면, 한 줄 안의 두 상자 높이가 같아진다.
    cells = ""
    for left_html, right_html in [
        (case_header(left_case), case_header(right_case)),
        (f'<div class="bt-box"><div class="bt-box-label">SYMPTOM · 증상</div>{escape(left_case["symptom"])}</div>',
         f'<div class="bt-box"><div class="bt-box-label">SYMPTOM · 증상</div>{escape(right_case["symptom"])}</div>'),
        (f'<div class="bt-box bt-key"><div class="bt-box-label">💡 KEY POINT · 핵심 원리</div><b>{escape(left_case["key_point"])}</b></div>',
         f'<div class="bt-box bt-key"><div class="bt-box-label">💡 KEY POINT · 핵심 원리</div><b>{escape(right_case["key_point"])}</b></div>'),
    ]:
        cells += left_html + right_html
    render_html(f'<div class="cmp-grid">{cells}</div>')
    # 버튼은 상자들 아래에 따로 한 줄로 놓아서 두 버튼이 항상 같은 높이에 오게 한다.
    left_button, right_button = st.columns(2)
    with left_button:
        if st.button(f"BUG-{left_case['id']:03d} 원인 추적 ▶", key="compare_open_left", width="stretch"):
            open_case(left_case["id"])
    with right_button:
        if st.button(f"BUG-{right_case['id']:03d} 원인 추적 ▶", key="compare_open_right", width="stretch"):
            open_case(right_case["id"])

# -------------------------------------------------------------
# 3. 공통점과 차이점 분석
# -------------------------------------------------------------

def find_common_keywords(left_case, right_case):
    """두 오류의 키워드 중 겹치는 것을 찾는다."""
    # set(집합)으로 바꾸고 & 연산을 하면 양쪽에 모두 있는 값만 남는다. (교집합)
    return sorted(set(left_case["keywords"]) & set(right_case["keywords"]))


# 두 사례의 공통점과 차이점을 계산하는 비교 기능이다.
# 화면 배치는 별도 함수에서 담당해 비교 로직과 출력 코드를 구분한다.

def compare_cases(left_case, right_case):
    """두 오류를 비교해서 (공통점 목록, 차이점 목록)을 만든다."""
    same = []        # 공통점
    different = []   # 차이점

    # (1) 원인 유형
    if left_case["cause_type"] == right_case["cause_type"]:
        cause = left_case["cause_type"]
        same.append(f"두 오류 모두 **'{cause}'** 유형이에요. {CAUSE_TYPES[cause]}.")
    else:
        different.append(
            f"원인 유형이 달라요. A는 **{left_case['cause_type']}**, B는 **{right_case['cause_type']}**이에요."
        )

    # (2) 분류
    if left_case["category"] == right_case["category"]:
        same.append(f"두 오류 모두 **{left_case['category']}** 분류에 속해요.")
    else:
        different.append(f"A는 **{left_case['category']}** 분류, B는 **{right_case['category']}** 분류예요.")

    # (3) 겹치는 키워드
    common_keywords = find_common_keywords(left_case, right_case)
    if common_keywords:
        same.append(f"겹치는 키워드: **{', '.join(common_keywords)}**")

    # (4) 서로 관련 사례로 연결되어 있는지
    if right_case["id"] in left_case["related"] or left_case["id"] in right_case["related"]:
        same.append("두 오류는 서로 **관련 사례**로 연결되어 있어요.")

    # (5) 사용하는 기술은 언제나 차이점에 넣는다
    different.append(f"관련 기술: A는 **{left_case['tech']}**, B는 **{right_case['tech']}**")

    return same, different


def show_analysis(left_case, right_case):
    """공통점과 차이점을 탭으로 나누어 체크 목록으로 보여 준다."""
    # 같은 오류를 두 번 고른 경우
    if left_case["id"] == right_case["id"]:
        st.warning("같은 오류를 골랐어요. 서로 다른 두 오류를 골라 보세요.")
        return

    same, different = compare_cases(left_case, right_case)
    same_tab, different_tab = st.tabs([f"공통점 ({len(same)})", f"차이점 ({len(different)})"])
    with same_tab:
        if not same:
            st.markdown("- 뚜렷한 공통점이 없어요. 원인이 서로 다른 오류예요.")
        for item in same:
            st.markdown(f"✅ {item}")
    with different_tab:
        for item in different:
            st.markdown(f"↔️ {item}")


# -------------------------------------------------------------
# 4. 원인 유형별 묶음 (추천 비교 조합)
# -------------------------------------------------------------

def group_by_cause(cases):
    """원인 유형마다 해당하는 오류들을 묶는다. 예) {"표현의 한계": [오류1, 오류2], ...}"""
    groups = {}
    for cause in CAUSE_TYPES:
        groups[cause] = []
    for case in cases:
        groups[case["cause_type"]].append(case)
    return groups


def show_cause_groups(cases):
    """같은 원인 유형의 오류끼리 묶어서 보여 주고, 버튼으로 바로 비교할 수 있게 한다."""
    st.markdown("### 🗂️ 같은 원인, 다른 증상")
    st.caption("겉으로는 전혀 달라 보여도 원인이 같은 오류들이에요. 버튼을 누르면 바로 비교해요.")

    groups = group_by_cause(cases)
    columns = st.columns(3)
    # enumerate로 순서(0, 1, 2...)를 받아서 세 칸에 차례로 넣는다.
    for order, (cause, group_cases) in enumerate(groups.items()):
        with columns[order % 3]:                # 0,3번째는 첫째 칸 / 1,4번째는 둘째 칸 / 2,5번째는 셋째 칸
            with st.container(border=True):
                # 원인 유형 이름 + 설명 + 해당 오류 목록을 한 번에 그린다.
                case_lines = "".join(f"<div>· {escape(case_label(case))}</div>" for case in group_cases)
                render_html(f"""
                    <div class="bt-box-label" style="color:var(--ink)">{escape(cause)}</div>
                    <div style="font-size:0.85rem;color:var(--dim)">{escape(CAUSE_TYPES[cause])}</div>
                    <div style="font-size:0.88rem;margin-top:4px">{case_lines}</div>
                """)
                # 오류가 2개 이상인 유형만 비교 버튼을 보여 준다.
                if len(group_cases) >= 2:
                    st.button(
                        "이 두 오류 비교",
                        key=f"pair_{cause}",
                        on_click=choose_pair,
                        args=(group_cases[0]["id"], group_cases[1]["id"]),
                        icon=":material/balance:",
                        width="stretch",
                    )


# 비교 격자 디자인: 2칸, 같은 줄의 상자는 높이를 맞춘다 (상자 안 여백 정리)
COMPARE_STYLE = "<style>.cmp-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 14px; } .cmp-grid .bt-box { margin: 0; } .cmp-grid h3 { margin: 6px 0 0 !important; }</style>"


# ----- 실제 실행 순서 -----
all_cases = load_cases()
render_html(COMPARE_STYLE)

with crt_frame("pages/compare.py", "COMPARE"):
    page_banner("compare_arrows", "ERROR COMPARE", "오류 비교실", "두 오류의 공통점과 차이점을 나란히 비교합니다.")
    show_selectors(all_cases)                                          # 1) 두 오류 고르기
    case_a = find_case(all_cases, st.session_state["compare_left"])    # 왼쪽 오류 데이터
    case_b = find_case(all_cases, st.session_state["compare_right"])   # 오른쪽 오류 데이터
    show_side_by_side(case_a, case_b)        # 2) 나란히 비교
    show_analysis(case_a, case_b)            # 3) 공통점·차이점 분석 (탭)
    show_cause_groups(all_cases)             # 4) 원인 유형별 묶음
