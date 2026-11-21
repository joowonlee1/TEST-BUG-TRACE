# =============================================================
# pages/home.py  (홈 = 첫 화면)
# 깔끔한 시작 화면: CRT 모니터 안에 픽셀 컴퓨터, BUG TRACE 제목,
# 웹앱 간단 소개, "연구소 들어가기" 버튼만 놓는다.
# =============================================================

import streamlit as st

from common import PIXEL_COMPUTER_SVG, render_html, show_monitor_panel


def apply_home_style():
    """첫 화면에만 쓰는 디자인: 화면 높이를 채우는 모니터, 큰 컴퓨터·제목, 소개 상자, 큰 시작 버튼"""
    render_html("""
        <style>
        /* 모니터는 common.py에서 브라우저 높이에 딱 맞춰진다. 내용은 위아래 가운데에 놓고,
           노트북처럼 화면이 낮으면 그림과 글자를 vh(화면 높이의 1%) 기준으로 줄여서 한 화면에 다 들어오게 한다 */
        .st-key-crt_screen { justify-content: center; overflow-y: auto; }
        /* 첫 화면은 디자인(CSS) 상자가 모니터 위에 한 칸 더 있어서, 그만큼(20px) 모니터를 낮춘다 */
        [data-testid="stLayoutWrapper"]:has(> .st-key-crt) { height: calc(100vh - 46px); }

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
        .home-hero { text-align: center; }
        /* min(가로 기준, 세로 기준): 둘 중 작은 값 → 화면이 낮으면 세로 기준으로 작아진다 */
        .home-hero .px-computer { width: clamp(80px, min(12vw, 15vh), 230px); height: auto; display: block; margin: 0 auto -0.4vw; }
        .home-title-wrap { display: inline-flex; align-items: flex-end; }
        .home-title-box {
            position: relative; background: #FBFDF1; padding: min(1.6vw, 2.2vh) 4.6vw min(1.2vw, 1.6vh); margin: 9px;
            box-shadow: 0 -8px 0 0 var(--ink), 0 8px 0 0 var(--ink), -8px 0 0 0 var(--ink), 8px 0 0 0 var(--ink),
                        inset 0 -6px 0 0 rgba(31, 77, 37, .12), 0 16px 0 0 rgba(31, 77, 37, .25);
        }
        /* 제목 상자 네 귀퉁이 안쪽의 작은 라임색 점 */
        .home-title-box span { position: absolute; width: 10px; height: 10px; background: #B9DC6A; }
        .home-title-box .tl { left: 6px; top: 6px; } .home-title-box .tr { right: 6px; top: 6px; }
        .home-title-box .bl { left: 6px; bottom: 6px; } .home-title-box .br { right: 6px; bottom: 6px; }
        .home-title { font-family: 'Press Start 2P', monospace; font-size: clamp(1.8rem, min(5vw, 8vh), 4.8rem); color: var(--ink); line-height: 1.1; }

        /* 웹앱 간단 소개 */
        .home-intro { max-width: 900px; margin: 1.6vh auto 0.4vh; text-align: center; }
        .home-intro-main { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: clamp(1.05rem, 1.5vw, 1.5rem); line-height: 1.6; }
        .home-intro-sub { font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); font-size: clamp(0.95rem, 1.2vw, 1.2rem); margin-top: 2px; }
        /* 화면 배율 안내: 상자 없이 작은 글 한 줄 (첫 화면을 깔끔하게) */
        .home-zoom { margin: 1.2vh 0 1.8vh; color: var(--dim); font-size: clamp(0.82rem, 0.9vw, 0.95rem); }
        /* 글 상자 아래의 기본 -16px 여백 때문에 배율 안내가 버튼에 가려져서 0으로 되돌린다 */
        .st-key-crt_screen [data-testid="stMarkdownContainer"]:has(.home-intro) { margin-bottom: 0 !important; }

        /* "연구소 들어가기" 큰 시작 버튼 */
        .st-key-enter_lab div[data-testid="stPageLink"] a { min-height: clamp(48px, 8vh, 84px); background: var(--lime) !important; }
        .st-key-enter_lab div[data-testid="stPageLink"] a p { font-size: clamp(1.3rem, 1.9vw, 1.9rem) !important; }
        .st-key-enter_lab div[data-testid="stPageLink"] a [data-testid="stIconMaterial"] { font-size: clamp(1.8rem, 2.4vw, 2.6rem) !important; }
        .st-key-enter_lab div[data-testid="stPageLink"] a:hover { background: #D7F57E !important; }

        @media (max-width: 800px) {
            .home-title-box { padding: 14px 18px 10px; }
            .home-corner i { display: none; }
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
            </div>
        </div>
    """)


def show_intro():
    """웹앱 간단 소개: 질문 한 줄 + 설명 한 줄 + 배율 안내 한 줄 (꼭 필요한 것만 남겨 깔끔하게)"""
    render_html("""
        <div class="home-intro">
            <div class="home-intro-main">조회수가 갑자기 음수가 되고, 0.1 + 0.2가 0.3이 아닌 이유는?</div>
            <div class="home-intro-sub">숫자 저장의 한계를 추적하는 디지털 오류 연구소</div>
            <div class="home-zoom">화면 배율 <b>100%</b>에서 가장 잘 보여요 (Ctrl + 0)</div>
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
