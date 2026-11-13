# =============================================================
# pages/compare.py  (오류 비교실)
# 정수(BUG-001)와 실수(BUG-002)를 항목별로 나란히 비교하고,
# 오버플로·언더플로가 정수와 실수에서 각각 어떻게 다른지 2×2 칸으로 정리한다.
# =============================================================

from html import escape

import streamlit as st

from common import CAUSE_TYPES, crt_frame, find_case, icon, load_cases, open_case, page_banner, render_html

INTEGER_ID = 1    # 정수 사례 번호
FLOAT_ID = 2      # 실수 사례 번호

# 비교 항목: (항목 이름, 정수 쪽 설명, 실수 쪽 설명)
COMPARE_ROWS = [
    ("저장하는 수", "소수점이 없는 수 (예: 조회수, 점수, 초)", "소수점이 있는 수 (예: 0.1, 3.14, 확률)"),
    ("칸 나누는 방법", "32칸 전부 수 하나 (맨 앞 1칸 = 부호 비트)", "64칸을 부호 1 · 지수 11 · 가수 52로 나눔"),
    ("음수 표현", "2의 보수 (뒤집고 1 더하기)", "부호 칸 하나만 1로 바꿈"),
    ("담을 수 있는 범위", "-2,147,483,648 ~ 2,147,483,647 (32비트)", "약 ±1.8 × 10³⁰⁸ 까지, 0에 가장 가까운 수는 약 4.9 × 10⁻³²⁴"),
    ("한계를 넘으면", "반대쪽 끝으로 넘어감 (최댓값 + 1 → 최솟값)", "너무 크면 inf(무한대), 너무 작으면 0이 됨"),
    ("범위 안에서도 생기는 문제", "없음 (범위 안의 정수는 정확함)", "끝없는 2진 소수를 잘라서 생기는 반올림 오차"),
    ("대표 사례", "2038년 문제, 강남스타일 조회수, 보잉 787 248일", "0.1 + 0.2 = 0.30000000000000004"),
    ("해결 방법", "64비트로 늘리기, 계산 전에 범위 검사", "오차 범위로 비교, 10진수 자료형(Decimal), 로그로 바꿔 계산"),
]


def show_case_heads(integer_case, float_case):
    """맨 위: 두 사례의 이름과 원인 유형을 나란히 보여 준다."""
    heads = ""
    for case in (integer_case, float_case):
        heads += f"""
            <div class="bt-box">
                <span class="bt-badge bt-badge-on">BUG-{case['id']:03d}</span>
                <span class="bt-badge">{escape(case['category'])}</span>
                <span class="bt-badge">{escape(case['cause_type'])}</span>
                <h3>{escape(case['title'])}</h3>
                <div class="bt-card-nick">“{escape(case['nickname'])}”</div>
                <div class="cmp-cause">{escape(CAUSE_TYPES[case['cause_type']])}</div>
            </div>
        """
    render_html(f'<div class="cmp-heads">{heads}</div>')


def show_compare_table():
    """비교 항목을 '항목 | 정수 | 실수' 3칸 표로 보여 준다. 한 줄의 칸 높이는 똑같이 맞춰진다."""
    rows = '<div class="cmp-cell cmp-th">항목</div><div class="cmp-cell cmp-th">정수 (BUG-001)</div><div class="cmp-cell cmp-th">실수 (BUG-002)</div>'
    for name, integer_text, float_text in COMPARE_ROWS:
        rows += (f'<div class="cmp-cell cmp-name">{escape(name)}</div>'
                 f'<div class="cmp-cell">{escape(integer_text)}</div>'
                 f'<div class="cmp-cell">{escape(float_text)}</div>')
    render_html(f'<div class="sec-label">{icon("table_chart")} TABLE · 항목별 비교</div><div class="cmp-table">{rows}</div>')


# 오버플로·언더플로 4가지: (제목, 상자 색, 설명, 예시 계산, 원인)
FLOW_CELLS = {
    ("정수", "오버플로"): ("넘어간다", "bt-err", "최댓값보다 커지면 가장 작은 음수로 넘어가요.",
                          "2,147,483,647 + 1 → -2,147,483,648", "받아올림이 부호 비트까지 올라가 0이 1로 바뀜"),
    ("정수", "언더플로"): ("넘어간다", "bt-err", "최솟값보다 작아지면 가장 큰 양수로 넘어가요.",
                          "-2,147,483,648 − 1 → 2,147,483,647", "빌림 때문에 부호 비트가 1에서 0으로 바뀜"),
    ("실수", "오버플로"): ("무한대가 된다", "bt-obs", "절댓값이 너무 커지면(약 1.8 × 10³⁰⁸ 초과) inf(무한대)가 돼요.",
                          "1.8e308 × 10 → inf", "지수 칸(11비트)으로 더 큰 지수를 나타낼 수 없음"),
    ("실수", "언더플로"): ("0이 된다", "bt-obs", "0에 너무 가까워지면 정밀도를 잃다가(비정규 수) 0이 돼요.",
                          "4.9 × 10⁻³²⁴ ÷ 2 → 0.0", "지수 칸으로 더 작은 지수를 나타낼 수 없음"),
}


def flow_cell(kind, flow):
    """오버플로·언더플로 표의 칸 하나를 HTML로 만든다."""
    result, box_class, text, example, cause = FLOW_CELLS[(kind, flow)]
    return f"""
        <div class="bt-box {box_class}">
            <div class="bt-box-label">{kind} {flow} = {result}</div>
            {escape(text)}<br><code>{escape(example)}</code><br>
            <span class="cmp-cause">원인: {escape(cause)}</span>
        </div>
    """


def show_flow_matrix():
    """오버플로와 언더플로를 정수·실수 각각에서 2×2 칸으로 비교한다."""
    render_html(f"""
        <div class="sec-label">{icon("grid_view")} OVER / UNDER · 오버플로와 언더플로, 정수와 실수에서</div>
        <div class="bt-box bt-key">
            <div class="bt-box-label">💡 한 줄 정리</div>
            <b>정수</b>에서는 <b>최댓값과 최솟값</b>이 경계이고, <b>부동소수점</b>에서는 값의 <b>절댓값이 너무 크거나 0에 너무 가까울 때</b> 문제가 생겨요.
        </div>
        <div class="cmp-matrix">
            <div></div><div class="cmp-cell cmp-th">오버플로 (너무 큼)</div><div class="cmp-cell cmp-th">언더플로 (너무 작음)</div>
            <div class="cmp-cell cmp-name">정수</div>{flow_cell("정수", "오버플로")}{flow_cell("정수", "언더플로")}
            <div class="cmp-cell cmp-name">실수</div>{flow_cell("실수", "오버플로")}{flow_cell("실수", "언더플로")}
        </div>
        <div class="cmp-note">※ 정수에서 최솟값 아래로 넘는 것도 넓게 '오버플로'라고 부르기도 해요. 이 연구소에서는 방향을 구분하려고 '언더플로'라고 불러요.</div>
    """)


def show_open_buttons():
    """두 사례의 원인 해부실로 가는 버튼을 한 줄에 놓는다."""
    integer_column, float_column = st.columns(2)
    if integer_column.button("BUG-001 원인 추적 ▶", key="compare_open_int", width="stretch"):
        open_case(INTEGER_ID)
    if float_column.button("BUG-002 원인 추적 ▶", key="compare_open_float", width="stretch"):
        open_case(FLOAT_ID)


# 비교 화면 디자인: 2칸 격자(사례 제목, 언더플로)와 3칸 표
COMPARE_STYLE = """
<style>
.cmp-heads { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 14px; margin-bottom: 8px; }
.cmp-heads .bt-box { margin: 0; }
.cmp-heads h3 { margin: 6px 0 0 !important; }
.cmp-cause { font-size: 0.92rem; color: var(--dim); }
.cmp-table { display: grid; grid-template-columns: 0.8fr 1.6fr 1.6fr; border: 3px solid var(--ink); background: var(--paper); margin-bottom: 8px; }
.cmp-cell { padding: 8px 12px; border-bottom: 2px solid #C9D9A6; border-right: 2px solid #C9D9A6; font-size: 0.97rem; line-height: 1.6; }
.cmp-th { background: var(--lime); font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); border-bottom: 3px solid var(--ink); }
.cmp-name { font-weight: 800; color: var(--ink); background: var(--lime-soft); }
.cmp-matrix { display: grid; grid-template-columns: 90px 1fr 1fr; gap: 8px; align-items: stretch; margin-bottom: 4px; }
.cmp-matrix .bt-box { margin: 0; }
.cmp-matrix .cmp-name { display: flex; align-items: center; justify-content: center; border: 3px solid var(--ink); font-family: 'Galmuri11', sans-serif; }
.cmp-matrix .cmp-th { border: 3px solid var(--ink); text-align: center; }
.cmp-note { font-size: 0.88rem; color: var(--dim); margin: 6px 0 8px; }
@media (max-width: 800px) { .cmp-heads, .cmp-table, .cmp-matrix { grid-template-columns: 1fr; } }
</style>
"""


# ----- 실제 실행 순서 -----
all_cases = load_cases()
render_html(COMPARE_STYLE)

with crt_frame("pages/compare.py", "COMPARE"):
    page_banner("compare_arrows", "ERROR COMPARE", "오류 비교실", "정수와 실수, 두 사례의 같은 점과 다른 점을 나란히 비교합니다.")
    show_case_heads(find_case(all_cases, INTEGER_ID), find_case(all_cases, FLOAT_ID))   # 1) 두 사례 이름
    show_compare_table()                    # 2) 항목별 비교 표
    show_flow_matrix()                      # 3) 오버플로·언더플로 × 정수·실수 (2×2)
    show_open_buttons()                     # 4) 원인 해부실로 가는 버튼
