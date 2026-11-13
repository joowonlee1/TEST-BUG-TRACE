# =============================================================
# pages/home.py  (홈 = 첫 화면)
# 깔끔한 시작 화면: CRT 모니터 안에 픽셀 컴퓨터, BUG TRACE 제목,
# 웹앱 간단 소개, "연구소 들어가기" 버튼만 놓는다.
# =============================================================

import streamlit as st

from common import PIXEL_COMPUTER_SVG, render_html, show_monitor_panel

# 제목 상자 옆에 놓을 픽셀 마우스 커서 그림 (1칸짜리 사각형을 쌓아서 그린다)
PIXEL_CURSOR_SVG = """
<svg class="home-cursor" viewBox="0 0 12 18" shape-rendering="crispEdges" xmlns="http://www.w3.org/2000/svg">
<path fill="#1F4D25" d="M0 0h1v1H0zM0 1h2v1H0zM0 2h3v1H0zM0 3h4v1H0zM0 4h5v1H0zM0 5h6v1H0zM0 6h7v1H0zM0 7h8v1H0zM0 8h9v1H0zM0 9h10v1H0zM0 10h6v1H0zM0 11h3v1H0zM4 11h3v1H4zM0 12h2v1H0zM5 12h2v2H5zM0 13h1v1H0zM6 14h2v2H6z"/>
<path fill="#FBFDF1" d="M1 2h1v1H1zM1 3h2v1H1zM1 4h3v1H1zM1 5h4v1H1zM1 6h5v1H1zM1 7h6v1H1zM1 8h7v1H1zM1 9h3v1H1zM5 9h2v1H5zM1 10h1v1H1z"/>
</svg>
"""


def apply_home_style():
    """첫 화면에만 쓰는 디자인: 화면 높이를 채우는 모니터, 큰 컴퓨터·제목, 소개 상자, 큰 시작 버튼"""
    render_html("""
        <style>
        /* 모니터 화면이 브라우저 높이를 거의 채우고, 내용은 위아래 가운데에 오게 한다 */
        /* 100vh = 브라우저 창 높이. 모니터 틀과 아래쪽 패널 높이(약 280px)를 빼서 한 화면에 다 보이게 한다 */
        .st-key-crt_screen { min-height: calc(100vh - 280px); justify-content: center; }

        /* 화면 네 귀퉁이의 ㄱ자 빗금 무늬 (가로 빗금 + 아래로 짧은 세로 빗금) */
        .home-corners { display: flex; justify-content: space-between; }
        .home-corner { width: 20%; }
        .home-corner b { display: block; height: 16px; background: repeating-linear-gradient(-60deg, #6F9A3A 0 6px, transparent 6px 13px); }
        .home-corner i { display: block; width: 26px; height: 34px; margin-top: 4px; background: repeating-linear-gradient(-60deg, #6F9A3A 0 6px, transparent 6px 13px); }
        .home-corner.right i { margin-left: auto; }
        .home-corners.bottom { align-items: flex-end; }
        .home-corners.bottom .home-corner i { margin: 0 0 4px 0; }
        .home-corners.bottom .home-corner.right i { margin-left: auto; }

        /* 픽셀 컴퓨터 + 제목 상자 (화면 크기에 맞춰 커진다: vw = 화면 폭의 1%) */
        .home-hero { text-align: center; margin-top: -2vh; }
        .home-hero .px-computer { width: clamp(130px, 12vw, 230px); height: auto; display: block; margin: 0 auto -0.4vw; }
        .home-title-wrap { display: inline-flex; align-items: flex-end; }
        .home-title-box {
            position: relative; background: #FBFDF1; padding: 1.6vw 4.6vw 1.2vw; margin: 9px;
            box-shadow: 0 -8px 0 0 var(--ink), 0 8px 0 0 var(--ink), -8px 0 0 0 var(--ink), 8px 0 0 0 var(--ink),
                        inset 0 -6px 0 0 rgba(31, 77, 37, .12), 0 16px 0 0 rgba(31, 77, 37, .25);
        }
        /* 제목 상자 네 귀퉁이 안쪽의 작은 라임색 점 */
        .home-title-box span { position: absolute; width: 10px; height: 10px; background: #B9DC6A; }
        .home-title-box .tl { left: 6px; top: 6px; } .home-title-box .tr { right: 6px; top: 6px; }
        .home-title-box .bl { left: 6px; bottom: 6px; } .home-title-box .br { right: 6px; bottom: 6px; }
        .home-title { font-family: 'Press Start 2P', monospace; font-size: clamp(2rem, 5vw, 4.8rem); color: var(--ink); line-height: 1.1; }
        .home-cursor { width: clamp(28px, 3vw, 48px); margin: 0 0 -1.6vw -2vw; }

        /* 웹앱 간단 소개 */
        .home-intro { max-width: 900px; margin: 2.2vh auto 0.6vh; text-align: center; }
        .home-intro-main { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: clamp(1.05rem, 1.5vw, 1.5rem); line-height: 1.6; }
        .home-intro-sub { color: var(--dim); font-size: clamp(0.92rem, 1.05vw, 1.1rem); margin-top: 6px; }
        .home-chips { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; margin: 14px 0 18px; }
        .home-chips span { font-family: 'Galmuri11', monospace; font-weight: 700; color: var(--ink); font-size: 0.95rem; background: #FBFDF1; border: 3px solid var(--ink); padding: 4px 12px; }

        /* "연구소 들어가기" 큰 시작 버튼 */
        .st-key-enter_lab div[data-testid="stPageLink"] a { min-height: clamp(60px, 8vh, 84px); background: var(--lime) !important; }
        .st-key-enter_lab div[data-testid="stPageLink"] a p { font-size: clamp(1.3rem, 1.9vw, 1.9rem) !important; }
        .st-key-enter_lab div[data-testid="stPageLink"] a [data-testid="stIconMaterial"] { font-size: clamp(1.8rem, 2.4vw, 2.6rem) !important; }
        .st-key-enter_lab div[data-testid="stPageLink"] a:hover { background: #D7F57E !important; }

        @media (max-width: 800px) {
            .home-title-box { padding: 14px 18px 10px; }
            .home-cursor, .home-corner i { display: none; }
        }
        </style>
    """)


def show_corners(position):
    """화면 위쪽(top) 또는 아래쪽(bottom) 양 귀퉁이에 ㄱ자 빗금 무늬를 그린다."""
    # 위쪽은 가로 빗금이 먼저, 아래쪽은 세로 빗금이 먼저 오도록 순서를 바꾼다.
    if position == "top":
        corner = "<b></b><i></i>"
    else:
        corner = "<i></i><b></b>"
    render_html(f"""
        <div class="home-corners {position}">
            <div class="home-corner left">{corner}</div>
            <div class="home-corner right">{corner}</div>
        </div>
    """)


def show_hero():
    """픽셀 컴퓨터 그림 + BUG TRACE 제목 상자(+ 픽셀 커서)"""
    render_html(f"""
        <div class="home-hero">
            {PIXEL_COMPUTER_SVG}
            <div class="home-title-wrap">
                <div class="home-title-box"><span class="tl"></span><span class="tr"></span><span class="bl"></span><span class="br"></span><div class="home-title">BUG TRACE</div></div>
                {PIXEL_CURSOR_SVG}
            </div>
        </div>
    """)


def show_intro():
    """웹앱 간단 소개: 무엇을 하는 곳인지 한두 줄 + 다루는 주제 이름표"""
    render_html("""
        <div class="home-intro">
            <div class="home-intro-main">조회수가 갑자기 음수가 되고, 0.1 + 0.2가 0.3이 아닌 이유는?<br>숫자를 정해진 비트에 저장하는 컴퓨터의 한계를 추적하는 디지털 오류 연구소</div>
            <div class="home-intro-sub">2가지 사례를 공식 문서를 근거로 깊이 추적하고, 직접 계산해서 확인해요.</div>
            <div class="home-chips"><span>정수 오버플로·언더플로</span><span>2038년 문제</span><span>실수 정밀도 오차·언더플로</span><span>오류 검출</span></div>
        </div>
    """)


def show_enter_button():
    """'연구소 들어가기' 버튼: 누르면 오류 도감 페이지로 이동한다."""
    # 가운데 칸에만 버튼을 놓아서 화면 가운데에 오게 한다. (왼쪽·오른쪽 칸은 비워 둔다)
    left_space, button_column, right_space = st.columns([1, 1.2, 1])
    with button_column:
        with st.container(key="enter_lab"):
            st.page_link("pages/catalog.py", label="연구소 들어가기", icon=":material/play_arrow:", width="stretch")


# ----- 실제 실행 순서 -----
apply_home_style()                                   # 1) 첫 화면 디자인

with st.container(key="crt"):                        # 2) 모니터 바깥 틀
    with st.container(key="crt_screen"):             # 3) 모니터 화면
        show_corners("top")                          #    위쪽 귀퉁이 빗금
        show_hero()                                  #    픽셀 컴퓨터 + 제목
        show_intro()                                 #    웹앱 간단 소개
        show_enter_button()                          #    연구소 들어가기 버튼
        show_corners("bottom")                       #    아래쪽 귀퉁이 빗금
    show_monitor_panel()                             # 4) 모니터 아래쪽 (스피커·불빛·플로피·전원)
