# =============================================================
# common.py
# 여러 페이지에서 함께 쓰는 데이터와 함수를 모아 둔 파일
# - 같은 코드를 페이지마다 반복해서 쓰지 않으려고 한곳에 모았다.
# - 각 페이지는 맨 위에서 "from common import ..."로 필요한 것만 가져다 쓴다.
# =============================================================

import json                      # JSON 파일(오류 데이터)을 파이썬 자료로 바꾸는 모듈
from html import escape          # 글자 속 <, > 같은 기호를 안전하게 바꿔 주는 함수
from pathlib import Path         # 파일 경로를 운영체제와 상관없이 다루는 도구

import streamlit as st           # 웹앱을 만드는 라이브러리


# -------------------------------------------------------------
# 1. 상수(바뀌지 않는 값) 정의
# -------------------------------------------------------------

# 오류 데이터 파일 위치
# __file__ = 지금 이 파일(common.py)의 위치
# .parent  = 그 파일이 들어 있는 폴더
# 즉 "common.py와 같은 폴더 안의 data/cases.json"을 가리킨다.
DATA_PATH = Path(__file__).parent / "data" / "cases.json"

# 오류 분류 목록 (오류 도감의 분류 버튼, 막대그래프에 사용)
CATEGORIES = ["입력", "숫자", "문자", "이미지", "파일", "화면", "시간"]

# 분류마다 붙일 아이콘 (Streamlit이 제공하는 Material 아이콘 이름)
CATEGORY_ICONS = {
    "전체": "layers",
    "입력": "keyboard",
    "숫자": "calculate",
    "문자": "text_fields",
    "이미지": "image",
    "파일": "description",
    "화면": "desktop_windows",
    "시간": "schedule",
}

# 원인 유형 이름과 설명 (딕셔너리: "이름": "설명")
# 오류 비교실에서 두 오류의 원인 유형을 설명할 때 사용한다.
CAUSE_TYPES = {
    "상태 불일치": "두 곳이 기억하는 정보가 서로 달라서 생기는 오류",
    "표현의 한계": "컴퓨터가 정보를 완벽하게 저장할 수 없어서 생기는 오류",
    "규칙 불일치": "저장할 때와 읽을 때 쓰는 규칙이 달라서 생기는 오류",
    "보이지 않는 정보": "화면에 안 보이는 정보 때문에 생기는 오류",
    "자동 해석": "컴퓨터가 데이터의 종류를 스스로 짐작하다가 생기는 오류",
    "환경 차이": "기기나 지역 같은 환경이 달라서 생기는 오류",
}


# -------------------------------------------------------------
# 2. 데이터 관련 함수
# -------------------------------------------------------------

# @st.cache_data: 한 번 읽은 결과를 저장(캐시)해 두는 기능
# → 페이지를 이동할 때마다 파일을 다시 읽지 않아서 빠르다.
@st.cache_data
def load_cases():
    """cases.json 파일을 읽어서 오류 목록(딕셔너리들의 리스트)으로 돌려준다."""
    # encoding="utf-8": 한글이 깨지지 않도록 UTF-8 규칙으로 읽는다. (CASE 03과 관련!)
    with open(DATA_PATH, encoding="utf-8") as file:
        return json.load(file)


def find_case(cases, case_id):
    """오류 목록에서 번호(id)가 같은 오류 하나를 찾아 돌려준다. 없으면 None."""
    for case in cases:                 # 목록을 처음부터 하나씩 확인
        if case["id"] == case_id:      # 번호가 같으면
            return case                # 그 오류를 바로 돌려준다
    return None                        # 끝까지 못 찾으면 None


def case_label(case):
    """선택 상자나 버튼에 보여 줄 이름을 만든다. 예) CASE 01 · 완성을 고치다 완완성이 됨"""
    # :02d → 숫자를 두 자리로 맞춘다. (1 → 01)
    return f"CASE {case['id']:02d} · {case['title']}"


def search_cases(cases, keyword, category):
    """검색어(keyword)와 분류(category)로 오류 목록을 걸러 낸다."""
    # 앞뒤 공백을 지우고 소문자로 바꿔서 "IME"와 "ime"를 같은 검색어로 본다.
    keyword = keyword.strip().lower()
    results = []

    for case in cases:
        # 조건 1) 분류: "전체"가 아니고 분류가 다르면 건너뛴다.
        if category != "전체" and case["category"] != category:
            continue

        # 조건 2) 검색어: 제목, 기술, 요약, 증상, 키워드를 한 문장으로 합친 뒤 검색한다.
        searchable_text = " ".join(
            [case["title"], case["tech"], case["summary"], case["symptom"]]
            + case["keywords"]
        ).lower()

        # 검색어가 비어 있으면 ""는 모든 글자 안에 있으므로 전부 통과한다.
        if keyword in searchable_text:
            results.append(case)

    return results


# -------------------------------------------------------------
# 3. 페이지 이동 함수
# -------------------------------------------------------------

def open_case(case_id):
    """선택한 오류 번호를 기억해 두고 원인 해부실 페이지로 이동한다."""
    # st.session_state: 페이지를 옮겨도 사라지지 않는 저장 공간 (상태 관리)
    st.session_state["selected_case"] = case_id
    st.switch_page("pages/anatomy.py")


# -------------------------------------------------------------
# 4. 화면 그리기 함수
# -------------------------------------------------------------

def render_html(code):
    """HTML 코드를 화면에 그린다."""
    # 줄 앞의 공백이 4칸 이상이면 마크다운이 '코드 블록'으로 착각해서
    # HTML이 글자 그대로 보인다. 그래서 줄마다 앞뒤 공백을 지우고,
    # 빈 줄도 지워서 HTML이 중간에 끊기지 않게 한다.
    lines = [line.strip() for line in code.splitlines()]
    clean_code = "\n".join(line for line in lines if line)
    # unsafe_allow_html=True: 마크다운 안에서 HTML 태그를 쓸 수 있게 허용
    st.markdown(clean_code, unsafe_allow_html=True)


def icon(name):
    """HTML 안에서 쓸 Material 아이콘 하나를 만든다. 예) icon("science") → 플라스크 모양"""
    # Streamlit이 이미 불러와 둔 'Material Symbols' 글꼴을 써서 아이콘 이름을 그림으로 보여 준다.
    return f'<span class="bt-icon">{escape(name)}</span>'


def page_header(icon_name, title, description):
    """내부 페이지 맨 위에 '아이콘 + 제목 + 설명'을 그린다."""
    # escape(): 글자 속 <, > 같은 기호가 HTML 태그로 오해되지 않게 바꾼다.
    render_html(f"""
        <div class="bt-header">
            <h1 class="bt-title">{icon(icon_name)} {escape(title)}</h1>
            <p class="bt-desc">{escape(description)}</p>
        </div>
    """)


def case_card(case):
    """오류 카드 한 장의 내용(번호, 분류, 제목, 기술, 요약)을 그린다."""
    category_icon = CATEGORY_ICONS[case["category"]]
    render_html(f"""
        <div class="bt-card">
            <div class="bt-card-top">
                <span class="bt-tag">{icon(category_icon)} {escape(case['category'])}</span>
                <span class="bt-no">BUG-{case['id']:03d}</span>
            </div>
            <div class="bt-card-title">{escape(case['title'])}</div>
            <div class="bt-card-tech">{escape(case['tech'])}</div>
            <div class="bt-card-summary">{escape(case['summary'])}</div>
        </div>
    """)


def apply_style():
    """앱 전체에 적용할 디자인(CSS)을 넣는다. → 라임색 다크 터미널 스타일"""
    render_html("""
        <style>
        /* 1) 글꼴 불러오기: 본문 한글 글꼴, 코딩용 한글 글꼴, 레트로 영문 글꼴 */
        @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic+Coding:wght@400;700&family=Noto+Sans+KR:wght@400;500;700;800&family=VT323&display=swap');

        /* 2) 자주 쓰는 색을 변수로 정해 둔다. (한곳에서만 정의) */
        :root {
            --bt-bg: #101417;        /* 배경 */
            --bt-panel: #1C2529;     /* 상자 배경 */
            --bt-line: #46554A;      /* 테두리 */
            --bt-text: #E9EDE7;      /* 기본 글자 */
            --bt-dim: #BFCBC1;       /* 흐린 글자 (배경과 대비가 충분한 밝기) */
            --bt-lime: #B7E66B;      /* 대표 강조 색(라임) */
            --bt-lime-soft: rgba(183, 230, 107, 0.14);   /* 라임색 옅은 배경 */
            --bt-lime-line: rgba(183, 230, 107, 0.55);   /* 라임색 옅은 테두리 */
            --bt-glow: 0 0 18px rgba(183, 230, 107, 0.25); /* 라임색 빛 번짐 */
            --bt-red: #ff5c7a;       /* 오류(빨강) */
            --bt-yellow: #ffd166;    /* 핵심·추정(노랑) */
            --bt-sky: #8fc7ff;       /* 직접 관찰(하늘색) */
        }

        /* 3) 전체 배경과 본문 영역 */
        html, body, [data-testid="stAppViewContainer"] { background: var(--bt-bg); }
        .block-container { max-width: 1280px; padding: 4.8rem 2.6rem 5rem; }  /* 위쪽 여백: 메뉴 바에 가리지 않게 */

        /* 4) 글꼴과 글자 크기 (읽기 쉽게 크고 넉넉하게) */
        .stMarkdown p, .stMarkdown li, [data-testid="stWidgetLabel"] p {
            font-family: 'Noto Sans KR', sans-serif; font-size: 1rem; line-height: 1.72;
        }
        h1, h2, h3, h4 {
            font-family: 'Noto Sans KR', sans-serif !important; font-weight: 800 !important; line-height: 1.35 !important;
        }
        code, pre, .bt-no, .bt-box-label, .bt-basis { font-family: 'Nanum Gothic Coding', monospace !important; }

        /* 5) HTML 안에서 쓰는 아이콘 (Material Symbols 글꼴) */
        .bt-icon {
            font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal;
            font-size: 1.15em; line-height: 1; vertical-align: -0.18em;
            display: inline-block; letter-spacing: normal; text-transform: none; white-space: nowrap;
            -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga';
        }

        /* 6) 위쪽 메뉴 바 */
        header[data-testid="stHeader"] {
            background: #0c1110; border-bottom: 1px solid var(--bt-lime-line);
        }

        /* 7) 페이지 제목 (아이콘 + 제목 + 설명) */
        .bt-header { border-bottom: 1px solid var(--bt-line); padding-bottom: 20px; margin-bottom: 26px; }
        .bt-title { color: var(--bt-text); font-size: clamp(1.8rem, 3vw, 2.5rem); margin: 0 0 6px 0; padding: 0; }
        .bt-title .bt-icon { color: var(--bt-lime); }
        .bt-desc { color: var(--bt-dim); font-size: 1.05rem; line-height: 1.7; margin: 0; }

        /* 8) 오류 카드 */
        .bt-card { min-height: 175px; }
        .bt-card-top { display: flex; justify-content: space-between; align-items: center; }
        .bt-no { color: var(--bt-lime); font-size: 0.9rem; font-weight: 700; }
        .bt-tag {
            color: var(--bt-lime); font-size: 0.9rem; font-weight: 700;
            border: 1px solid var(--bt-lime-line); border-radius: 8px; padding: 4px 10px;
        }
        .bt-card-title { color: var(--bt-text); font-size: 1.22rem; font-weight: 800; line-height: 1.45; margin-top: 10px; }
        .bt-card-tech { color: var(--bt-lime); font-size: 0.94rem; font-weight: 700; margin: 2px 0 8px 0; }
        .bt-card-summary { color: var(--bt-dim); font-size: 1rem; line-height: 1.7; }

        /* 9) 설명 상자 (정상 = 라임, 오류 = 빨강, 핵심 = 노랑, 직접 관찰 = 하늘) */
        .bt-box {
            background: var(--bt-panel); border: 1px solid var(--bt-line);
            border-radius: 13px; padding: 20px 22px; margin-bottom: 12px; color: var(--bt-text); line-height: 1.75;
        }
        .bt-box-label { font-size: 0.9rem; font-weight: 700; margin-bottom: 6px; }
        .bt-ok { border-left: 4px solid var(--bt-lime); }
        .bt-ok .bt-box-label { color: var(--bt-lime); }
        .bt-obs { border-left: 4px solid var(--bt-sky); }
        .bt-obs .bt-box-label { color: var(--bt-sky); }
        .bt-err { border-left: 4px solid var(--bt-red); }
        .bt-err .bt-box-label { color: var(--bt-red); }
        .bt-key { border-left: 4px solid var(--bt-yellow); }
        .bt-key .bt-box-label { color: var(--bt-yellow); }

        /* 10) 처리 과정 그림 (입력 → 처리 → 출력) */
        .bt-flow { display: flex; align-items: stretch; gap: 10px; margin: 6px 0 18px 0; }
        .bt-flow-box {
            flex: 1; text-align: center; padding: 16px 12px; border-radius: 13px;
            border: 1.5px solid var(--bt-lime); background: var(--bt-lime-soft); box-shadow: var(--bt-glow);
        }
        .bt-flow-box .bt-icon { font-size: 2rem; color: var(--bt-lime); }
        .bt-flow-name { color: var(--bt-lime); font-weight: 800; margin: 4px 0; }
        .bt-flow-text { color: var(--bt-text); font-size: 0.95rem; line-height: 1.5; }
        .bt-flow-out { border-color: var(--bt-red); background: rgba(255, 92, 122, 0.08); box-shadow: none; }
        .bt-flow-out .bt-icon, .bt-flow-out .bt-flow-name { color: var(--bt-red); }
        .bt-flow-arrow { align-self: center; color: var(--bt-lime); font-size: 1.6rem; }

        /* 11) 발생 과정 단계 (TRACE #01 → #02 → #03 흐름) */
        .bt-step { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 0; }
        .bt-step-no {
            flex: 0 0 42px; height: 42px; border-radius: 9px; text-align: center; line-height: 42px;
            background: var(--bt-lime-soft); color: var(--bt-lime);
            font-family: 'Nanum Gothic Coding', monospace; font-weight: 700;
        }
        .bt-step-text { line-height: 1.7; padding-top: 4px; font-size: 1rem; }
        .bt-arrow { color: var(--bt-lime); opacity: 0.6; padding: 2px 0 2px 30px; font-size: 0.9rem; line-height: 1.1; }

        /* 12) 단계별 근거 이름표 (문서로 확인 = 라임, 추정 = 노랑) */
        .bt-basis {
            display: inline-block; font-size: 0.85rem; font-weight: 700;
            border-radius: 6px; padding: 1px 8px; margin-bottom: 4px;
        }
        .bt-basis-ok { color: var(--bt-lime); border: 1px solid var(--bt-lime-line); }
        .bt-basis-guess { color: var(--bt-yellow); border: 1px solid rgba(255, 209, 102, 0.5); }

        /* 13) 작은 이름표 (BUG-001, 분류, 기술 등) */
        .bt-badge {
            display: inline-block; font-family: 'Nanum Gothic Coding', monospace; font-size: 0.9rem; font-weight: 700;
            border: 1px solid var(--bt-line); border-radius: 6px; padding: 3px 10px; margin: 0 6px 6px 0;
            color: var(--bt-dim);
        }
        .bt-badge-on { color: var(--bt-lime); border-color: var(--bt-lime-line); }

        /* 14) 버튼: 크고 굵게 (누르기 쉽게) */
        div.stButton > button, div[data-testid="stPageLink"] a {
            min-height: 52px; padding: 10px 20px; border-radius: 12px;
            font-family: 'Noto Sans KR', sans-serif !important; font-weight: 800 !important;
            border: 1.5px solid #6c8a58; background: #202b27; color: #eef4e8;
            transition: background-color .14s ease, border-color .14s ease, box-shadow .14s ease;
        }
        div.stButton > button p { font-size: 1.05rem !important; font-weight: 800 !important; }
        div.stButton > button:hover { border-color: var(--bt-lime); background: #2d3c2d; box-shadow: var(--bt-glow); }
        /* 라임색(주요) 버튼: 밝은 배경이라 글자는 어두운 색 */
        div.stButton > button[kind="primary"] { background: var(--bt-lime); border-color: var(--bt-lime); color: #101417; }
        div.stButton > button[kind="primary"] p { color: #101417 !important; }
        div.stButton > button[kind="primary"]:hover { background: #cef48d; }
        /* 키보드로 이동할 때 지금 위치가 잘 보이게 */
        button:focus-visible, input:focus-visible, a:focus-visible { outline: 3px solid var(--bt-lime) !important; outline-offset: 3px; }

        /* 15) 분류 선택(라디오)을 큰 칩 버튼처럼 */
        div[data-testid="stRadio"] > div[role="radiogroup"] { display: flex; flex-wrap: wrap; gap: 10px 12px; }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label {
            display: inline-flex; align-items: center; justify-content: center;
            min-height: 48px; min-width: 92px; padding: 8px 16px; margin: 0;
            border: 1.5px solid #5b7654; border-radius: 24px; background: #1c2923; cursor: pointer;
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover { background: #2a3c2d; border-color: var(--bt-lime); }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) { background: var(--bt-lime); border-color: var(--bt-lime); }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) p,
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) span { color: #101417 !important; }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label p { font-size: 1rem !important; font-weight: 800 !important; }
        /* 동그란 라디오 표시는 숨긴다 */
        div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { width: 0; height: 0; overflow: hidden; margin: 0; padding: 0; }

        /* 16) 입력창, 선택 상자, 테두리 상자, 탭 */
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
            min-height: 50px; border-radius: 11px; background-color: #18211f; border-color: #61745e;
        }
        [data-testid="stWidgetLabel"] p { font-weight: 700 !important; color: var(--bt-text); }
        div[data-testid="stVerticalBlockBorderWrapper"] { background: var(--bt-panel); border-radius: 14px; border-color: var(--bt-line); }
        div[data-testid="stCodeBlock"], pre { border-radius: 12px; }
        [data-testid="stTabs"] button p { font-weight: 800 !important; font-size: 1rem !important; }
        .stMarkdown a { color: var(--bt-lime); }

        /* 17) 좁은 화면(휴대폰)에서는 여백과 글자를 조금 줄인다 */
        @media (max-width: 800px) {
            .block-container { padding: 4.5rem 1rem 4rem; }
            .bt-card-title { font-size: 1.12rem; }
            .bt-flow { flex-direction: column; }
            .bt-flow-arrow { transform: rotate(90deg); }
        }
        /* 18) 움직임을 줄이는 설정을 켠 사용자에게는 애니메이션을 끈다 */
        @media (prefers-reduced-motion: reduce) {
            *, *::before, *::after { transition-duration: 0.01ms !important; animation-duration: 0.01ms !important; }
        }

        /* 19) 접근성 및 가독성: 전체 화면의 흐릿한 글씨 보정 */
        [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            color: #E9EDE7;
        }
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stWidgetLabel"] p {
            color: #E9EDE7;
            opacity: 1 !important;
        }
        [data-testid="stCaptionContainer"] p,
        [data-testid="stHelperText"] p,
        [data-testid="stMetricLabel"] p {
            color: #CBD8CE !important;
            opacity: 1 !important;
            font-size: 0.93rem !important;
        }

        /* 20) Streamlit 상단 내비게이션: 선택되지 않은 메뉴도 밝게 */
        [data-testid="stNavigation"],
        [data-testid="stTopNav"],
        [data-testid="stTopNav"] nav,
        [data-testid="stNavigation"] nav {
            background: #101714 !important;
        }
        [data-testid="stTopNav"] a,
        [data-testid="stTopNav"] button,
        [data-testid="stNavigation"] a,
        [data-testid="stNavigation"] button,
        header[data-testid="stHeader"] a {
            color: #E9EDE7 !important;
            opacity: 1 !important;
            font-family: 'Noto Sans KR', sans-serif !important;
            font-size: 1.05rem !important;
            font-weight: 800 !important;
            min-height: 48px;
        }
        [data-testid="stTopNav"] a *,
        [data-testid="stTopNav"] button *,
        [data-testid="stNavigation"] a *,
        [data-testid="stNavigation"] button * {
            color: inherit !important;
            opacity: 1 !important;
            font-weight: 800 !important;
        }
        [data-testid="stTopNav"] a[aria-current="page"],
        [data-testid="stNavigation"] a[aria-current="page"],
        [data-testid="stTopNav"] a[aria-selected="true"],
        [data-testid="stNavigation"] a[aria-selected="true"] {
            background: #B7E66B !important;
            color: #101417 !important;
            border-radius: 10px;
        }
        [data-testid="stTopNav"] a:hover,
        [data-testid="stNavigation"] a:hover {
            background: #2B3A30;
            color: #FFFFFF !important;
            border-radius: 10px;
        }

        /* 21) 버튼: Streamlit 내부 텍스트까지 색상 지정 */
        div.stButton > button,
        div.stButton > button *,
        div[data-testid="stPageLink"] a,
        div[data-testid="stPageLink"] a * {
            color: #F4F8F0 !important;
            opacity: 1 !important;
            font-weight: 800 !important;
        }
        div.stButton > button[kind="primary"],
        div.stButton > button[kind="primary"] *,
        div.stButton > button[data-testid="stBaseButton-primary"],
        div.stButton > button[data-testid="stBaseButton-primary"] * {
            color: #101417 !important;
            background-color: #B7E66B;
        }
        div.stButton > button:disabled,
        div.stButton > button:disabled * {
            color: #C3CEC4 !important;
            opacity: 1 !important;
        }

        /* 22) 입력창: 날짜·시간·검색·선택 메뉴의 값과 안내문 */
        div[data-baseweb="input"] input,
        div[data-baseweb="select"] input,
        div[data-baseweb="select"] [role="combobox"],
        div[data-baseweb="select"] [role="combobox"] *,
        [data-testid="stDateInput"] input,
        [data-testid="stTimeInput"] input,
        textarea {
            color: #F2F6F0 !important;
            -webkit-text-fill-color: #F2F6F0 !important;
            font-family: 'Noto Sans KR', sans-serif !important;
            font-size: 1.04rem !important;
            font-weight: 700 !important;
            opacity: 1 !important;
        }
        input::placeholder, textarea::placeholder {
            color: #BAC9BC !important;
            -webkit-text-fill-color: #BAC9BC !important;
            opacity: 1 !important;
        }
        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div {
            background: #202B28 !important;
            border: 1.5px solid #758D76 !important;
        }
        [data-baseweb="popover"] [role="option"],
        [data-baseweb="popover"] [role="option"] * {
            color: #E9EDE7 !important;
            font-size: 1rem !important;
            font-weight: 700 !important;
        }

        /* 23) 분류 필터: 모든 칩이 읽히고 선택 상태가 뚜렷하게 */
        div[data-testid="stRadio"] > div[role="radiogroup"] > label {
            background: #202B27 !important;
            border-color: #819A75 !important;
            min-height: 52px;
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label p,
        div[data-testid="stRadio"] > div[role="radiogroup"] > label span {
            color: #F0F6EE !important;
            opacity: 1 !important;
            font-weight: 800 !important;
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {
            background: #B7E66B !important;
            border-color: #B7E66B !important;
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) p,
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) span {
            color: #101417 !important;
        }

        /* 24) 탭, 펼침 상자, 표 및 코드 결과 */
        [data-testid="stTabs"] button,
        [data-testid="stTabs"] button p,
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary * {
            color: #E9EDE7 !important;
            opacity: 1 !important;
            font-weight: 800 !important;
        }
        [data-testid="stTabs"] button[aria-selected="true"],
        [data-testid="stTabs"] button[aria-selected="true"] p {
            color: #B7E66B !important;
        }
        [data-testid="stDataFrame"], [data-testid="stTable"] {
            color: #E9EDE7;
        }
        .bt-box, .bt-card, .bt-step-text, .bt-flow-text {
            color: #E9EDE7 !important;
            opacity: 1 !important;
        }

        /* 25) 모바일에서 버튼과 메뉴를 작게 줄이지 않음 */
        @media (max-width: 800px) {
            div.stButton > button { min-height: 52px; }
            div[data-testid="stRadio"] > div[role="radiogroup"] > label {
                min-height: 48px;
                min-width: 88px;
            }
        }


/* BUG TRACE: warm beige CRT research lab, high contrast override */
:root {
 --bt-bg:#F5F0E4; --bt-panel:#FFFCF5; --bt-line:#B7BEA6;
 --bt-text:#233529; --bt-dim:#4D5E50; --bt-lime:#D7EAA4;
 --bt-lime-soft:#EDF5D8; --bt-lime-line:#72944F;
 --bt-glow:0 4px 15px rgba(63,80,43,.12);
 --bt-red:#A94135; --bt-yellow:#80610E; --bt-sky:#285C86;
}
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:#F5F0E4 !important; color:#233529 !important; }
[data-testid="stHeader"], header[data-testid="stHeader"], [data-testid="stTopNav"], [data-testid="stNavigation"], [data-testid="stTopNav"] nav, [data-testid="stNavigation"] nav { background:#E9E0CD !important; color:#233529 !important; border-bottom:1px solid #ACB49C !important; }
[data-testid="stTopNav"] a, [data-testid="stTopNav"] button, [data-testid="stNavigation"] a, [data-testid="stNavigation"] button, header[data-testid="stHeader"] a,
[data-testid="stTopNav"] a *, [data-testid="stTopNav"] button *, [data-testid="stNavigation"] a *, [data-testid="stNavigation"] button * {
 color:#24382A !important; opacity:1 !important; -webkit-text-fill-color:#24382A !important; font-size:16px !important; font-weight:800 !important;
}
[data-testid="stTopNav"] a[aria-current="page"], [data-testid="stNavigation"] a[aria-current="page"], [data-testid="stTopNav"] a[aria-selected="true"], [data-testid="stNavigation"] a[aria-selected="true"] { background:#C9DE91 !important; border-radius:9px; }
[data-testid="stTopNav"] a:hover, [data-testid="stNavigation"] a:hover {background:#D8E8B9 !important;}
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li, [data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"] p, [data-testid="stHelperText"] p, [data-testid="stMetricLabel"] p {color:#344839 !important;opacity:1 !important; -webkit-text-fill-color:initial !important;}
[data-testid="stCaptionContainer"] p {font-size:14px !important;}
.bt-header {border-bottom:2px solid #B7BEA6;}
.bt-title,.bt-card-title {color:#203A28 !important;}
.bt-desc,.bt-card-summary,.bt-step-text,.bt-flow-text {color:#435448 !important;}
.bt-card-tech,.bt-no,.bt-tag,.bt-flow-name,.bt-flow-box .bt-icon,.bt-title .bt-icon,.bt-badge-on {color:#406A2D !important;}
.bt-card,.bt-box {background:#FFFCF5 !important;color:#233529 !important;border-color:#B7BEA6 !important;box-shadow:0 2px 9px rgba(35,53,41,.06);}
.bt-box-label {font-weight:800;}
.bt-ok .bt-box-label,.bt-basis-ok {color:#406A2D !important;}
.bt-err .bt-box-label,.bt-flow-out .bt-flow-name {color:#A94135 !important;}
.bt-key .bt-box-label,.bt-basis-guess {color:#80610E !important;}
.bt-obs .bt-box-label {color:#285C86 !important;}
.bt-flow-box {background:#EEF5DA !important; border-color:#85A661 !important;box-shadow:none !important;}
.bt-flow-out {background:#FFF0E8 !important;border-color:#BD7D68 !important;}
.bt-step-no {background:#DFECC2 !important;color:#335D2C !important;}
.bt-arrow,.bt-flow-arrow {color:#557E38 !important;}
.bt-badge,.bt-tag,.bt-basis {background:#F4F5E9 !important;border-color:#B5C4A4 !important;color:#3B5D35 !important;}
[data-testid="stVerticalBlockBorderWrapper"] {background:#FFFCF5 !important;border-color:#C4C8B5 !important;box-shadow:0 3px 14px rgba(45,58,37,.06);}
div.stButton > button,div.stButton > button *,div[data-testid="stPageLink"] a,div[data-testid="stPageLink"] a * {
 color:#233529 !important; -webkit-text-fill-color:#233529 !important; background:#E9EEDB !important;
 border-color:#879D75 !important;opacity:1 !important;font-weight:800 !important;
}
div.stButton > button,div[data-testid="stPageLink"] a {min-height:54px !important; border-radius:10px !important; font-size:17px !important;}
div.stButton > button:hover,div[data-testid="stPageLink"] a:hover {background:#D8E7B8 !important;border-color:#527D39 !important;}
div.stButton > button[kind="primary"],div.stButton > button[kind="primary"] *,div.stButton > button[data-testid="stBaseButton-primary"],div.stButton > button[data-testid="stBaseButton-primary"] * {background:#C9E28E !important;color:#1E3022 !important;-webkit-text-fill-color:#1E3022 !important;}
div[data-testid="stRadio"] > div[role="radiogroup"] > label {background:#FFFDF5 !important;border:2px solid #9DAE8D !important;min-height:52px !important;min-width:94px !important;border-radius:10px !important;}
div[data-testid="stRadio"] > div[role="radiogroup"] > label p,div[data-testid="stRadio"] > div[role="radiogroup"] > label span {color:#24382A !important;-webkit-text-fill-color:#24382A !important;font-size:16px !important;font-weight:800 !important;}
div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) {background:#C9E28E !important;border-color:#557E38 !important;box-shadow:inset 0 0 0 1px #557E38;}
div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) p,div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) span {color:#1E3022 !important;}
div[data-baseweb="input"] > div,div[data-baseweb="select"] > div, [data-testid="stDateInput"] [data-baseweb="input"] > div,[data-testid="stTimeInput"] [data-baseweb="input"] > div {background:#FFFFFF !important;border:1.5px solid #A2B19A !important;min-height:52px !important;}
div[data-baseweb="input"] input,div[data-baseweb="select"] input,div[data-baseweb="select"] [role="combobox"],div[data-baseweb="select"] [role="combobox"] *,[data-testid="stDateInput"] input,[data-testid="stTimeInput"] input,textarea {color:#22372A !important;-webkit-text-fill-color:#22372A !important;font-size:16px !important;font-weight:700 !important;}
input::placeholder,textarea::placeholder {color:#637568 !important;-webkit-text-fill-color:#637568 !important;}
[data-baseweb="popover"],[data-baseweb="popover"] [role="option"], [data-baseweb="popover"] [role="option"] * {background:#FFFFFF !important;color:#233529 !important;-webkit-text-fill-color:#233529 !important;}
[data-testid="stTabs"] button,[data-testid="stTabs"] button p,[data-testid="stExpander"] summary,[data-testid="stExpander"] summary * {color:#29412F !important;font-weight:800 !important;}
[data-testid="stTabs"] button[aria-selected="true"],[data-testid="stTabs"] button[aria-selected="true"] p {color:#386F2B !important;}
.stMarkdown a {color:#386F2B !important;text-decoration:underline;}
hr {border-color:#B7BEA6 !important;}
@media(max-width:800px){.block-container{padding:4.5rem 1rem 3rem !important;} .bt-card{min-height:0;}}

        </style>
    """)

    render_html('\n        <style>\n        /* Retro OS window: readable interior pages, consistent with CRT home */\n        [data-testid="stAppViewContainer"] {background: #eae4d4!important;color:#203b29!important;}\n        .block-container {max-width:1250px;padding-top:4.6rem;}\n        .bt-header {background:#f9f7e9;border:2px solid #8c9f7b;border-radius:12px;padding:20px 24px;margin-bottom:22px;box-shadow:5px 5px 0 #c6cbb1;}\n        .bt-title {font-size:clamp(1.7rem,2.8vw,2.35rem)!important;color:#1c4027!important;}\n        .bt-card {background:#fffdf5!important;border:0!important;box-shadow:none!important;padding:0!important;min-height:0!important;}\n        .bt-card-title {font-family:\'Noto Sans KR\',sans-serif!important;font-size:1.25rem!important;line-height:1.55!important;word-break:keep-all!important;}\n        .bt-card-summary {font-size:1rem!important;line-height:1.8!important;word-break:keep-all!important;}\n        .bt-card-tech {font-size:.94rem!important;}\n        div[data-testid="stVerticalBlockBorderWrapper"] {background:#fffdf5!important;border:1.5px solid #a6b296!important;border-radius:13px!important;padding:3px;}\n        div.stButton>button {border:1.5px solid #78906c!important;background:#e9efdb!important;color:#203c2a!important;border-radius:8px!important;min-height:47px!important;box-shadow:0 3px 0 #a5b294!important;}\n        div.stButton>button *,div.stButton>button p {color:#203c2a!important;font-size:1rem!important;}\n        div.stButton>button:hover {background:#d7edaa!important;}\n        div.stButton>button[kind="primary"] {background:#c6f344!important;}\n        div[data-baseweb="input"]>div,div[data-baseweb="select"]>div {background:#fffef6!important;border:1.5px solid #8c9f7b!important;}\n        div[data-baseweb="input"] input,div[data-baseweb="select"] input,[data-testid="stDateInput"] input,[data-testid="stTimeInput"] input,textarea {color:#1b3824!important;-webkit-text-fill-color:#1b3824!important;}\n        div[data-testid="stRadio"]>div[role="radiogroup"]>label {background:#faf8eb!important;border:1.5px solid #9bac8b!important;border-radius:8px!important;min-height:48px!important;}\n        div[data-testid="stRadio"]>div[role="radiogroup"]>label p,div[data-testid="stRadio"]>div[role="radiogroup"]>label span {color:#23412c!important;font-weight:800!important;}\n        div[data-testid="stRadio"]>div[role="radiogroup"]>label:has(input:checked) {background:#c6f344!important;border-color:#547d3a!important;}\n        [data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li {color:#273d2c!important;}\n        .bt-box,.bt-step-text,.bt-flow-text {color:#263d2d!important;}\n        .bt-box {background:#fffdf5!important;}\n        .bt-no,.bt-tag {color:#315c39!important;}\n        .bt-tag {background:#edf2e2!important;}\n        [data-testid="stTopNav"] a,[data-testid="stTopNav"] a * {color:#25402d!important;font-size:1rem!important;font-weight:800!important;}\n        </style>\n')
