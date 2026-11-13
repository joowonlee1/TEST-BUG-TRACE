# =============================================================
# common.py
# 여러 페이지에서 함께 쓰는 데이터와 함수를 모아 둔 파일
# - 같은 코드를 페이지마다 반복해서 쓰지 않으려고 한곳에 모았다.
# - 각 페이지는 맨 위에서 "from common import ..."로 필요한 것만 가져다 쓴다.
# - 모든 페이지는 crt_frame() 안에 그려져서, 레트로 CRT 모니터 화면 속에 보인다.
# =============================================================

import json                                  # JSON 파일(오류 데이터)을 파이썬 자료로 바꾸는 모듈
from contextlib import contextmanager        # "with 함수():" 형태로 쓸 수 있는 함수를 만드는 도구
from html import escape                      # 글자 속 <, > 같은 기호를 안전하게 바꿔 주는 함수
from pathlib import Path                     # 파일 경로를 운영체제와 상관없이 다루는 도구

import streamlit as st                       # 웹앱을 만드는 라이브러리


# -------------------------------------------------------------
# 1. 상수(바뀌지 않는 값) 정의
# -------------------------------------------------------------

# 오류 데이터 파일 위치
# __file__ = 지금 이 파일(common.py)의 위치, .parent = 그 파일이 들어 있는 폴더
# 즉 "common.py와 같은 폴더 안의 data/cases.json"을 가리킨다.
DATA_PATH = Path(__file__).parent / "data" / "cases.json"

# 오류 분류 목록 (오류 도감의 분류 버튼에 사용)
# 순서 = 탐구 흐름: 숫자(정수 → 실수)를 비트로 저장하는 방식 → 글자를 숫자로 저장하는 방식 → 한글 입력
CATEGORIES = ["숫자", "문자", "입력"]

# 분류마다 붙일 아이콘 (Streamlit이 제공하는 Material 아이콘 이름)
CATEGORY_ICONS = {
    "전체": "layers",
    "숫자": "calculate",
    "문자": "text_fields",
    "입력": "keyboard",
}

# 원인 유형 이름과 설명 (딕셔너리: "이름": "설명")
# 오류 비교실에서 두 오류의 원인을 묶고 비교할 때 사용한다.
CAUSE_TYPES = {
    "표현의 한계": "정해진 칸 수(비트)로는 정보를 완벽하게 저장할 수 없어서 생기는 오류",
    "규칙 불일치": "저장할 때와 읽을 때 쓰는 규칙이 달라서 생기는 오류",
    "상태 불일치": "두 곳이 기억하는 정보가 서로 달라서 생기는 오류",
}

# 모니터 화면 위쪽 메뉴: (페이지 파일, 메뉴 이름, 아이콘)
# 첫 화면(홈)으로는 창의 × 버튼과 전원 버튼으로 돌아가므로 메뉴에는 넣지 않는다.
NAV_PAGES = [
    ("pages/catalog.py", "오류 도감", ":material/menu_book:"),
    ("pages/anatomy.py", "원인 해부실", ":material/layers:"),
    ("pages/laboratory.py", "현상 실험실", ":material/science:"),
    ("pages/compare.py", "오류 비교실", ":material/compare_arrows:"),
]

# 픽셀 아트 컴퓨터 그림 (웃는 얼굴 모니터) - 창 제목 줄과 홈 화면에서 사용
# SVG의 <rect>(사각형)를 1칸짜리 픽셀처럼 쌓아서 그린다.
# shape-rendering="crispEdges": 사각형 가장자리를 흐리지 않고 또렷하게 그린다.
PIXEL_COMPUTER_SVG = """
<svg class="px-computer" viewBox="0 0 40 30" shape-rendering="crispEdges" xmlns="http://www.w3.org/2000/svg">
<g fill="#1F4D25">
<rect x="2" y="9" width="4" height="1"/><rect x="3" y="5" width="2" height="1"/><rect x="5" y="6" width="1" height="1"/>
<rect x="3" y="13" width="2" height="1"/><rect x="5" y="12" width="1" height="1"/>
<rect x="34" y="9" width="4" height="1"/><rect x="35" y="5" width="2" height="1"/><rect x="34" y="6" width="1" height="1"/>
<rect x="35" y="13" width="2" height="1"/><rect x="34" y="12" width="1" height="1"/>
<rect x="10" y="1" width="20" height="18"/><rect x="8" y="20" width="24" height="7"/>
</g>
<rect x="11" y="2" width="18" height="16" fill="#E9F2C4"/>
<rect x="13" y="4" width="14" height="11" fill="#1F4D25"/>
<rect x="14" y="5" width="12" height="9" fill="#C6EA4E"/>
<g fill="#1F4D25">
<rect x="17" y="7" width="1" height="2"/><rect x="22" y="7" width="1" height="2"/>
<rect x="17" y="10" width="1" height="1"/><rect x="18" y="11" width="4" height="1"/><rect x="22" y="10" width="1" height="1"/>
</g>
<rect x="9" y="21" width="22" height="5" fill="#E9F2C4"/>
<g fill="#1F4D25"><rect x="11" y="23" width="1" height="1"/><rect x="13" y="23" width="1" height="1"/><rect x="22" y="23" width="7" height="1"/></g>
</svg>
"""


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
    """선택 상자나 버튼에 보여 줄 이름을 만든다. 예) BUG-001 · IME 입력 조합 상태 불일치"""
    # :03d → 숫자를 세 자리로 맞춘다. (1 → 001)
    return f"BUG-{case['id']:03d} · {case['title']}"


# 공통 데이터 검색 로직: 각 페이지의 UI 코드와 독립적으로 동작한다.
# 제목·기술·요약·증상·키워드 중 검색어가 포함된 사례만 반환한다.

def search_cases(cases, keyword, category):
    """검색어(keyword)와 분류(category)로 오류 목록을 걸러 낸다."""
    # 앞뒤 공백을 지우고 소문자로 바꿔서 "IME"와 "ime"를 같은 검색어로 본다.
    keyword = keyword.strip().lower()
    results = []

    for case in cases:
        # 조건 1) 분류: "전체"가 아니고 분류가 다르면 건너뛴다.
        if category != "전체" and case["category"] != category:
            continue

        # 조건 2) 검색어: 제목, 쉬운 이름, 기술, 요약, 증상, 키워드, 용어 이름을 한 문장으로 합친 뒤 검색한다.
        term_names = [term["term"] for term in case["terms"]]
        searchable_text = " ".join(
            [case["title"], case["nickname"], case["tech"], case["summary"], case["symptom"]]
            + case["keywords"] + term_names
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


def toggle_window(state_name):
    """창 상태(최소화 'win_min' / 최대화 'win_max')를 켜고 끈다. True ↔ False"""
    # .get(이름, False): 저장된 값이 없으면 False(꺼짐)로 본다. not → 반대로 바꾼다.
    st.session_state[state_name] = not st.session_state.get(state_name, False)


def show_window_buttons():
    """창 버튼 3개(— □ ×)를 진짜로 동작하게 만든다."""
    is_max = st.session_state.get("win_max", False)
    # horizontal=True: 버튼 3개를 가로로 나란히 놓는다.
    with st.container(key="win_btns", horizontal=True):
        # — 최소화: 화면 내용을 접는다 / 다시 누르면 펼친다
        st.button("—", key="win_min_btn", help="최소화 (내용 접기)", on_click=toggle_window, args=("win_min",))
        # □ 최대화: 모니터 틀을 빼고 화면을 꽉 채운다 / 최대화 중에는 ❐(원래대로) 모양
        st.button("❐" if is_max else "□", key="win_max_btn", help="최대화 / 원래 크기", on_click=toggle_window, args=("win_max",))
        # × 닫기: 프로그램을 닫듯이 첫 화면으로 돌아간다
        if st.button("×", key="win_close_btn", help="닫고 첫 화면으로"):
            st.session_state["win_min"] = False
            st.switch_page("pages/home.py")


def show_window_bar(english_name):
    """모니터 화면 맨 위 '창 제목 줄': 픽셀 컴퓨터 + BUG TRACE + 현재 위치 + 창 버튼(— □ ×)"""
    # 왼쪽 넓은 칸: 로고와 경로(HTML) / 오른쪽 좁은 칸: 진짜 창 버튼(Streamlit 버튼)
    title_column, button_column = st.columns([6, 1], vertical_alignment="center")
    with title_column:
        render_html(f"""
            <div class="win-bar">
                <div class="win-logo">{PIXEL_COMPUTER_SVG}<span class="win-title">BUG TRACE</span></div>
                <div class="win-path">C:\\BUG_TRACE\\{escape(english_name)}&gt;</div>
            </div>
        """)
    with button_column:
        show_window_buttons()


def show_nav(current_page):
    """창 제목 줄 아래에 4개 페이지로 가는 메뉴 버튼을 놓는다. 지금 페이지는 라임색으로 강조한다."""
    columns = st.columns(len(NAV_PAGES))
    for number, (column, (page_file, name, icon_name)) in enumerate(zip(columns, NAV_PAGES)):
        with column:
            # 지금 페이지의 버튼 상자에만 key="nav_active"를 붙여서 CSS로 라임색을 칠한다.
            box_key = "nav_active" if page_file == current_page else f"nav_{number}"
            with st.container(key=box_key):
                # st.page_link: 누르면 해당 페이지로 이동하는 링크
                st.page_link(page_file, label=name, icon=icon_name, width="stretch")


def show_monitor_panel():
    """모니터 아래쪽: 스피커 구멍, 깜빡이는 불빛, 플로피 디스크 입구 + 진짜 전원 버튼"""
    # 왼쪽 넓은 칸: 장식(HTML) / 오른쪽 좁은 칸: 누를 수 있는 전원 버튼(Streamlit 버튼)
    decor_column, power_column = st.columns([12, 1], vertical_alignment="center")
    with decor_column:
        render_html("""
            <div class="px-panel">
                <div class="px-screw"></div>
                <div class="px-grill"></div>
                <div class="px-leds"><span class="px-led-on"></span><span class="px-led-dim"></span></div>
                <div class="px-floppy"></div>
                <div class="px-grill"></div>
            </div>
        """)
    with power_column:
        with st.container(key="power"):
            # 전원 버튼: 컴퓨터를 껐다 켜듯이 첫 화면으로 돌아간다
            if st.button("", key="power_btn", icon=":material/power_settings_new:", help="전원: 첫 화면으로"):
                st.session_state["win_min"] = False
                st.session_state["win_max"] = False
                st.switch_page("pages/home.py")


# @contextmanager: 이 함수를 "with crt_frame(...):" 형태로 쓸 수 있게 만든다.
# with 블록 안에 쓴 코드(각 페이지의 내용)는 yield 자리에서 실행된다.
@contextmanager
def crt_frame(current_page, english_name):
    """레트로 CRT 모니터를 그리고, 그 화면 안에 페이지 내용을 담는다. 창 버튼(— □ ×) 상태도 반영한다."""
    is_min = st.session_state.get("win_min", False)    # 최소화 중인가?
    is_max = st.session_state.get("win_max", False)    # 최대화 중인가?
    # 최대화 중이면 바깥 틀 이름을 "crt_max"로 바꿔서 CSS로 틀을 얇게, 아래 패널은 숨긴다.
    with st.container(key="crt_max" if is_max else "crt"):     # 모니터 바깥 틀 (베이지 플라스틱)
        with st.container(key="crt_screen"):                    # 모니터 화면 (연두빛 형광 화면)
            show_window_bar(english_name)                      # 1) 창 제목 줄 (+ 진짜 창 버튼) → 화면 위에 고정
            show_nav(current_page)                             # 2) 메뉴 버튼 → 화면 위에 고정
            if is_min:
                render_html('<div class="win-min-note">▁ 창이 최소화되어 있어요. 오른쪽 위 <b>—</b> 버튼을 다시 누르면 펼쳐져요.</div>')
            # 3) 페이지 내용 상자: 높이를 정해 두고(CSS) 이 상자 안에서만 스크롤된다. → 모니터는 움직이지 않는다
            #    최소화 중이면 상자 이름을 "win_hidden"으로 바꿔서 CSS로 숨긴다. (코드는 그대로 실행됨)
            with st.container(key="win_hidden" if is_min else "win_body"):
                yield                                          # ← 여기에 각 페이지의 내용이 들어간다
        if not is_max:
            show_monitor_panel()                               # 4) 모니터 아래쪽 (최대화 중에는 숨김)


def page_banner(icon_name, english, korean, description):
    """페이지 맨 위 라임색 픽셀 배너: 아이콘 + 영어 이름 + 한글 이름 + 한 줄 설명"""
    # escape(): 글자 속 <, > 같은 기호가 HTML 태그로 오해되지 않게 바꾼다.
    render_html(f"""
        <div class="bt-banner">
            <div class="bt-banner-main">{icon(icon_name)}<span class="bt-banner-en">{escape(english)}</span><span class="bt-banner-ko">{escape(korean)}</span></div>
            <div class="bt-banner-desc">{escape(description)}</div>
        </div>
    """)


def case_card(case):
    """오류 카드 한 장의 내용(분류, 번호, 전문용어 제목, 쉬운 이름, 요약)을 그린다."""
    category_icon = CATEGORY_ICONS[case["category"]]
    render_html(f"""
        <div class="bt-card">
            <div class="bt-card-top">
                <span class="bt-tag">{icon(category_icon)} {escape(case['category'])}</span>
                <span class="bt-no">BUG-{case['id']:03d}</span>
            </div>
            <div class="bt-card-title">{escape(case['title'])}</div>
            <div class="bt-card-nick">“{escape(case['nickname'])}”</div>
            <div class="bt-card-summary">{escape(case['summary'])}</div>
        </div>
    """)


def apply_style():
    """앱 전체 디자인(CSS): 화면을 가득 채우는 베이지 레트로 CRT 모니터 + 픽셀 스타일"""
    render_html("""
        <style>
        /* ===== 1) 글꼴 불러오기 =====
           Galmuri: 한글 픽셀 글꼴(무료, SIL 오픈 폰트 라이선스) / Press Start 2P: 영어 픽셀 글꼴
           Noto Sans KR: 본문 글꼴 / Nanum Gothic Coding: 코드·터미널 글꼴 */
        @import url('https://cdn.jsdelivr.net/npm/galmuri@2.40.2/dist/galmuri.css');
        @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Nanum+Gothic+Coding:wght@400;700&family=Noto+Sans+KR:wght@400;500;700;800&display=swap');

        /* ===== 2) 색 변수 (한곳에서만 정의) ===== */
        :root {
            --ink: #1F4D25;        /* 픽셀 테두리·진한 초록 (잉크 색) */
            --lime: #C6EA4E;       /* 강조 배경: 라임 */
            --lime-soft: #E7F3C2;  /* 옅은 라임 */
            --screen: #EEF5D8;     /* 모니터 화면 바탕 */
            --paper: #FBFDF1;      /* 상자 바탕 (밝은 화면색) */
            --text: #1E3322;       /* 기본 글자 */
            --dim: #3F5844;        /* 보조 글자 (화면 위에서도 충분히 진하게) */
            --red: #A23A2E;        /* 오류: 벽돌색 */
            --yellow: #7A5A06;     /* 핵심·추정: 황토색 */
            --sky: #245A86;        /* 직접 관찰: 파랑 */
            --beige: #E8DDC4;      /* 모니터 플라스틱 */
        }

        /* ===== 3) 배경(벽)과 본문 폭, 여백 줄이기 ===== */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
            background: #E6DCC6; color: var(--text);   /* 배경은 단색. 장식 없이 모니터만 보이게 */
        }
        header[data-testid="stHeader"] { display: none; }        /* Streamlit 기본 상단 바 숨기기 (메뉴는 모니터 안에 있음) */
        .block-container { max-width: 100%; padding: 10px 16px 16px; }   /* 모니터가 화면 폭을 가득 채우도록 */
        [data-testid="stVerticalBlock"] { gap: 0.55rem; }          /* 요소 사이 간격을 촘촘하게 */
        [data-testid="stHorizontalBlock"] { gap: 0.6rem; }

        /* ===== 4) 글꼴 ===== */
        .stMarkdown p, .stMarkdown li, [data-testid="stWidgetLabel"] p {
            font-family: 'Noto Sans KR', sans-serif; font-size: 1.02rem; line-height: 1.75; color: var(--text);
        }
        [data-testid="stCaptionContainer"] p { color: var(--dim); font-size: 0.88rem; }
        /* 글꼴 나누기: 픽셀 글꼴(Galmuri)은 버튼·배너·이름표 같은 '짧은 글자'에만 쓰고,
           제목·설명처럼 읽어야 하는 글은 본문 글꼴(Noto Sans KR)로 → 레트로 느낌은 살리고 읽기는 편하게 */
        h1, h2, h3, h4 { font-family: 'Noto Sans KR', sans-serif !important; font-weight: 800 !important; color: var(--ink) !important; line-height: 1.35 !important; padding: 0.2rem 0 !important; letter-spacing: -0.3px; }
        h2 { font-size: 1.45rem !important; } h3 { font-size: 1.15rem !important; }
        code, pre { font-family: 'Nanum Gothic Coding', monospace !important; }
        .bt-icon {
            font-family: 'Material Symbols Rounded'; font-weight: normal; font-style: normal; font-size: 1.15em;
            line-height: 1; vertical-align: -0.18em; display: inline-block; letter-spacing: normal;
            text-transform: none; white-space: nowrap; font-feature-settings: 'liga';
        }

        /* ===== 5) CRT 모니터 바깥 틀과 화면 ===== */
        /* 바깥 틀: 두꺼운 베이지 플라스틱. 위쪽은 밝게, 아래쪽은 어둡게 칠해서 입체감을 준다 */
        .st-key-crt {
            background: linear-gradient(165deg, #F6EEDC 0%, #E6D8BA 55%, #D2C2A0 100%);
            border: 3px solid #B9A884; border-radius: clamp(22px, 3vw, 46px);
            padding: clamp(14px, 2.6vw, 42px) clamp(14px, 3vw, 50px) clamp(8px, 1vw, 14px); gap: 0;
            box-shadow: inset 0 5px 0 #FFFAEC, inset 0 -8px 0 #C6B490, 0 20px 34px rgba(70, 55, 30, .30);
        }
        /* 화면: 가운데는 밝고 가장자리는 초록빛으로 어두워지는 CRT 유리 + 가로 주사선 + 진한 초록 테두리
           box-shadow 바깥쪽 고리 2개 = 화면이 플라스틱 틀 안으로 쏙 들어간 '홈'처럼 보이게 한다 */
        .st-key-crt_screen {
            border-radius: clamp(18px, 2.6vw, 40px); padding: clamp(10px, 1.4vw, 22px) clamp(12px, 1.8vw, 30px); gap: 0.55rem;
            background:
                repeating-linear-gradient(0deg, rgba(31, 77, 37, .07) 0px, rgba(31, 77, 37, .07) 1px, transparent 2px, transparent 4px),
                radial-gradient(ellipse at 50% 45%, #F8FBEA 0%, #EEF5D6 55%, #D9E8AE 85%, #B7D27F 100%);
            border: clamp(6px, 0.8vw, 12px) solid #234B22;
            box-shadow: inset 0 0 0 3px #8FB05A, inset 0 0 70px rgba(70, 125, 35, .55),
                        0 0 0 clamp(6px, 0.8vw, 12px) #D3C5A6, 0 0 0 clamp(8px, 1vw, 15px) #B9A884;
        }

        /* 창 제목 줄: 픽셀 컴퓨터 + BUG TRACE + 경로 + 창 버튼 */
        .win-bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-bottom: 6px; border-bottom: 3px solid var(--ink); }
        .win-logo { display: flex; align-items: center; gap: 10px; }
        .win-logo .px-computer { width: 64px; height: auto; }
        .win-title { font-family: 'Press Start 2P', monospace; font-size: 1.55rem; color: var(--ink); letter-spacing: 1px; }
        .win-path { flex: 1; font-family: 'Galmuri11', monospace; font-weight: 700; color: var(--ink); font-size: 0.95rem; text-align: right; }
        /* 진짜 창 버튼(— □ ×): 작은 정사각형 픽셀 버튼, 오른쪽 끝에 붙인다 */
        .st-key-win_btns { justify-content: flex-end; gap: 4px; }
        .st-key-win_btns div.stButton { padding-top: 0; }
        .st-key-win_btns div.stButton button { min-height: 34px; width: 40px; min-width: 40px; padding: 0; margin: 4px; }
        .st-key-win_btns div.stButton button p { font-family: 'Noto Sans KR', sans-serif !important; font-size: 1.1rem !important; font-weight: 900 !important; }
        .st-key-win_btns div.stButton button:hover { background: var(--lime); }
        /* 최소화: 내용 상자를 숨기고 안내 한 줄만 보여 준다 */
        .st-key-win_hidden { display: none !important; }
        .win-min-note { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); background: var(--paper); border: 3px dashed var(--ink); padding: 10px 14px; }
        /* 최대화: 베이지 틀을 얇게 줄여서 화면이 브라우저를 꽉 채운다 */
        .st-key-crt_max { background: #D9CCAE; border: 3px solid #B9A884; border-radius: 16px; padding: 6px; gap: 0; }
        @keyframes blink { 50% { opacity: 0; } }

        /* 모니터 아래쪽: 스피커, 불빛, 플로피 디스크, 전원 버튼 */
        .px-panel { display: flex; align-items: center; justify-content: space-between; gap: 2vw; padding: clamp(12px, 1.6vw, 26px) 1vw 2px; }
        .px-screw { width: 14px; height: 14px; border-radius: 50%; background: #D8CAAA; border: 2px solid #9C8D6E; box-shadow: inset 2px 2px 0 #F3EAD4; }
        .px-grill { width: 15vw; max-width: 240px; height: 38px; background: repeating-linear-gradient(0deg, #7E735C 0 4px, transparent 4px 9px); border-radius: 3px; }
        .px-leds { display: flex; gap: 14px; }
        .px-leds span { width: 18px; height: 18px; border-radius: 50%; border: 3px solid #6C6450; }
        /* 초록 불빛: 컴퓨터가 일하는 것처럼 불규칙하게 깜빡인다 */
        .px-led-on { background: #6BD43C; box-shadow: 0 0 10px #6BD43C; animation: led 2.4s steps(1) infinite; }
        @keyframes led { 0%, 30%, 55%, 100% { opacity: 1; } 25%, 50%, 70% { opacity: .35; } }
        .px-led-dim { background: #A39324; }
        /* 플로피 디스크 입구: 틀 + 검은 틈 + 꺼내는 버튼 */
        .px-floppy { width: 22vw; max-width: 360px; height: 58px; border: 3px solid #A99B7E; border-radius: 5px; background: linear-gradient(180deg, #F3EAD5, #E2D5B8); position: relative; box-shadow: inset 0 2px 0 #FFF8E8; }
        .px-floppy::before { content: ""; position: absolute; left: 7%; right: 26%; top: 22px; height: 10px; background: #2F2B22; border-radius: 2px; }
        .px-floppy::after { content: ""; position: absolute; right: 6%; top: 17px; width: 15%; height: 20px; background: #F7F0DE; border: 3px solid #A99B7E; border-radius: 3px; }
        /* 진짜 전원 버튼 (라임색, 누르면 첫 화면으로) */
        .st-key-power { padding-top: clamp(14px, 1.8vw, 28px); }   /* 화면 테두리와 겹치지 않게 아래로 */
        .st-key-power div.stButton { padding-top: 0; }
        .st-key-power div.stButton button { background: var(--lime); min-height: 56px; width: 76px; min-width: 76px; padding: 0; }
        .st-key-power div.stButton button [data-testid="stIconMaterial"] { font-size: 2rem !important; margin-right: 0; }
        .st-key-power div.stButton button:hover { background: #D7F57E; }

        /* ===== 6) 픽셀 테두리 (모서리가 한 칸 비는 도트 느낌)
           테두리(border) 대신 위·아래·왼쪽·오른쪽 그림자 4개를 붙인다. 그림자끼리 모서리에서 만나지 않아 계단처럼 보인다. ===== */
        /* 두꺼운 픽셀 버튼: 진한 초록 그림자 4개(테두리) + 안쪽 아래 그림자(입체감) + 바깥 아래 그림자(바닥에 놓인 느낌)
           "div.stButton button"(띄어쓰기) = 버튼이 상자 안 몇 겹 아래에 있어도 적용된다. (설명 말풍선이 있는 버튼도 포함) */
        div.stButton button, div[data-testid="stPageLink"] a {
            border: none !important; border-radius: 0; margin: 5px 5px 10px; min-height: 48px; padding: 6px 14px;
            background: var(--paper); transition: background-color .12s ease, transform .08s ease;
            box-shadow: 0 -5px 0 0 var(--ink), 0 5px 0 0 var(--ink), -5px 0 0 0 var(--ink), 5px 0 0 0 var(--ink),
                        inset 0 -5px 0 0 rgba(31, 77, 37, .14), 0 10px 0 0 rgba(31, 77, 37, .28) !important;
        }
        div.stButton button:active, div[data-testid="stPageLink"] a:active { transform: translateY(3px); }   /* 누르면 살짝 내려간다 */
        div.stButton button p, div[data-testid="stPageLink"] a p {
            font-family: 'Galmuri11', 'Noto Sans KR', sans-serif !important; font-size: 1.05rem !important;
            font-weight: 700 !important; color: var(--ink) !important;
        }
        div.stButton button [data-testid="stIconMaterial"], div[data-testid="stPageLink"] a [data-testid="stIconMaterial"] { color: var(--ink) !important; font-weight: 700; margin-right: 8px; }   /* margin-right: 아이콘과 글자 사이 간격 */
        div.stButton button:hover, div[data-testid="stPageLink"] a:hover { background: var(--lime-soft); }
        div.stButton button[kind="primary"] { background: var(--lime); }
        div.stButton { padding-top: 8px; }   /* 버튼 위쪽 여백: 바로 위 글 상자와 픽셀 테두리가 겹치지 않게 */
        div.stButton button[kind="primary"]:hover { background: #D7F57E; }
        /* 메뉴 버튼: 지금 있는 페이지는 라임색 */
        .st-key-nav_active div[data-testid="stPageLink"] a { background: var(--lime) !important; }
        div[data-testid="stPageLink"] a { justify-content: center; }
        div[data-testid="stPageLink"] a > span:first-child { margin-right: 10px; }   /* 아이콘을 감싼 칸 오른쪽에 간격 → 아이콘과 글자가 붙지 않게 */
        button:focus-visible, input:focus-visible, a:focus-visible { outline: 3px solid var(--sky) !important; outline-offset: 3px; }

        /* ===== 7) 페이지 배너 (예: ERROR CATALOG · 오류 도감) ===== */
        .bt-banner {
            background: var(--lime); margin: 10px 6px 14px; padding: 10px 18px; text-align: center;
            box-shadow: 0 -5px 0 0 var(--ink), 0 5px 0 0 var(--ink), -5px 0 0 0 var(--ink), 5px 0 0 0 var(--ink);
        }
        .bt-banner-main { display: flex; align-items: center; justify-content: center; gap: 14px; color: var(--ink); }
        .bt-banner-main .bt-icon { font-size: 2rem; }
        .bt-banner-en { font-family: 'Press Start 2P', monospace; font-size: 1.45rem; }
        .bt-banner-ko { font-family: 'Galmuri11', sans-serif; font-weight: 700; font-size: 1.2rem; }
        .bt-banner-desc { color: var(--ink); font-size: 0.92rem; font-weight: 600; margin-top: 4px; }

        /* ===== 8) 오류 카드 ===== */
        .bt-card-top { display: flex; justify-content: space-between; align-items: center; }
        .bt-no { font-family: 'Galmuri11', monospace; color: var(--ink); font-size: 0.85rem; font-weight: 700; }
        .bt-tag { font-family: 'Galmuri11', sans-serif; color: var(--ink); font-size: 0.85rem; font-weight: 700; background: var(--lime-soft); border: 2px solid var(--ink); padding: 2px 8px; }
        .bt-card-title { color: var(--ink); font-size: 1.05rem; font-weight: 800; line-height: 1.4; margin-top: 8px; }
        .bt-card-nick { color: #2F6B2A; font-size: 0.9rem; font-weight: 700; margin: 2px 0 4px 0; }
        /* 요약은 두 줄까지만 보여 준다 (카드 높이를 일정하게, 스크롤을 줄이려고) */
        .bt-card-summary { color: var(--dim); font-size: 0.88rem; line-height: 1.55; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

        /* ===== 9) 테두리 상자, 입력창, 선택 상자, 탭 ===== */
        div[data-testid="stVerticalBlockBorderWrapper"] { background: var(--paper); border-radius: 0; border: 3px solid var(--ink); padding: 10px 12px; }
        div[data-baseweb="input"] > div, div[data-baseweb="select"] > div { min-height: 44px; border-radius: 0; background-color: #FFFFFF; border: 3px solid var(--ink); }
        [data-testid="stWidgetLabel"] p { font-family: 'Noto Sans KR', sans-serif !important; font-weight: 700 !important; color: var(--ink) !important; }
        div[data-testid="stCodeBlock"], pre { border-radius: 0; }
        [data-testid="stTabs"] button p { font-family: 'Noto Sans KR', sans-serif !important; font-weight: 800 !important; font-size: 1rem !important; color: var(--ink) !important; }
        /* 현상 실험실 꺾은선 그래프(SVG) */
        .lab-chart { width: 100%; height: auto; margin-bottom: 14px; background: var(--paper); border: 3px solid var(--ink); font-family: 'Noto Sans KR', sans-serif; }
        /* 실험 실행 전, 결과가 나올 자리의 안내 상자 (점선 테두리) */
        .lab-waiting { border: 3px dashed var(--ink); background: rgba(251, 253, 241, .6); color: var(--ink); text-align: center;
                       padding: 40px 16px; line-height: 1.8; font-size: 0.98rem; min-height: 330px; display: flex; flex-direction: column; justify-content: center; }
        .lab-waiting-icon { font-family: 'Press Start 2P', monospace; font-size: 1.8rem; margin-bottom: 8px; }
        .stMarkdown a { color: #2F6B2A; text-decoration: underline; font-weight: 600; }
        hr { border-color: var(--ink) !important; opacity: .3; margin: 0.4rem 0 !important; }

        /* 분류 선택(라디오)을 픽셀 칩 버튼처럼 */
        div[data-testid="stRadio"] > div[role="radiogroup"] { display: flex; flex-wrap: wrap; gap: 8px 10px; }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label {
            display: inline-flex; align-items: center; justify-content: center; min-height: 42px; min-width: 88px;
            padding: 6px 14px; margin: 4px; background: var(--paper); cursor: pointer;
            box-shadow: 0 -3px 0 0 var(--ink), 0 3px 0 0 var(--ink), -3px 0 0 0 var(--ink), 3px 0 0 0 var(--ink);
        }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:hover { background: var(--lime-soft); }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label:has(input:checked) { background: var(--lime); }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label p { font-family: 'Galmuri11', sans-serif !important; font-size: 0.98rem !important; font-weight: 700 !important; color: var(--ink) !important; }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label [data-testid="stIconMaterial"] { color: var(--ink) !important; }
        div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child { width: 0; height: 0; overflow: hidden; margin: 0; padding: 0; }   /* 동그란 라디오 표시 숨기기 */

        /* ===== 11) 설명 상자 (정상 = 초록, 오류 = 벽돌, 핵심 = 황토, 관찰 = 파랑) ===== */
        .bt-box { background: var(--paper); border: 2px solid var(--ink); padding: 12px 16px; margin-bottom: 8px; color: var(--text); line-height: 1.75; font-size: 1rem; }
        .bt-box-label { font-family: 'Galmuri11', monospace; font-size: 0.92rem; font-weight: 700; margin-bottom: 5px; }
        .bt-ok { border-left: 8px solid #2F6B2A; } .bt-ok .bt-box-label { color: #2F6B2A; }
        .bt-obs { border-left: 8px solid var(--sky); } .bt-obs .bt-box-label { color: var(--sky); }
        .bt-err { border-left: 8px solid var(--red); } .bt-err .bt-box-label { color: var(--red); }
        .bt-key { border-left: 8px solid var(--yellow); } .bt-key .bt-box-label { color: var(--yellow); }

        /* 처리 과정 그림 (입력 → 처리 → 출력) */
        .bt-flow { display: flex; align-items: stretch; gap: 8px; margin: 2px 0 6px 0; }
        .bt-flow-box { flex: 1; text-align: center; padding: 8px 8px; border: 3px solid var(--ink); background: var(--lime-soft); }
        .bt-flow-box .bt-icon { font-size: 1.6rem; color: var(--ink); }
        .bt-flow-name { font-family: 'Galmuri11', sans-serif; color: var(--ink); font-weight: 700; margin: 2px 0; }
        .bt-flow-text { color: var(--text); font-size: 0.97rem; line-height: 1.55; }
        .bt-flow-out { border-color: var(--red); background: #FBE7DF; }
        .bt-flow-out .bt-icon, .bt-flow-out .bt-flow-name { color: var(--red); }
        .bt-flow-arrow { align-self: center; color: var(--ink); font-size: 1.4rem; font-weight: 800; }

        /* 단계별 추적 기록 (#01 → #02 …) */
        .bt-step { display: flex; gap: 10px; align-items: flex-start; }
        .bt-step-no { flex: 0 0 44px; height: 36px; text-align: center; line-height: 32px; background: var(--lime); color: var(--ink); border: 2px solid var(--ink); font-family: 'Galmuri11', monospace; font-weight: 700; }
        .bt-step-text { line-height: 1.6; font-size: 0.93rem; color: var(--text); }
        .bt-basis { display: inline-block; font-family: 'Galmuri11', monospace; font-size: 0.78rem; font-weight: 700; padding: 0 6px; margin-bottom: 2px; background: var(--paper); }
        .bt-basis-ok { color: #2F6B2A; border: 2px solid #2F6B2A; }
        .bt-basis-guess { color: var(--yellow); border: 2px solid var(--yellow); }

        /* 작은 이름표 (BUG-001, 분류, 기술 등) */
        .bt-badge { display: inline-block; font-family: 'Galmuri11', monospace; font-size: 0.82rem; font-weight: 700; border: 2px solid var(--ink); padding: 1px 8px; margin: 0 4px 4px 0; color: var(--ink); background: var(--paper); }
        .bt-badge-on { background: var(--lime); }

        /* ===== 11-1) 고정된 모니터 안에서만 스크롤 =====
           모니터 틀·창 제목 줄·메뉴는 그대로 두고, 페이지 내용 상자(win_body)만 정해진 높이 안에서 스크롤한다.
           100vh = 브라우저 창 높이. --chrome = 모니터 틀·제목 줄·메뉴·아래 패널이 차지하는 높이 */
        :root { --chrome: 375px; --chrome-max: 200px; }
        html, body { overflow: hidden; }                                   /* 페이지 전체는 스크롤하지 않는다 */
        [data-testid="stMain"] { overflow: hidden; }
        /* !important: Streamlit이 상자에 자동으로 넣는 높이 설정보다 우선하게 한다 */
        .st-key-win_body { height: calc(100vh - var(--chrome)) !important; max-height: calc(100vh - var(--chrome)) !important; flex: none !important;
                           overflow-y: auto !important; overflow-x: hidden; padding: 4px 14px 24px 4px; }
        .st-key-crt_max .st-key-win_body { height: calc(100vh - var(--chrome-max)) !important; max-height: calc(100vh - var(--chrome-max)) !important; }
        /* 스크롤 막대도 픽셀 느낌으로 */
        .st-key-win_body::-webkit-scrollbar { width: 14px; }
        .st-key-win_body::-webkit-scrollbar-track { background: var(--lime-soft); border-left: 3px solid var(--ink); }
        .st-key-win_body::-webkit-scrollbar-thumb { background: var(--ink); border: 3px solid var(--lime-soft); }

        /* ===== 11-2) 핵심 원리 강조 상자 (가장 눈에 띄게) ===== */
        .bt-keypoint { display: flex; gap: 14px; align-items: center; background: var(--lime); color: var(--ink); padding: 16px 20px; margin: 10px 6px 14px;
                       box-shadow: 0 -5px 0 0 var(--ink), 0 5px 0 0 var(--ink), -5px 0 0 0 var(--ink), 5px 0 0 0 var(--ink), 0 10px 0 0 rgba(31,77,37,.25); }
        .bt-keypoint .bt-icon { font-size: 2.4rem; }
        .bt-keypoint-label { font-family: 'Galmuri11', monospace; font-weight: 700; font-size: 0.9rem; }
        .bt-keypoint-text { font-family: 'Noto Sans KR', sans-serif; font-weight: 800; font-size: 1.18rem; line-height: 1.55; }

        /* ===== 11-3) 먼저 알아 둘 용어 (카드 4장) ===== */
        .bt-terms { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin-bottom: 6px; }
        .bt-term { background: var(--paper); border: 2px solid var(--ink); border-top: 6px solid var(--ink); padding: 10px 12px; }
        .bt-term-name { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: 1rem; margin-bottom: 4px; }
        .bt-term-desc { font-size: 0.95rem; line-height: 1.6; color: var(--text); }

        /* ===== 11-4) 구역 제목 (SYMPTOM · 어떤 현상인가 등) ===== */
        .sec-label { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: 1.08rem;
                     border-bottom: 3px solid var(--ink); padding-bottom: 4px; margin: 22px 0 10px; }

        /* ===== 11-5) 사례 선택 상자: 눈에 잘 띄게 (라임색 띠 + 큰 글자) ===== */
        .st-key-case_pick { background: var(--lime); padding: 10px 14px 12px; margin: 4px 6px 6px;
                            box-shadow: 0 -4px 0 0 var(--ink), 0 4px 0 0 var(--ink), -4px 0 0 0 var(--ink), 4px 0 0 0 var(--ink); }
        .st-key-case_pick [data-testid="stWidgetLabel"] p { font-family: 'Galmuri11', sans-serif !important; font-size: 1.05rem !important; }
        .st-key-case_pick div[data-baseweb="select"] > div { min-height: 52px; border-width: 4px; }
        .st-key-case_pick div[data-baseweb="select"] div { font-size: 1.1rem; font-weight: 700; color: var(--ink); }

        /* ===== 11-6) '문서로 확인' 이름표 = 누르면 공식 문서가 새 탭에서 열리는 링크 ===== */
        a.bt-basis-ok { text-decoration: none !important; cursor: pointer; }
        a.bt-basis-ok:hover { background: var(--lime); }

        /* ===== 11-7) 오류 도감의 넓은 사례 카드 ===== */
        .cat-head { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
        .cat-title { font-family: 'Noto Sans KR', sans-serif; font-weight: 800; color: var(--ink); font-size: 1.3rem; margin: 6px 0 2px; }
        .cat-summary { font-size: 1rem; line-height: 1.7; color: var(--text); margin: 4px 0 8px; }
        .cat-terms { display: flex; flex-wrap: wrap; gap: 6px; }
        .cat-terms span { font-size: 0.9rem; background: var(--lime-soft); border: 2px solid var(--ink); padding: 2px 8px; color: var(--ink); }
        .cat-terms b { font-family: 'Galmuri11', sans-serif; }
        .cat-flow { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 6px 0 12px; font-family: 'Galmuri11', sans-serif; color: var(--ink); }
        .cat-flow span { background: var(--paper); border: 2px solid var(--ink); padding: 3px 10px; font-weight: 700; }
        /* ===== 12) 좁은 화면(휴대폰) ===== */
        @media (max-width: 800px) {
            .st-key-crt { padding: 10px 8px 6px; border-radius: 18px; }
            .st-key-crt_screen { padding: 8px 8px 12px; border-width: 4px; border-radius: 14px; }
            .win-title { font-size: 0.95rem; } .win-path { display: none; }
            .win-logo .px-computer { width: 40px; }
            .bt-banner-en { font-size: 0.9rem; } .bt-banner-ko { font-size: 1rem; }
            .px-grill, .px-floppy { display: none; }
            .bt-flow { flex-direction: column; } .bt-flow-arrow { transform: rotate(90deg); }
            html, body, [data-testid="stMain"] { overflow: auto; }          /* 휴대폰은 화면이 작아서 페이지 전체 스크롤 */
            .st-key-win_body { height: auto !important; max-height: none !important; overflow: visible !important; }
        }
        @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; } }
        </style>
    """)
