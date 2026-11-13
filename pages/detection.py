# =============================================================
# pages/detection.py  (오류 검출)
# 앞의 두 사례가 '오류가 왜 생기나'였다면, 이 페이지는 '망가진 데이터를 컴퓨터가 어떻게 알아채나'를 다룬다.
#   ① 데이터는 왜 망가질까 → ② 핵심 아이디어(확인값 덧붙이기) → ③ 패리티 비트 계산 순서
#   → ④ 직접 실험(비트 1~2개 뒤집기) → ⑤ 패리티의 한계와 XOR 체크섬 → ⑥ CRC와 실제 쓰임 → ⑦ 출처
# =============================================================

from html import escape

import streamlit as st

from common import crt_frame, icon, page_banner, render_html

# 데이터가 망가지는 대표적인 원인: (아이콘, 이름, 설명)
DAMAGE_CAUSES = [
    ("bolt", "전기 잡음", "전선 주변의 전기·자기 신호가 섞여서 0으로 보낸 신호가 1처럼 읽혀요."),
    ("wifi", "약한 무선 신호", "와이파이·블루투스 신호가 약하거나 벽에 막히면 일부 비트를 잘못 받아요."),
    ("hard_drive", "저장 장치 손상", "긁힌 디스크, 오래된 플래시 메모리는 저장된 비트가 바뀌거나 읽히지 않아요."),
    ("flare", "우주 방사선", "우주에서 오는 입자가 메모리 칩에 부딪혀 비트 하나를 뒤집기도 해요. (소프트 오류)"),
]

# 실제로 쓰이는 오류 검출 방법: (어디서, 무엇을 쓰나)
REAL_USES = [
    ("바코드 · ISBN", "마지막 숫자 하나가 '검사 숫자'예요. 앞 숫자들로 계산한 값과 다르면 잘못 찍힌 거예요."),
    ("인터넷 · 와이파이", "데이터 묶음(패킷)마다 CRC 확인값을 붙여 보내고, 틀리면 다시 보내 달라고 해요."),
    ("ZIP · PNG 파일", "파일 안에 CRC 값을 저장해 두고, 열 때 다시 계산해서 파일이 망가졌는지 확인해요."),
    ("서버용 메모리 (ECC)", "확인 비트를 더 많이 붙여서 비트 하나가 바뀌면 찾아내고 고치기까지 해요. (오류 정정)"),
]

# 근거 문서
SOURCES = [
    ("Wikipedia · Parity bit (패리티 비트)", "https://en.wikipedia.org/wiki/Parity_bit"),
    ("Wikipedia · Checksum (체크섬)", "https://en.wikipedia.org/wiki/Checksum"),
    ("Wikipedia · Cyclic redundancy check (CRC)", "https://en.wikipedia.org/wiki/Cyclic_redundancy_check"),
]


# -------------------------------------------------------------
# 1. 계산 함수 (비트 연산)
# -------------------------------------------------------------

def parity_bit(byte):
    """짝수 패리티: 1의 개수가 홀수면 1, 짝수면 0 → 패리티까지 합친 1의 개수가 항상 짝수가 되게 만든다."""
    # bin(수) : 2진수 글자로 바꾼다. .count("1") : 그 안의 1의 개수. % 2 : 2로 나눈 나머지(0 또는 1)
    return bin(byte).count("1") % 2


def xor_checksum(data):
    """모든 바이트를 XOR(^)로 차례로 접어서 확인값 1바이트를 만든다."""
    checksum = 0
    for byte in data:
        checksum ^= byte          # ^ (XOR) : 두 칸이 다르면 1, 같으면 0
    return checksum


def flip_bits(data, positions):
    """positions에 적힌 비트 번호(1부터 셈)를 뒤집은 새 데이터를 돌려준다. 0번은 '안 뒤집기'로 본다."""
    changed = bytearray(data)                     # bytes는 고칠 수 없어서, 고칠 수 있는 bytearray로 복사
    for position in set(positions) - {0}:         # set: 같은 번호를 두 번 고르면 한 번만 / {0}을 빼서 '안 뒤집기' 제외
        byte_index = (position - 1) // 8          # 몇 번째 바이트인가
        bit_index = 7 - (position - 1) % 8        # 그 바이트의 몇 번째 칸인가 (왼쪽 칸부터 1번)
        changed[byte_index] ^= 1 << bit_index     # ^ 와 << 로 그 칸 하나만 뒤집는다 (0↔1)
    return bytes(changed)


# -------------------------------------------------------------
# 2. 설명 화면
# -------------------------------------------------------------

def section_label(icon_name, english, korean):
    """각 구역 위에 붙는 작은 제목"""
    return f'<div class="sec-label">{icon(icon_name)} {english} · {korean}</div>'


def show_why_damaged():
    """① 데이터가 왜 망가지는지 원인 4가지를 카드로 보여 준다."""
    cards = "".join(
        f'<div class="bt-term"><div class="bt-term-name">{icon(icon_name)} {escape(name)}</div><div class="bt-term-desc">{escape(desc)}</div></div>'
        for icon_name, name, desc in DAMAGE_CAUSES
    )
    render_html(f"""
        {section_label("report", "WHY", "데이터는 왜 망가질까")}
        <div class="bt-box">데이터는 결국 0과 1(비트)이에요. 보내거나 저장하는 도중에 <b>비트 하나가 0↔1로 뒤집히면</b>
        글자·숫자·사진이 다른 값이 돼요. BUG-001·002는 <b>계산 규칙</b> 때문에 생긴 오류였다면, 여기서 다루는 것은 <b>전달 도중</b> 생기는 오류예요.</div>
        <div class="bt-terms">{cards}</div>
    """)


def show_main_idea():
    """② 오류 검출의 핵심 아이디어: 보내는 쪽이 확인값을 붙이고, 받는 쪽이 다시 계산해서 비교한다."""
    render_html(f"""
        {section_label("lightbulb", "IDEA", "핵심 아이디어")}
        <div class="bt-flow">
            <div class="bt-flow-box">{icon("upload")}<div class="bt-flow-name">보내는 쪽</div><div class="bt-flow-text">데이터로 확인값을 계산해서 데이터 뒤에 붙여 보낸다</div></div>
            <div class="bt-flow-arrow">▶</div>
            <div class="bt-flow-box">{icon("cell_tower")}<div class="bt-flow-name">전달 중</div><div class="bt-flow-text">잡음 때문에 비트가 뒤집힐 수 있다</div></div>
            <div class="bt-flow-arrow">▶</div>
            <div class="bt-flow-box">{icon("download")}<div class="bt-flow-name">받는 쪽</div><div class="bt-flow-text">받은 데이터로 확인값을 다시 계산해서, 함께 온 확인값과 비교한다</div></div>
        </div>
        <div class="bt-keypoint">{icon("fact_check")}<div><div class="bt-keypoint-label">KEY POINT · 이것만 기억하세요</div>
        <div class="bt-keypoint-text">두 확인값이 다르면 '오는 길에 망가졌다'는 것을 알 수 있어요. 같으면 아마도 그대로 온 거예요.</div></div></div>
    """)


def show_parity_explain():
    """③ 패리티 비트가 무엇인지, 짝수·홀수 패리티, XOR로 계산하는 법, 한계를 차례로 자세히 설명한다."""
    render_html(f"""
        {section_label("help", "PARITY", "패리티 비트란?")}
        <div class="bt-box dt-explain">
            <p><b>패리티 비트</b>는 데이터를 보내거나 저장할 때 <b>비트가 잘못 바뀌었는지 확인하려고 덧붙이는 1비트</b>예요.</p>
            <p>예를 들어 <code>1011</code>에는 1이 3개 있어요. <b>짝수 패리티</b>에서는 1의 총개수가 짝수가 되도록 뒤에 <code>1</code>을 붙여
            <code>1011<b>1</b></code>로 보내요. 보내는 도중 비트 하나가 바뀌어 <code>10011</code>이 되면 1이 3개(홀수)가 되므로,
            받는 쪽에서 "오는 길에 무언가 바뀌었다"는 것을 알아챌 수 있어요. <b>홀수 패리티</b>는 같은 방식으로 1의 총개수를 홀수로 맞춰요.</p>
            <p>비트 연산으로는 <b>XOR(^)</b>을 쓰면 돼요. XOR은 두 비트가 다르면 1, 같으면 0이라서, 모든 비트를 XOR하면 1이 홀수 개일 때 1이 나와요.
            <code>1 ^ 0 ^ 1 ^ 1 = 1</code>이므로, 이 결과가 바로 붙여야 할 짝수 패리티 비트예요.</p>
            <p>하지만 패리티 비트 하나로는 <b>어느 비트가 바뀌었는지</b> 알 수 없고, <b>두 비트가 함께 바뀌면</b> 짝수·홀수가 그대로라서 오류를 놓쳐요.
            2의 보수가 <b>비트에 숫자의 의미를 부여하는 규칙</b>이라면, 패리티 비트는 <b>비트가 전달되는 과정에서 바뀌었는지 검사하는 장치</b>예요.</p>
        </div>
    """)


def show_parity_steps():
    """③-2 패리티 비트를 붙이는 순서를 글자 'B' 예시로 보여 준다."""
    render_html(f"""
        {section_label("format_list_numbered", "STEP", "글자 B로 따라 해 보기 (짝수 패리티)")}
        <div class="an-steps">
            <div class="an-step"><span class="bt-step-no">#01</span><div class="an-step-text">글자 <b>B</b>를 비트로 바꾸면 <code>01000010</code>이에요. (컴퓨터 안의 글자 번호 66)</div></div>
            <div class="an-step"><span class="bt-step-no">#02</span><div class="an-step-text">1의 개수를 세요. <code>0<b>1</b>0000<b>1</b>0</code> → <b>2개</b> (짝수)</div></div>
            <div class="an-step"><span class="bt-step-no">#03</span><div class="an-step-text">1의 개수를 짝수로 맞추는 칸 하나를 붙여요. 이미 짝수이므로 <b>0</b>을 붙여요. → <code>01000010 0</code></div></div>
            <div class="an-step"><span class="bt-step-no">#04</span><div class="an-step-text">받는 쪽은 9칸의 1을 다시 세요. <b>홀수</b>라면 비트 하나가 뒤집힌 거예요!</div></div>
        </div>
    """)


# -------------------------------------------------------------
# 3. 직접 실험: 비트를 뒤집고 패리티·체크섬이 알아채는지 확인
# -------------------------------------------------------------

def byte_row_html(name, byte, parity, flipped=(), check=""):
    """바이트 하나를 '이름 + 8칸 + 패리티 칸 + 확인 결과' 한 줄로 그린다. 뒤집힌 칸은 빨간색."""
    text = format(byte, "08b")                    # 8칸짜리 2진수 글자
    cells = ""
    for index, bit in enumerate(text):
        kind = "flip" if index in flipped else ("one" if bit == "1" else "zero")
        cells += f'<span class="{kind}">{bit}</span>'
    cells += f'<span class="par">{parity}</span>'
    return (f'<div class="dt-row"><span class="dt-name">{escape(name)}</span>'
            f'<div class="bits"><div class="byte">{cells}</div></div><span class="dt-check">{check}</span></div>')


def show_transmission(data, received, positions):
    """보낸 데이터와 받은 데이터를 바이트마다 나란히 보여 주고, 패리티로 오류를 찾는다. 찾은 바이트 수를 돌려준다."""
    sent_rows, received_rows = "", ""
    caught = 0
    for index, (sent_byte, got_byte) in enumerate(zip(data, received)):
        sent_parity = parity_bit(sent_byte)                    # 보낼 때 붙인 패리티
        ok = parity_bit(got_byte) == sent_parity               # 받는 쪽: 다시 계산한 패리티와 비교
        caught += 0 if ok else 1
        # 이 바이트 안에서 뒤집힌 칸 위치 (왼쪽부터 0번)
        flipped = [(p - 1) % 8 for p in set(positions) - {0} if (p - 1) // 8 == index]
        check = "✅ 일치" if ok else "❌ 불일치"
        sent_rows += byte_row_html(f"#{index + 1} {chr(sent_byte)}", sent_byte, sent_parity)
        received_rows += byte_row_html(f"#{index + 1}", got_byte, sent_parity, flipped, check)
    send_column, receive_column = st.columns(2)
    with send_column:
        render_html(f'<div class="bits-label">📤 보낸 데이터 (8칸 + 패리티 칸)</div>{sent_rows}')
    with receive_column:
        render_html(f'<div class="bits-label">📥 받은 데이터 → 패리티 다시 계산</div>{received_rows}')
    return caught


def show_verdict(positions, caught, checksum_caught):
    """뒤집은 비트 수와 검사 결과를 비교해서 무엇을 알아채고 무엇을 놓쳤는지 알려 준다."""
    flipped_count = len(set(positions) - {0})
    if flipped_count == 0:
        render_html('<div class="bt-box bt-ok"><div class="bt-box-label">✅ 그대로 도착</div>아무 비트도 뒤집지 않았어요. 패리티와 체크섬이 모두 일치해요.</div>')
        return
    if caught or checksum_caught:
        found = []
        if caught:
            found.append(f"패리티({caught}개 바이트)")
        if checksum_caught:
            found.append("XOR 체크섬")
        render_html(f'<div class="bt-box bt-ok"><div class="bt-box-label">✅ 찾아냈어요</div>{escape(", ".join(found))}이(가) 오류를 알아챘어요.</div>')
    if not caught:
        render_html('<div class="bt-box bt-err"><div class="bt-box-label">❌ 패리티가 놓쳤어요</div>'
                    '한 바이트 안에서 비트 2개가 함께 뒤집히면 1의 개수가 다시 짝수가 되어 패리티가 알아채지 못해요.</div>')
    if not checksum_caught:
        render_html('<div class="bt-box bt-err"><div class="bt-box-label">❌ 체크섬이 놓쳤어요</div>'
                    '서로 다른 바이트의 <b>같은 자리</b> 비트가 함께 뒤집히면 XOR에서 서로 지워져서 확인값이 그대로예요.</div>')


def run_detection_lab():
    """④ 직접 실험: 글자를 비트로 바꿔 보내는 중에 비트를 1~2개 뒤집고, 패리티와 XOR 체크섬이 알아채는지 확인한다."""
    render_html(section_label("science", "TRY IT", "직접 비트를 뒤집어 보기"))
    with st.container(border=True):
        text_column, first_column, second_column = st.columns([2, 1, 1], vertical_alignment="bottom")
        message = text_column.text_input("보낼 글자 (영어·숫자, 8글자까지)", "BUG", max_chars=8, key="dt_text")
        data = message.encode("ascii", errors="ignore")      # 글자 → 바이트 (영어·숫자만 1글자 = 1바이트)
        if not data:
            st.info("영어나 숫자를 입력해 주세요. 예) BUG")
            return
        total_bits = len(data) * 8
        # 글자를 줄이면 전에 고른 번호가 범위를 넘을 수 있어서, 입력칸을 그리기 전에 최댓값으로 맞춘다
        for key in ("dt_flip1", "dt_flip2"):
            if st.session_state.get(key, 0) > total_bits:
                st.session_state[key] = total_bits
        first = first_column.number_input(f"뒤집을 비트 ① (0~{total_bits})", 0, total_bits, min(3, total_bits), key="dt_flip1")
        second = second_column.number_input("뒤집을 비트 ② (0 = 안 뒤집기)", 0, total_bits, 0, key="dt_flip2")
        st.caption("💡 해 볼 것: ② 에 ①과 같은 바이트 안의 번호(예: 3과 5)를 넣어 보세요. 그다음 ①=3, ②=11처럼 다른 바이트의 같은 자리도 넣어 보세요.")

        positions = [first, second]
        received = flip_bits(data, positions)               # 전달 중 비트가 뒤집혔다고 가정
        caught = show_transmission(data, received, positions)
        sent_sum, received_sum = xor_checksum(data), xor_checksum(received)
        st.code(f"XOR 체크섬 (보낼 때) : {sent_sum:08b}  ({sent_sum})\n"
                f"XOR 체크섬 (받은 뒤) : {received_sum:08b}  ({received_sum})")
        show_verdict(positions, caught, sent_sum != received_sum)


# -------------------------------------------------------------
# 4. 한계와 더 강한 방법, 실제 쓰임
# -------------------------------------------------------------

def show_stronger_methods():
    """⑤⑥ 패리티의 한계 → XOR 체크섬 → CRC 순서로 점점 강해지는 방법을 자세히 설명하고 표로 비교한다."""
    render_html(f"""
        {section_label("stairs", "STRONGER", "점점 강해지는 검사 방법")}
        <div class="bt-box dt-explain">
            <p><b>XOR 체크섬</b>은 바이트마다 패리티를 붙이는 대신, <b>모든 바이트를 XOR로 차례로 겹쳐 확인값 1바이트</b>를 만들어요.
            예를 들어 <code>B(01000010) ^ U(01010101) ^ G(01000111) = 01010000</code>이에요. 확인값의 각 자리는
            '그 자리에 있는 1의 개수가 홀수인가?'를 뜻하니까, <b>자리마다 패리티를 계산한 것</b>과 같아요.
            그래서 서로 다른 바이트의 <b>같은 자리</b> 비트 2개가 함께 바뀌면 서로 지워져서 놓치고, 바이트의 <b>순서가 바뀌어도</b> 값이 같아 알아채지 못해요.</p>
            <p><b>CRC(순환 중복 검사)</b>는 데이터 전체를 하나의 긴 2진수로 보고, 미리 정한 수로 <b>나눈 나머지</b>를 확인값으로 붙여요.
            (보통의 나눗셈과 달리 빼기 대신 XOR을 써요.) 비트 하나만 바뀌어도 나머지가 크게 달라져서, <b>여러 비트가 연속으로 망가진 경우</b>도 잘 찾아내요.
            그래서 인터넷 통신, ZIP·PNG 파일처럼 실제 시스템에서 가장 널리 쓰여요.</p>
        </div>
        <div class="dt-compare">
            <div class="cmp-cell cmp-th">방법</div><div class="cmp-cell cmp-th">계산 방법</div><div class="cmp-cell cmp-th">놓치는 경우</div>
            <div class="cmp-cell cmp-name">패리티 비트</div><div class="cmp-cell">바이트마다 1의 개수를 짝수로 맞추는 칸 1개</div><div class="cmp-cell">한 바이트에서 비트가 2개(짝수 개) 뒤집힐 때</div>
            <div class="cmp-cell cmp-name">XOR 체크섬</div><div class="cmp-cell">모든 바이트를 XOR로 접어 확인값 1바이트</div><div class="cmp-cell">다른 바이트의 같은 자리 비트가 함께 뒤집힐 때, 바이트 순서가 바뀔 때</div>
            <div class="cmp-cell cmp-name">CRC</div><div class="cmp-cell">데이터를 정해진 수로 '나눈 나머지'를 확인값으로 (2진수 나눗셈)</div><div class="cmp-cell">아주 드묾. 연속으로 망가진 비트 묶음도 잘 찾아내서 인터넷·파일에 널리 쓰임</div>
        </div>
    """)


def show_real_uses():
    """실제로 오류 검출이 쓰이는 곳을 카드로 보여 준다."""
    cards = "".join(
        f'<div class="bt-term"><div class="bt-term-name">{escape(place)}</div><div class="bt-term-desc">{escape(how)}</div></div>'
        for place, how in REAL_USES
    )
    render_html(f'{section_label("public", "REAL WORLD", "실제로 쓰이는 곳")}<div class="bt-terms">{cards}</div>')


def show_sources():
    """근거 문서 목록 (누르면 새 탭에서 열린다)"""
    items = "".join(f'<li><a href="{escape(url)}" target="_blank">{escape(title)} ↗</a></li>' for title, url in SOURCES)
    render_html(f'{section_label("library_books", "SOURCES", "출처")}<div class="bt-box"><ol class="an-sources">{items}</ol></div>')


# 이 페이지에만 쓰는 디자인: 바이트 한 줄, 3칸 비교 표, 단계 카드
DETECTION_STYLE = """
<style>
.dt-row { display: flex; align-items: center; gap: 10px; margin: 3px 0; }
.dt-row .bits { margin: 0; }
.dt-name { width: 54px; font-family: 'Galmuri11', monospace; font-weight: 700; color: var(--ink); }
.dt-check { font-family: 'Galmuri11', sans-serif; font-weight: 700; }
.dt-compare { display: grid; grid-template-columns: 0.8fr 1.6fr 1.6fr; border: 3px solid var(--ink); background: var(--paper); margin-bottom: 8px; }
.cmp-cell { padding: 8px 12px; border-bottom: 2px solid #C9D9A6; border-right: 2px solid #C9D9A6; font-size: 0.97rem; line-height: 1.6; }
.cmp-th { background: var(--lime); font-family: 'Galmuri11', sans-serif; font-weight: 700; color: var(--ink); border-bottom: 3px solid var(--ink); }
.cmp-name { font-weight: 800; color: var(--ink); background: var(--lime-soft); }
.an-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin-bottom: 8px; }
.an-step { background: var(--paper); border: 3px solid var(--ink); padding: 10px 12px; }
.an-step .bt-step-no { display: inline-block; width: 50px; height: 32px; line-height: 28px; margin-bottom: 6px; }
.an-step-text { font-size: 0.98rem; line-height: 1.7; }
.an-sources { margin: 0; padding-left: 22px; line-height: 1.9; }
.dt-explain p { margin: 0 0 10px; line-height: 1.85; }
.dt-explain p:last-child { margin-bottom: 0; }
.dt-explain code { background: var(--lime-soft); color: var(--ink); padding: 1px 6px; }
@media (max-width: 800px) { .dt-compare { grid-template-columns: 1fr; } }
</style>
"""


# ----- 실제 실행 순서 -----
render_html(DETECTION_STYLE)

with crt_frame("pages/detection.py", "DETECTION"):
    page_banner("fact_check", "ERROR DETECTION", "오류 검출", "보내는 도중 망가진 데이터를 컴퓨터가 어떻게 알아채는지 살펴봅니다.")
    show_why_damaged()          # ① 데이터는 왜 망가질까
    show_main_idea()            # ② 핵심 아이디어
    show_parity_explain()       # ③ 패리티 비트란? (자세한 설명)
    show_parity_steps()         # ③-2 글자 B로 따라 해 보기
    run_detection_lab()         # ④ 직접 실험
    show_stronger_methods()     # ⑤ 한계와 더 강한 방법
    show_real_uses()            # ⑥ 실제 쓰임
    show_sources()              # ⑦ 출처
