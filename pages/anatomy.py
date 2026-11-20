# =============================================================
# pages/anatomy.py  (원인 해부실)
# 오류 하나를 골라 위에서 아래로 '추적 순서'대로 분석한다.
#   ① 제목 → ② 핵심 원리(가장 크게) → ③ 먼저 알아 둘 용어 → ④ 증상 · 정상이라면 · 실제로는 (+ 직접 관찰)
#   → ⑤ 처리 과정(입력 → 처리 → 출력) → ⑥ 원인 추적 기록 #01~#05 (문서로 확인 = 누르면 문서가 열림 / 추정)
#   → ⑦ 관련 영상(있을 때만) → ⑧ 실험실 버튼 → ⑨ 출처 → ⑩ 탭: 자주 생기는 곳 / 해결 방법 / 관련 사례
# =============================================================

import re                         # 글자 규칙(정규식): **굵게** 표시를 찾을 때 사용
from html import escape           # 글자 속 <, > 기호를 안전하게 바꾸는 함수

import streamlit as st

from common import case_label, crt_frame, find_case, icon, load_cases, page_banner, render_html


# -------------------------------------------------------------
# 용어 카드의 '자세히 보기' 내용: 오류 사례를 반복하지 않고 저장 원리만 설명한다.
# (예전에는 아래쪽 '원리 이해하기' 접기 상자에 따로 있었는데, 용어 카드와 내용이 겹쳐서 카드 안 팝업으로 합쳤다)
# -------------------------------------------------------------

# **굵게** 표시를 찾는 규칙. (.+?) = 별표 사이의 글자를 가능한 한 짧게 찾는다
BOLD_PATTERN = re.compile(r"\*\*(.+?)\*\*")


def write_text(text):
    """문장을 보여 준다. **굵게**는 HTML <b>로 바꿔서, 한글 바로 앞에서도 별표가 그대로 보이지 않게 한다."""
    st.markdown(BOLD_PATTERN.sub(r"<b>\1</b>", text), unsafe_allow_html=True)


def topic_bits():
    """자세히 보기 ① 비트와 2진수: 2진수 자리 값과 13을 2진수로 바꾸는 예"""
    write_text(
        "**8비트 = 1바이트**이고, 8비트로 만들 수 있는 조합은 **256가지**예요.\n\n"
        "10진수는 오른쪽부터 1, 10, 100…의 자리 값을 쓰지만, "
        "2진수는 오른쪽부터 **1, 2, 4, 8, 16…**의 자리 값을 써요."
    )
    st.markdown("#### 13을 8비트 2진수로 표현하기")
    render_html("""
        <div class="btg-bits">
          <div><small>128</small><span>0</span></div><div><small>64</small><span>0</span></div>
          <div><small>32</small><span>0</span></div><div><small>16</small><span>0</span></div>
          <div class="active"><small>8</small><span>1</span></div><div class="active"><small>4</small><span>1</span></div>
          <div><small>2</small><span>0</span></div><div class="active"><small>1</small><span>1</span></div>
        </div>
        <div class="btg-result">8 + 4 + 1 = <strong>13</strong> <span>→ 00001101₂</span></div>
    """)
    write_text("반대로 `00001010`은 8과 2 자리에 1이 있으므로 **10**이에요.")


def topic_range():
    """자세히 보기 ② 비트 수와 범위: 조합 수와 실제로 담을 수 있는 범위의 차이"""
    write_text("비트 하나에는 0과 1, 두 가지 상태가 있어요. 그래서 **n비트의 전체 조합 수는 2ⁿ가지**예요.")
    render_html("""
        <div class="btg-table-wrap"><table class="btg-table">
        <thead><tr><th>비트 수</th><th>가능한 조합 수</th></tr></thead>
        <tbody>
        <tr><td>8비트</td><td>256가지 (2⁸)</td></tr>
        <tr><td>32비트</td><td>4,294,967,296가지 (2³²)</td></tr>
        <tr><td>64비트</td><td>18,446,744,073,709,551,616가지 (2⁶⁴)</td></tr>
        </tbody></table></div>
    """)
    write_text(
        "하지만 **조합 수가 곧 양수의 최댓값은 아니에요.** "
        "같은 8비트라도 부호 없는 정수는 **0~255**, 2의 보수로 표현한 부호 있는 정수는 "
        "**−128~127**을 나타내요. 둘 다 256가지 값이에요.\n\n"
        "이 범위의 끝을 넘으면 반대쪽 끝으로 넘어가요. 위로 넘치면 **오버플로**, 아래로 넘치면 **언더플로**예요."
    )


def topic_twos():
    """자세히 보기 ③ 음수와 2의 보수: 5를 −5로 바꾸는 과정과 비트 연산"""
    write_text(
        "비트에는 `−` 기호를 직접 적을 수 없어요. 그래서 부호 있는 정수는 **2의 보수** 규칙으로 읽어요. "
        "맨 앞 비트(부호 비트)가 0이면 0 이상, 1이면 음수예요."
    )
    st.markdown("#### 5를 −5로 바꾸기")
    render_html("""
        <div class="btg-twos">
          <div><b>① +5의 8비트</b><code>00000101</code></div>
          <div><b>② 0과 1 뒤집기</b><code>11111010</code></div>
          <div><b>③ 1 더하기</b><code>11111011</code></div>
        </div>
    """)
    write_text(
        "8비트 2의 보수에서 맨 앞 자리의 값은 **−128**, 나머지는 64, 32, 16, 8, 4, 2, 1이에요.\n\n"
        "`11111011` = −128 + 64 + 32 + 16 + 8 + 2 + 1 = **−5**\n\n"
        "그래서 8비트 부호 있는 정수의 범위는 **−128~127**이에요. 0이 양수 쪽 자리를 하나 차지해서 음수 쪽이 하나 더 많아요."
    )
    st.markdown("#### 비트 연산: 0과 1을 직접 다루는 계산")
    write_text(
        "**AND (`&`)** — 두 비트가 모두 1일 때만 1 · `1100 & 1010 = 1000`\n\n"
        "**XOR (`^`)** — 두 비트가 다를 때만 1 · `1100 ^ 1010 = 0110`\n\n"
        "**NOT (`~`)** — 0과 1을 모두 뒤집기 · `1100 → 0011` (2의 보수 ②단계)\n\n"
        "**왼쪽 밀기 (`<<`)** — 비트를 왼쪽으로 한 칸씩 옮기기 = 2를 곱하기 · `0011 << 1 = 0110`"
    )


def topic_fraction():
    """자세히 보기 ④ 2진 소수: 0.1이 2진수로 끝나지 않는 이유와 오차가 눈에 안 띄는 경우"""
    write_text("10진수는 소수점 아래가 1/10, 1/100… 순서이고, 2진수는 **1/2, 1/4, 1/8…** 순서예요.")
    render_html("""
        <div class="btg-table-wrap"><table class="btg-table btg-table-small">
        <thead><tr><th>2진수</th><th>10진수</th></tr></thead>
        <tbody><tr><td>0.1₂</td><td>0.5</td></tr><tr><td>0.01₂</td><td>0.25</td></tr><tr><td>0.11₂</td><td>0.75</td></tr></tbody>
        </table></div>
    """)
    write_text(
        "반면 **10진수 0.1**은 2진수로 `0.0001100110011…`처럼 끝없이 반복돼요. "
        "정해진 칸에 담으려면 가까운 값으로 반올림해야 해서 아주 작은 오차가 생겨요."
    )
    st.markdown("#### 그런데 왜 평소에는 오차가 잘 안 보일까요?")
    st.code(
        "print(0.5 + 0.25)       # 0.75\n"
        "print(0.1 + 0.3)        # 0.4\n"
        "print(0.1 + 0.2)        # 0.30000000000000004\n"
        "print(0.1 + 0.2 == 0.3) # False",
        language="python",
    )
    write_text(
        "`0.5`와 `0.25`는 2진수로 정확하게 저장돼요. `0.1`과 `0.3`은 정확하지 않지만, 출력할 때 반올림되어 `0.4`로 보여요. "
        "반면 `0.1 + 0.2`는 작은 차이가 화면에도 드러나요. 그래서 실수를 `==`로 비교하면 예상과 다른 결과가 나올 수 있어요."
    )


def topic_ieee():
    """자세히 보기 ⑤ 부동소수점과 IEEE 754: 부호·지수·가수와 정상 수·비정규 수"""
    st.markdown("#### 부동소수점(浮動小數點) — 소수점 위치를 움직이는 표현")
    write_text(
        "**부(浮)**는 뜨다, **동(動)**은 움직이다, **소수점(小數點)**은 숫자의 점을 뜻해요. "
        "소수점 위치를 옮기고 지수를 조정해 큰 수와 작은 수를 함께 나타내는 방식이에요. "
        "예를 들어 123.45 = 1.2345 × 10²이고, 컴퓨터는 이 원리를 2진수에 적용해요."
    )
    st.markdown("#### IEEE 754는 실수를 저장하는 대표적인 규칙이에요")
    write_text("64비트 실수는 칸을 **부호 · 지수 · 가수** 세 부분으로 나눠 저장해요.")
    render_html("""
        <div class="btg-table-wrap"><table class="btg-table">
        <thead><tr><th>부분</th><th>칸 수</th><th>하는 일</th></tr></thead>
        <tbody>
        <tr><td>부호</td><td>1</td><td>양수·음수 표시</td></tr>
        <tr><td>지수</td><td>11</td><td>수의 크기 조절 (2의 몇 제곱인지)</td></tr>
        <tr><td>가수</td><td>52</td><td>유효숫자 저장</td></tr>
        </tbody></table></div>
    """)
    write_text(
        "보통의 **정상 수**는 저장하지 않는 맨 앞 1비트까지 합쳐 **53비트의 정밀도**를 써요. "
        "0에 아주 가까워 지수 칸이 바닥에 닿으면 **비정규 수**가 되어 정밀도가 줄어들고, 그보다 작으면 0이 돼요. "
        "반대로 너무 커서 지수 칸이 넘치면 무한대(inf)가 돼요."
    )


# 자세히 보기 주제: 이름표 → (팝업 제목, 내용을 그리는 함수)
TOPICS = {
    "bits": ("비트와 2진수", topic_bits),
    "range": ("비트 수와 범위", topic_range),
    "twos": ("음수와 2의 보수, 비트 연산", topic_twos),
    "fraction": ("2진 소수", topic_fraction),
    "ieee": ("부동소수점과 IEEE 754", topic_ieee),
}

# 용어마다 열어 줄 자세히 보기 주제 (없는 용어는 카드 설명만으로 충분해서 버튼을 달지 않는다)
TERM_TOPICS = {
    "비트": "bits", "부호 비트": "twos", "2의 보수": "twos",
    "정수 오버플로": "range", "정수 언더플로": "range",
    "2진 소수": "fraction", "반올림 오차": "fraction",
    "부동소수점": "ieee", "IEEE 754": "ieee", "부동소수점 오버플로": "ieee",
    "부동소수점 언더플로": "ieee", "비정규 수": "ieee",
}


@st.dialog("자세히 보기", width="large")
def show_topic_dialog(topic_key):
    """용어 카드의 '자세히 보기'를 누르면 뜨는 팝업 창: 주제 제목과 내용을 보여 준다."""
    title, draw_topic = TOPICS[topic_key]
    st.markdown(f"### {title}")
    draw_topic()


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
    """분석할 사례를 고르는 버튼(라디오)을 보여 준다. 사례가 2개라 펼쳐 놓아야 한눈에 보인다."""
    case_ids = [case["id"] for case in cases]   # [1, 2]
    restore_selected_case(case_ids)
    # key="case_pick": 라임색 띠 상자 (CSS로 눈에 띄게 꾸민다)
    # 안내 글과 사례 버튼을 한 줄에 놓아서 세로 공간을 아낀다.
    with st.container(key="case_pick", horizontal=True, vertical_alignment="center"):
        render_html('<div class="pick-label">🔎 분석할 사례</div>')
        # format_func: 선택지에 번호 대신 "BUG-001 · 제목"처럼 보여 준다.
        st.radio(
            "분석할 사례",
            case_ids,
            key="anatomy_case",
            format_func=lambda case_id: case_label(find_case(cases, case_id)),
            on_change=remember_case,
            horizontal=True,
            label_visibility="collapsed",
        )


# -------------------------------------------------------------
# 2. 화면 위쪽: 제목, 증상 비교, 처리 과정
# -------------------------------------------------------------

def section_label(icon_name, title):
    """각 구역 위에 붙는 작은 제목. 예) ⚙ 컴퓨터 안에서 일어난 일"""
    return f'<div class="sec-label">{icon(icon_name)} {title}</div>'


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
                <div class="bt-box-label">{icon("visibility")} 직접 관찰</div>{escape(case['observation'])}
            </div>
        """
    render_html(f"""
        {section_label("search", "어떤 현상인가")}
        <div class="an-grid3">
            <div class="bt-box"><div class="bt-box-label">증상</div>{escape(case['symptom'])}</div>
            <div class="bt-box bt-ok"><div class="bt-box-label">정상이라면</div>{escape(case['expected'])}</div>
            <div class="bt-box bt-err"><div class="bt-box-label">실제로는</div>{escape(case['actual'])}</div>
        </div>
        {observed}
    """)


def show_flow(case):
    """③ 오류가 생기는 흐름을 '입력 → 처리 → 출력' 세 칸 그림으로 보여 준다."""
    flow = case["flow"]       # {"input": "...", "process": "...", "output": "..."}
    # 출력 칸(bt-flow-out)은 벽돌색으로 그려서 '이상한 결과'임을 강조한다.
    render_html(f"""
        {section_label("route", "컴퓨터 안에서 일어난 일")}
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

def basis_badge(case, step):
    """단계마다 붙일 근거 이름표. 확인 = 누르면 그 근거 문서가 새 탭에서 열린다 / 추정 = 아직 확인되지 않은 설명"""
    if step["basis"] == "확인" and step["source"] is not None:
        source = case["sources"][step["source"]]          # 이 단계의 근거 문서 (출처 목록에서 몇 번째인지 데이터에 적혀 있음)
        # target="_blank": 새 탭에서 열기 / title: 마우스를 올리면 문서 이름이 보인다
        return (f'<a class="bt-basis bt-basis-ok" href="{escape(source["url"])}" target="_blank" '
                f'title="{escape(source["title"])}">📘 문서로 확인 ↗</a>')
    return '<span class="bt-basis bt-basis-guess">🔎 추정</span>'


def group_steps(steps):
    """바로 이어지는 단계가 같은 근거 문서를 가리키면 한 묶음으로 합친다.
    예) #01·#02가 둘 다 '2의 보수' 문서 → 카드 하나에 두 문장. 결과: [[단계, 단계], [단계], ...]"""
    groups = []
    for step in steps:
        same_source = groups and groups[-1][-1]["source"] == step["source"] and groups[-1][-1]["basis"] == step["basis"]
        if same_source and step["source"] is not None:
            groups[-1].append(step)              # 앞 묶음과 같은 문서 → 그 묶음에 붙인다
        else:
            groups.append([step])                # 다른 문서 → 새 묶음을 시작한다
    return groups


def show_steps(case):
    """④ 원인을 #01 → #02 … 순서의 추적 카드로 가로로 나란히 보여 준다. 같은 문서를 근거로 한 단계는 한 카드로 합친다."""
    cards = ""
    # enumerate(목록, start=1): 번호(1, 2, 3...)와 단계 묶음을 함께 꺼낸다.
    # 단계 하나는 {"basis": "확인" 또는 "추정", "source": 문서 번호, "text": "설명"} 형태의 딕셔너리다.
    for step_number, group in enumerate(group_steps(case["steps"]), start=1):
        texts = "".join(f'<p>{escape(step["text"])}</p>' for step in group)
        cards += f"""
            <div class="an-step">
                <div class="an-step-head"><span class="bt-step-no">#{step_number:02d}</span>{basis_badge(case, group[0])}</div>
                <div class="an-step-text">{texts}</div>
            </div>
        """
    render_html(f"""
        {section_label("troubleshoot", "원인 추적 기록")}
        <div class="an-steps">{cards}</div>
    """)


def show_key_point(case):
    """② 오류의 핵심 원리를 한 문장으로, 페이지에서 가장 눈에 띄게 보여 준다."""
    render_html(f"""
        <div class="bt-keypoint">
            {icon("lightbulb")}
            <div><div class="bt-keypoint-label">이것만 기억하세요</div>
            <div class="bt-keypoint-text">{escape(case['key_point'])}</div></div>
        </div>
    """)


def show_terms(case):
    """③ 먼저 알아 둘 용어를 한 줄 카드로 보여 준다. 설명이 더 필요한 용어는 '자세히 보기'로 팝업을 연다."""
    render_html(section_label("menu_book", "먼저 알아 둘 용어 · 더 궁금하면 '자세히 보기'"))
    terms = case["terms"]
    with st.container(key="term_row"):
        columns = st.columns(len(terms), gap="small")          # 용어 수만큼 칸을 만들어 한 줄에 놓는다
        for number, (column, term) in enumerate(zip(columns, terms)):
            with column, st.container(key=f"term_card_{number}"):
                render_html(f'<div class="bt-term-name">{escape(term["term"])}</div>'
                            f'<div class="bt-term-desc">{escape(term["desc"])}</div>')
                topic = TERM_TOPICS.get(term["term"])            # 이 용어와 연결된 자세히 보기 주제 (없으면 None)
                if topic and st.button("자세히 보기", key=f"term_more_{number}", width="stretch"):
                    show_topic_dialog(topic)


def show_sources(case):
    """⑧ 근거가 된 공식 문서 목록 (누르면 새 탭에서 열린다)"""
    items = ""
    for number, source in enumerate(case["sources"], start=1):
        items += f'<li><a href="{escape(source["url"])}" target="_blank">{escape(source["title"])} ↗</a></li>'
    render_html(f'{section_label("library_books", "출처")}<div class="bt-box"><ol class="an-sources">{items}</ol></div>')


def show_video(case):
    """⑦ 관련 영상: 데이터에 video가 있는 사례에서만 YouTube 영상을 바로 재생할 수 있게 넣는다."""
    video = case["video"]               # {"title": "...", "url": "..."} 또는 None
    render_html(section_label("smart_display", "영상으로 한 번 더"))
    video_column, guide_column = st.columns([3, 2], vertical_alignment="center")
    with video_column:
        st.video(video["url"])          # st.video: YouTube 주소를 넣으면 화면 안에서 재생된다
    with guide_column:
        render_html(f"""
            <div class="bt-box bt-obs">
                <div class="bt-box-label">{icon("play_circle")} {escape(video['title'])}</div>
                이 영상에서 확인할 것<br>
                ① 유닉스 시간이 무엇인지<br>
                ② 왜 2038년 1월 19일에 문제가 생기는지<br>
                ③ 64비트로 바꾸는 해결 방법
            </div>
        """)


def show_lab_link(case):
    """실험실로 가는 버튼: 이 사례와 연결된 실험을 열어 둔 채로 이동한다."""
    if st.button("이 원리를 현상 실험실에서 직접 확인하기", icon=":material/science:", type="primary", width="stretch"):
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
    """⑨ 자세한 정보를 탭으로 나눠서 한 화면에 담는다."""
    where_tab, fix_tab, related_tab = st.tabs(["📍 자주 생기는 곳", "🛠️ 해결 방법", "🔗 관련 사례"])
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
    with related_tab:
        show_related_cases(cases, case)


def apply_anatomy_style():
    """원인 해부실에만 쓰는 배치 디자인"""
    render_html("""
        <style>
        .an-title h2 { margin: 2px 0 0 !important; }
        .pick-label { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: 1.05rem; white-space: nowrap; margin-right: 10px; }
        .st-key-case_pick > div { width: auto !important; flex: none !important; }
        .an-summary { color: var(--text); font-size: 1.02rem; line-height: 1.7; }
        /* 같은 높이의 3칸 격자 (증상 · 정상이라면 · 실제로는) */
        .an-grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
        .an-grid3 .bt-box { margin: 0; }
        .an-observed { margin-top: 10px; }
        /* 원인 추적 카드: 화면 폭에 맞춰 한 줄에 최대 4장, 높이는 모두 같게 */
        .an-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 10px; margin-bottom: 16px; }
        .an-step { background: var(--paper); border: 3px solid var(--ink); padding: 10px 12px; }
        .an-step-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
        .an-step-head .bt-step-no { flex: none; width: 50px; height: 32px; line-height: 28px; }
        .an-step-text { font-size: 0.98rem; line-height: 1.7; color: var(--text); }
        .an-step-text p { margin: 0 0 6px; }   /* 한 카드에 합쳐진 문장 사이 간격 */
        .an-sources { margin: 0; padding-left: 22px; line-height: 1.9; }
        .an-sources a { color: #2F6B2A; font-weight: 700; }
        @media (max-width: 800px) { .an-grid3 { grid-template-columns: 1fr; } }

        /* 용어 카드: 한 줄에 나란히, 높이는 모두 같게, '자세히 보기' 버튼은 카드 맨 아래 */
        .st-key-term_row [data-testid="stHorizontalBlock"] { align-items: stretch; }
        .st-key-term_row [data-testid="stColumn"] > [data-testid="stVerticalBlock"] { height: 100%; }
        .st-key-term_row [data-testid="stLayoutWrapper"]:has(> [class*="st-key-term_card_"]) { flex: 1 1 auto; }
        [class*="st-key-term_card_"] { height: 100%; gap: 4px; background: var(--paper); border: 2px solid var(--ink);
                                       border-top: 6px solid var(--ink); padding: 10px 10px 2px; }
        [class*="st-key-term_card_"] > [data-testid="stElementContainer"]:has(.stButton) { margin-top: auto; }
        [class*="st-key-term_card_"] div.stButton { padding-top: 2px; }
        [class*="st-key-term_card_"] div.stButton button { min-height: 32px; padding: 2px 6px; margin: 4px 4px 8px; }
        [class*="st-key-term_card_"] div.stButton button p { font-size: 0.88rem !important; }
        /* 자세히 보기 팝업 안의 글 */
        div[role="dialog"] p, div[role="dialog"] li { font-size: 1.02rem; line-height: 1.75; word-break: keep-all; }
        div[role="dialog"] h4 { margin: 14px 0 6px !important; }
        .btg-table-wrap { max-width: 680px; margin: 14px 0 18px; overflow-x: auto; }
        .btg-table {
            border-collapse: collapse;
            width: 100%;
            background: transparent;
            font-size: 1rem;
            color: #24382A;
        }
        .btg-table th {
            color: #1F4D25;
            background: #DCE6C9;
            font-weight: 750;
        }
        .btg-table th, .btg-table td {
            border: 1px solid #9BAE91;
            padding: 10px 14px;
            text-align: center;
            overflow-wrap: anywhere;
        }
        .btg-table-small { max-width: 460px; }
        .btg-bits {
            display: grid;
            grid-template-columns: repeat(8, minmax(0, 1fr));
            gap: 4px;
            max-width: 640px;
            margin: 12px 0 6px;
        }
        .btg-bits > div { text-align: center; min-width: 0; }
        .btg-bits small {
            display: block; color: #315338; font-weight: 700;
            font-size: .78rem; margin-bottom: 4px;
        }
        .btg-bits span {
            display: block; border: 1px solid #789373;
            padding: 9px 0; background: #F0F3E8;
            font-weight: 750; color: #193D23;
        }
        .btg-bits .active span { background: #C6EA4E; }
        .btg-result {
            max-width: 640px; padding: 7px 0;
            font-size: .96rem; color: #23482C;
        }
        .btg-result span { margin-left: 14px; }
        @media (max-width: 800px) {
            .btg-table th, .btg-table td { padding: 8px 6px; }
            .btg-bits { gap: 2px; }
            .btg-bits small { font-size: .68rem; }
            .btg-bits span { padding: 7px 0; }
        }
        .btg-twos { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:10px 0; }
        .btg-twos > div { display:flex; flex-direction:column; gap:10px; padding:14px 10px; border:2px solid #1F4D25; background:#F6F9E8; text-align:center; }
        .btg-twos code { font-size:clamp(.85rem,1.5vw,1.15rem); overflow-wrap:anywhere; }
        @media(max-width:680px){.btg-twos{grid-template-columns:1fr;}}
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
    show_key_point(current_case)              # ② 핵심 원리 (가장 크게)
    show_terms(current_case)                  # ③ 먼저 알아 둘 용어 (+ 자세히 보기 팝업)
    show_symptom_row(current_case)            # ④ 증상 · 정상이라면 · 실제로는 (+ 직접 관찰)
    show_flow(current_case)                   # ⑤ 처리 과정
    show_steps(current_case)                  # ⑥ 원인 추적 기록
    if current_case["video"]:                 # ⑦ 관련 영상이 있는 사례만
        show_video(current_case)
    show_lab_link(current_case)               # ⑧ 실험실 버튼
    show_sources(current_case)                # ⑨ 출처 (누르면 문서가 열린다)
    show_detail_tabs(all_cases, current_case) # ⑩ 아래 탭
