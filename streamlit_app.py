# =============================================================
# streamlit_app.py  (시작 파일)
# BUG TRACE 웹앱이 실행되면 가장 먼저 이 파일이 실행된다.
# 하는 일: 기본 설정 → 공통 디자인 → 페이지 목록 등록 → 선택한 페이지 실행
# (메뉴는 각 페이지의 CRT 모니터 화면 안에 있다. → common.py의 crt_frame)
# =============================================================

import streamlit as st

from common import apply_style   # 공통 디자인(CSS)


def setup_page():
    """브라우저 탭 제목, 아이콘, 화면 너비를 설정한다."""
    # set_page_config는 반드시 다른 Streamlit 명령보다 먼저 실행해야 한다.
    st.set_page_config(
        page_title="BUG TRACE",   # 브라우저 탭에 보이는 제목
        page_icon="🐞",           # 브라우저 탭 아이콘
        layout="wide",            # 화면을 넓게 사용
    )


def create_pages():
    """pages 폴더 안의 파일들을 페이지로 등록하고 목록으로 돌려준다."""
    # st.Page(파일 경로, title=메뉴 이름, icon=메뉴 아이콘)
    # default=True → 처음 접속했을 때 보여 줄 페이지
    return [
        st.Page("pages/home.py", title="홈", icon=":material/home:", default=True),
        st.Page("pages/catalog.py", title="오류 도감", icon=":material/menu_book:"),
        st.Page("pages/anatomy.py", title="원인 해부실", icon=":material/layers:"),
        st.Page("pages/laboratory.py", title="현상 실험실", icon=":material/science:"),
        st.Page("pages/compare.py", title="오류 비교실", icon=":material/compare_arrows:"),
        st.Page("pages/detection.py", title="오류 검출", icon=":material/fact_check:"),
    ]


# ----- 실제 실행 순서 -----
setup_page()                              # 1) 기본 설정
apply_style()                             # 2) 모든 페이지에 공통 디자인 적용

# 3) 페이지를 등록한다. position="hidden": Streamlit 기본 메뉴는 숨기고,
#    모니터 화면 안의 메뉴 버튼(st.page_link)으로 이동한다.
current_page = st.navigation(create_pages(), position="hidden")
current_page.run()                        # 4) 고른 페이지의 코드를 실행한다
