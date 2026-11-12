# =============================================================
# pages/home.py  (홈)
# 레트로 컴퓨터 책상 장면으로 BUG TRACE를 소개하고,
# 4개 페이지로 가는 메뉴 카드와 대표 오류 3개를 보여 준다.
# =============================================================

import streamlit as st

from common import case_card, find_case, load_cases, open_case, render_html

# 홈에서 보여 줄 대표 오류 번호 (가장 많이 겪는 오류 3개)
FEATURED_CASE_IDS = [1, 2, 3]

# 메뉴 카드 내용: (페이지 파일, 메뉴 이름, 아이콘, 설명)
MENU_CARDS = [
    ("pages/catalog.py", "오류 도감", ":material/menu_book:", "12가지 디지털 오류 사례 모음"),
    ("pages/anatomy.py", "원인 해부실", ":material/layers:", "오류가 발생하는 내부 원리 분석"),
    ("pages/laboratory.py", "현상 실험실", ":material/science:", "직접 실행하며 확인하는 실험"),
    ("pages/compare.py", "오류 비교실", ":material/compare_arrows:", "두 오류의 공통점과 차이점 분석"),
]


def apply_home_style():
    """홈에만 쓰는 디자인: 레트로 모니터, 책, 메모지, 머그컵, 바닥 격자"""
    render_html("""
        <style>
        /* ---------- 장면 전체 ---------- */
        .scene {
            position: relative; overflow: hidden; border-radius: 22px; height: 470px;
            border: 1px solid var(--bt-line);
            background: radial-gradient(ellipse at 50% 35%, #1d2a14 0%, #0d130c 55%, #070a07 100%);
        }
        /* 바닥의 라임색 격자 (원근감) */
        .scene-floor {
            position: absolute; left: -20%; right: -20%; bottom: -40px; height: 210px;
            background-image:
                linear-gradient(rgba(183,230,107,.28) 1px, transparent 1px),
                linear-gradient(90deg, rgba(183,230,107,.28) 1px, transparent 1px);
            background-size: 46px 46px;
            transform: perspective(380px) rotateX(62deg);
            mask-image: linear-gradient(to top, black 10%, transparent 95%);
            -webkit-mask-image: linear-gradient(to top, black 10%, transparent 95%);
        }

        /* ---------- 가운데 레트로 모니터 ---------- */
        .crt {
            position: absolute; left: 50%; top: 34px; transform: translateX(-50%);
            width: 560px; padding: 20px 22px 34px; border-radius: 34px;
            background: linear-gradient(180deg, #6d6a5e 0%, #4c4a40 100%);
            box-shadow: 0 0 60px rgba(183,230,107,.25), inset 0 2px 0 rgba(255,255,255,.15);
        }
        .crt-screen {
            position: relative; overflow: hidden; border-radius: 22px; padding: 14px 26px 22px;
            background: radial-gradient(ellipse at center, #1e3012 0%, #0e1709 75%, #070b05 100%);
            border: 2px solid var(--bt-lime); box-shadow: inset 0 0 40px rgba(0,0,0,.8), 0 0 24px rgba(183,230,107,.35);
            color: var(--bt-lime); text-align: center;
        }
        /* 화면 위 가로줄(주사선) */
        .crt-screen::after {
            content: ""; position: absolute; inset: 0; pointer-events: none;
            background: repeating-linear-gradient(0deg, rgba(0,0,0,.22) 0px, rgba(0,0,0,.22) 1px, transparent 2px, transparent 4px);
        }
        /* 창 제목 줄: >_ BUG_TRACE.exe   — □ × */
        .crt-bar {
            display: flex; justify-content: space-between; font-family: 'Nanum Gothic Coding', monospace;
            font-size: .85rem; border-bottom: 1px solid var(--bt-lime-line); padding-bottom: 6px; margin-bottom: 16px;
        }
        .crt-logo {
            font-family: 'VT323', monospace; font-size: 5rem; line-height: .95; letter-spacing: 3px;
            color: #d6ff8f; text-shadow: 0 0 12px rgba(183,230,107,.9), 0 0 30px rgba(183,230,107,.5);
        }
        /* 로고 아래 경고 줄무늬 */
        .crt-stripe {
            height: 8px; margin: 6px auto 16px; width: 82%;
            background: repeating-linear-gradient(-45deg, var(--bt-lime) 0 8px, transparent 8px 14px);
            opacity: .85;
        }
        .crt-text { color: #e3f5c8; font-size: 1rem; line-height: 1.65; }
        .crt-trace { font-family: 'Nanum Gothic Coding', monospace; font-size: .9rem; margin-top: 12px; text-align: left; }
        .crt-trace .err { color: var(--bt-red); }
        .crt-cursor { display: inline-block; width: 9px; height: 1em; background: var(--bt-lime); vertical-align: middle; animation: blink 1s steps(1) infinite; }
        /* 모니터 아래 받침과 불빛 */
        .crt-leds { position: absolute; right: 44px; bottom: 12px; display: flex; gap: 6px; }
        .crt-leds span { width: 9px; height: 9px; border-radius: 50%; background: var(--bt-lime); box-shadow: 0 0 8px var(--bt-lime); }

        /* ---------- 왼쪽 책 더미 ---------- */
        .books { position: absolute; left: 4%; bottom: 46px; display: flex; flex-direction: column; gap: 4px; }
        .book {
            width: 180px; padding: 6px 12px; border-radius: 4px; font-weight: 700; font-size: .95rem;
            background: linear-gradient(90deg, #26331f, #34452a); color: #dfeec9;
            border: 1px solid #56713f; box-shadow: 0 2px 0 #10160c;
        }
        .book:nth-child(2) { margin-left: 10px; }
        .book:nth-child(3) { margin-left: 4px; }
        .book:nth-child(4) { margin-left: 14px; }

        /* ---------- 메모지 (벌레, 경고) ---------- */
        .note {
            position: absolute; width: 86px; height: 86px; border-radius: 4px;
            background: #b9d97a; color: #24331a; display: flex; align-items: center; justify-content: center;
            box-shadow: 0 8px 18px rgba(0,0,0,.5);
        }
        .note .bt-icon { font-size: 3rem; }
        .note-bug { left: 15%; top: 70px; transform: rotate(-8deg); }
        .note-warn { right: 13%; top: 60px; transform: rotate(7deg); }

        /* ---------- 오른쪽 머그컵과 작은 모니터 ---------- */
        .mug {
            position: absolute; right: 22%; bottom: 52px; width: 70px; height: 80px; border-radius: 6px 6px 14px 14px;
            background: #1b2416; border: 2px solid #3d5230; color: var(--bt-lime);
            font-family: 'Nanum Gothic Coding', monospace; font-weight: 700; font-size: 1.3rem;
            display: flex; align-items: center; justify-content: center;
        }
        .mug::after {
            content: ""; position: absolute; right: -20px; top: 18px; width: 18px; height: 34px;
            border: 4px solid #3d5230; border-left: none; border-radius: 0 14px 14px 0;
        }
        .side-monitor {
            position: absolute; right: 3%; bottom: 60px; width: 170px; height: 120px; border-radius: 8px;
            background: #0b1109; border: 6px solid #2a2d27; padding: 10px; overflow: hidden;
        }
        .side-monitor div { height: 6px; margin-bottom: 7px; border-radius: 3px; background: rgba(183,230,107,.55); }

        @keyframes blink { 50% { opacity: 0; } }

        /* 좁은 화면에서는 장식을 숨기고 모니터만 보여 준다 */
        @media (max-width: 1100px) {
            .books, .note, .mug, .side-monitor { display: none; }
        }
        @media (max-width: 700px) {
            .scene { height: auto; padding: 18px 10px 30px; }
            .crt { position: relative; left: auto; top: auto; transform: none; width: 100%; padding: 12px; }
            .crt-logo { font-size: 3.2rem; }
        }

        /* ---------- 메뉴 카드 (오류 도감, 원인 해부실 ...) ---------- */
        [class*="st-key-menu_"] {
            border: 2px solid var(--bt-lime); border-radius: 16px; padding: 14px 10px 12px;
            background: #121a12; box-shadow: var(--bt-glow); text-align: center;
        }
        [class*="st-key-menu_"] div[data-testid="stPageLink"] a {
            border: none; background: transparent; justify-content: center; min-height: 44px;
        }
        [class*="st-key-menu_"] div[data-testid="stPageLink"] a p { font-size: 1.35rem !important; font-weight: 800 !important; }
        [class*="st-key-menu_"] div[data-testid="stPageLink"] a span { color: var(--bt-lime); font-size: 1.6rem; }
        [class*="st-key-menu_"] .stCaption, [class*="st-key-menu_"] [data-testid="stCaptionContainer"] { text-align: center; color: var(--bt-text); }


/* beige 1990s CRT laboratory scene */
.scene {background:radial-gradient(ellipse at 50% 26%,#FFFDF2 0%,#EEE4D0 65%,#CDBD9F 100%) !important;border:2px solid #C1B296 !important;box-shadow:inset 0 0 55px rgba(105,88,58,.10);}
.scene-floor {background-image:linear-gradient(rgba(89,105,69,.20) 1px,transparent 1px),linear-gradient(90deg,rgba(89,105,69,.20) 1px,transparent 1px) !important;}
.crt {background:linear-gradient(135deg,#EDE5D2 0%,#D4C7AC 68%,#B7AA8E 100%) !important;border:3px solid #AB9E83 !important;box-shadow:0 18px 0 -7px #B4A78E,0 25px 42px rgba(71,58,39,.28),inset 2px 3px 3px #FFF9E8 !important;}
.crt-screen {background:radial-gradient(ellipse at center,#203B20 0%,#112715 75%,#0A1B0D 100%) !important;border:9px solid #605F50 !important;box-shadow:inset 0 0 27px rgba(0,0,0,.5),0 0 0 2px #A69B82 !important;}
.crt-screen::after {opacity:.26 !important;}
.crt-logo {color:#E4F9B5 !important;text-shadow:0 0 8px rgba(181,230,122,.32) !important;}
.crt-text {color:#F0F7E6 !important;font-weight:700 !important;font-size:17px !important;}
.crt-trace {color:#DCEFCB !important;font-weight:700 !important;}
.crt-bar {color:#E5F4CF !important;}
.crt-leds span {background:#6C9E38 !important;box-shadow:0 0 5px #6C9E38 !important;}
.book {background:linear-gradient(90deg,#687B50,#89996B) !important;color:#FFFDF4 !important;border-color:#52683E !important;box-shadow:0 2px 0 #A89B83 !important;}
.note {background:#E8E1A0 !important;color:#475A36 !important;box-shadow:0 6px 16px rgba(87,70,43,.2) !important;}
.mug {background:#E4DDCA !important;border-color:#9B947D !important;color:#435B36 !important;}
.mug::after {border-color:#9B947D !important;}
.side-monitor {background:#1D3622 !important;border-color:#B8AE96 !important;}
[class*="st-key-menu_"] {background:#FFFCF3 !important;border:2px solid #91A97B !important;box-shadow:0 4px 12px rgba(62,75,46,.10) !important;}
[class*="st-key-menu_"] div[data-testid="stPageLink"] a,[class*="st-key-menu_"] div[data-testid="stPageLink"] a * {background:transparent !important;color:#28472C !important;-webkit-text-fill-color:#28472C !important;}
[class*="st-key-menu_"] div[data-testid="stPageLink"] a {min-height:65px !important;}
[class*="st-key-menu_"] div[data-testid="stPageLink"] a p {font-size:19px !important;font-weight:800 !important;}
[class*="st-key-menu_"] [data-testid="stCaptionContainer"] p {color:#53624B !important;}

        </style>
    """)


def show_scene(case_count):
    """레트로 컴퓨터 책상 장면을 그린다. (모니터, 책, 메모지, 머그컵, 작은 모니터)"""
    # &gt; 는 HTML에서 '>' 기호를 뜻한다.
    # bt-icon 글꼴: "pest_control"은 벌레, "warning"은 경고 삼각형 아이콘이다.
    render_html(f"""
        <div class="scene">
            <div class="scene-floor"></div>
            <div class="books">
                <div class="book">OS</div>
                <div class="book">Encoding</div>
                <div class="book">Unicode</div>
                <div class="book">Floating-Point</div>
            </div>
            <div class="note note-bug"><span class="bt-icon">pest_control</span></div>
            <div class="note note-warn"><span class="bt-icon">warning</span></div>
            <div class="mug">&gt;_</div>
            <div class="side-monitor"><div style="width:80%"></div><div style="width:55%"></div><div style="width:70%"></div><div style="width:40%"></div><div style="width:65%"></div><div style="width:50%"></div></div>
            <div class="crt">
                <div class="crt-screen">
                    <div class="crt-bar"><span>&gt;_ BUG_TRACE.exe</span><span>—&nbsp;&nbsp;□&nbsp;&nbsp;×</span></div>
                    <div class="crt-logo">BUG TRACE</div>
                    <div class="crt-stripe"></div>
                    <div class="crt-text">컴퓨터에서 발생하는 신기하고 이해하기 어려운 오류의<br>원인과 작동 원리를 탐구하는 디지털 아카이브입니다.</div>
                    <div class="crt-trace">&gt; TRACE: 완선 → [⌫] → ㅅㅓㅇ = <span class="err">완완성 !!</span> &nbsp;· {case_count} CASES LOADED <span class="crt-cursor"></span></div>
                </div>
                <div class="crt-leds"><span></span><span></span><span></span></div>
            </div>
        </div>
    """)


def show_menu_cards():
    """4개 페이지로 가는 큰 메뉴 카드를 보여 준다."""
    columns = st.columns(len(MENU_CARDS))
    # enumerate: 카드 순서 번호(0, 1, 2, 3)와 카드 내용을 함께 꺼낸다.
    for number, (column, (page_file, name, icon_name, description)) in enumerate(zip(columns, MENU_CARDS)):
        with column:
            # key="menu_0" 처럼 이름을 붙이면 CSS에서 이 상자만 골라 꾸밀 수 있다.
            with st.container(key=f"menu_{number}"):
                # st.page_link: 누르면 해당 페이지로 이동하는 링크
                st.page_link(page_file, label=f"{name}  ›", icon=icon_name)
                st.caption(description)


def show_featured_cases(cases):
    """대표 오류 3개를 카드로 보여 주고, 버튼을 누르면 원인 해부실로 이동한다."""
    st.markdown("## 대표 오류")
    st.caption("가장 많이 겪는 오류부터 추적해 보세요.")

    columns = st.columns(len(FEATURED_CASE_IDS))
    # zip(): 칸 목록과 오류 번호 목록을 하나씩 짝지어 반복한다.
    for column, case_id in zip(columns, FEATURED_CASE_IDS):
        case = find_case(cases, case_id)
        with column:
            with st.container(border=True):     # 테두리 있는 상자
                case_card(case)                 # 카드 내용 그리기
                # key: 버튼마다 서로 다른 이름을 붙여야 Streamlit이 구별할 수 있다.
                if st.button("원인 추적하기 →", key=f"home_open_{case_id}", width="stretch"):
                    open_case(case_id)          # 번호를 기억하고 원인 해부실로 이동


# ----- 실제 실행 순서 -----
all_cases = load_cases()                 # 오류 데이터 불러오기
apply_home_style()                       # 홈 디자인 적용
show_scene(len(all_cases))               # 레트로 컴퓨터 책상 장면
st.write("")                             # 빈 줄(간격)
show_menu_cards()                        # 4개 메뉴 카드
st.divider()                             # 구분선
show_featured_cases(all_cases)           # 대표 오류 3개
