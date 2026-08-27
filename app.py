"""
app.py - Astro Trading Signal Dashboard
-----------------------------------------
Dashboard Streamlit hien thi:
  - Dong ho THUC su chay real-time theo tung giay (JS client-side, khong
    phu thuoc vao chu ky rerun cua Streamlit)
  - Tin tuc / lich vi mo THAT (NFP, PPI, CPI, FOMC...) - macro_calendar.py
  - Chi bao "chiem tinh tai chinh" (pha trang, sao Thuy nghich hanh, nhat/
    nguyet thuc, goc chieu hanh tinh THAT) - astro.py + score_engine.py
  - Chon ngon ngu VN / EN
  - Ngay dang "active" (mac dinh = hom nay) duoc luu trong session_state va
    to sang tren bieu do; bam vao 1 vach se doi ngay active va cap nhat
    drill-down ben duoi

KHONG lay/hien thi gia cua bat ky san giao dich nao (theo yeu cau).
Day la cong cu THAM KHAO mang tinh giai tri/chiem tinh, KHONG phai loi
khuyen dau tu va khong duoc khoa hoc chinh thong cong nhan.

Chay: streamlit run app.py
"""

import calendar as _calmod
import datetime

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import astro
import houses
import macro_calendar
import score_engine
from i18n import (
    ASPECT_LABELS,
    ASPECT_SYMBOLS,
    ECLIPSE_LABELS,
    I18N,
    MOON_PHASE_LABELS,
    PLANET_LABELS,
    PLANET_SYMBOLS,
    ZODIAC_LABELS,
)

st.set_page_config(
    page_title="Bảng báo chiêm tinh",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded",  # sidebar mac dinh MO khi tai trang lan dau
)

# Mac dinh st.metric() cat ngan (text-overflow: ellipsis, khong xuong dong)
# khi gia tri qua dai, vd "Trang khuyet cuoi..." - ep font-size 24px va cho
# PHEP XUONG DONG thay vi cat ngan, de luon hien thi DAY DU noi dung. Kem
# theo do la 1 khoi CSS RESPONSIVE cho man hinh dien thoai (<= 640px): thu
# nho tieu de/heading, giam padding thua, va QUAN TRONG NHAT la giu lich
# thang (7 cot/tuan) KHONG bi Streamlit tu dong xep doc tren mobile (mac
# dinh st.columns() se stack doc <=640px) - phai ep no o lai dang hang
# ngang, chi thu nho nut lai cho vua man hinh, neu khong lich se vo dang.
st.markdown(
    """
    <style>
    /* Streamlit thuong dat overflow:hidden/text-overflow:ellipsis tren 1
       the <div> con NAM BEN TRONG [data-testid="stMetricValue"], khong
       phai tren chinh no - nen phai ep ca the con (dau *) thi moi het bi
       cat "..." , chi sua o cap container ngoai la khong du. */
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] * {
        font-size: 24px !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
        line-height: 1.3 !important;
        word-break: break-word !important;
    }

    /* Lich thang: bat buoc 7 cot/tuan LUON nam ngang (khong cho Streamlit
       tu stack doc), ap dung moi kich thuoc man hinh - chi giam kich thuoc
       chu/khoang cach rieng tren mobile o khoi @media ben duoi. */
    .st-key-calendar_grid [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 4px !important;
    }
    .st-key-calendar_grid [data-testid="stHorizontalBlock"] > div {
        min-width: 0 !important;
        flex: 1 1 0 !important;
    }

    @media (max-width: 640px) {
        /* Tieu de + subheader thu nho de khong bi vo dong / tran ngang */
        h1 { font-size: 1.35rem !important; }
        h2, h3 { font-size: 1.05rem !important; }
        p, li, span, div { font-size: 0.92rem; }

        /* Gia tri metric (Do manh, Xu huong, Mat Trang...) thu nho lai
           chut de khong chiem qua nhieu chieu cao tren man hinh nho, van
           du lon de doc va khong bi cat "..." nhu truoc khi sua. */
        [data-testid="stMetricValue"],
        [data-testid="stMetricValue"] * {
            font-size: 18px !important;
        }
        [data-testid="stMetricLabel"] { font-size: 0.8rem !important; }

        /* Giam padding thua 2 ben de tan dung toi da chieu ngang hep */
        .block-container {
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
            padding-top: 1rem !important;
        }

        /* Nut ngay trong lich thang: chu nho lai + bot padding cho vua 7
           cot tren man hinh hep, van du to de bam bang ngon tay. */
        .st-key-calendar_grid button {
            font-size: 0.72rem !important;
            padding: 0.15rem 0 !important;
            min-height: 2rem !important;
        }

        /* The badge khung gio song manh / Void-of-Course: nho lai chut */
        span[style*="border-radius:14px"] {
            font-size: 0.72rem !important;
            padding: 3px 9px !important;
        }
    }

    /* Tu TABLET tro len (>=641px, bao gom ca DESKTOP): mac dinh Streamlit
       coi day la man hinh "du rong" nen sidebar mo ra se DAY noi dung
       chinh sang ben - doi lai thanh dang OVERLAY (nam de len tren noi
       dung, khong day noi dung) giong hanh vi tren dien thoai, ap dung cho
       moi kich thuoc man hinh tu tablet tro len. Dong thoi ep nut mo/dong
       sidebar LUON hien thi (khong bi an di khi sidebar dong hoac mo). */
    @media (min-width: 641px) {
        [data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            height: 100vh !important;
            z-index: 999998 !important;
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.6);
        }
    }

    [data-testid="stSidebarCollapseButton"] {
        display: flex !important;
        align-items: center !important;
        overflow: visible !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999999 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Tu lam moi trang moi 5 phut de du lieu ngay/thang luon cap nhat. Dong ho
# giay khong phu thuoc vao cai nay (xem render_clock ben duoi - chay bang JS).
try:
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(interval=300_000, key="auto_refresh_5min")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Ngon ngu
# ---------------------------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state.lang = "vi"


def t(key: str, **kwargs) -> str:
    text = I18N[st.session_state.lang][key]
    return text.format(**kwargs) if kwargs else text


# Man hinh loading PHU TOAN BO TRANG voi vong xoay animation, tu dong hien
# moi khi Streamlit dang xu ly (rerun do bam nut/doi ngon ngu/doi ngay...)
# va tu dong an khi xong - dung CSS thuan (":has()") de theo doi trang
# thai "Running..." that cua Streamlit qua icon spinner co san cua no
# (data-testid="stStatusWidgetRunningIcon", chi ton tai trong DOM luc dang
# chay), khong can JS rieng.
st.markdown(
    f"""
    <div class="astro-loading-overlay">
        <div class="astro-spinner"></div>
        <div class="astro-loading-text">{t('loading_text')}</div>
    </div>
    <style>
    .astro-loading-overlay {{
        position: fixed;
        inset: 0;
        background: rgba(8, 8, 16, 0.93);
        z-index: 2147483647;
        display: none;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 18px;
    }}
    /* Chi hien khi Streamlit THAT SU dang chay/rerun (spinner "Running..."
       goc cua no dang ton tai trong DOM) - tu dong an khi xu ly xong. */
    body:has([data-testid="stStatusWidgetRunningIcon"]) .astro-loading-overlay {{
        display: flex;
    }}
    .astro-spinner {{
        width: 56px;
        height: 56px;
        border: 5px solid rgba(255, 255, 255, 0.15);
        border-top-color: #e67e22;
        border-radius: 50%;
        animation: astro-spin 0.8s linear infinite;
    }}
    @keyframes astro-spin {{
        to {{ transform: rotate(360deg); }}
    }}
    .astro-loading-text {{
        color: #ffffff;
        font-size: 1.1rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def moon_label(phase_key: str) -> str:
    return MOON_PHASE_LABELS[st.session_state.lang][phase_key]


def eclipse_label(kind: str) -> str:
    return ECLIPSE_LABELS[st.session_state.lang][kind]


def macro_name(event: dict) -> str:
    return event.get(f"name_{st.session_state.lang}", event.get("name_vi", ""))


def planet_label(key: str) -> str:
    return PLANET_LABELS[st.session_state.lang][key]


def aspect_label(key: str) -> str:
    return ASPECT_LABELS[st.session_state.lang][key]


def zodiac_label(key: str) -> str:
    return ZODIAC_LABELS[st.session_state.lang][key]


def render_clock():
    """Dong ho chay that theo tung giay, CHI hien thi gio may tinh/trinh
    duyet cua nguoi dung (khong con dong UTC rieng) - cap nhat 100% phia
    client bang JavaScript setInterval, hoan toan doc lap voi vong rerun
    cua Streamlit."""
    html_code = f"""
    <style>
      .clock-wrap {{ font-family:'Source Sans Pro', sans-serif; text-align:right; margin-top:10px; }}
      .clock-label {{ font-size:0.72rem; color:#888; letter-spacing:.02em; }}
      #clock-local {{ font-size:2rem; font-weight:700; line-height:1.15; color:#ffffff; }}
      /* Man hinh dien thoai thuong lam cot nay hep lai - thu nho dong ho +
         can giua thay vi can phai de khong bi tran/cat chu. */
      @media (max-width: 480px) {{
        .clock-wrap {{ text-align:center; }}
        #clock-local {{ font-size:1.4rem; }}
      }}
    </style>
    <div class="clock-wrap">
      <div class="clock-label">{t('clock_label')}</div>
      <div id="clock-local">--:--:--</div>
    </div>
    <script>
    function pad(n) {{ return n.toString().padStart(2, '0'); }}
    function tick() {{
      const now = new Date();
      const h = pad(now.getHours()), m = pad(now.getMinutes()), s = pad(now.getSeconds());
      const el = document.getElementById('clock-local');
      if (el) el.innerText = h + ':' + m + ':' + s;
    }}
    tick();
    setInterval(tick, 1000);
    </script>
    """
    components.html(html_code, height=75)


# ---------------------------------------------------------------------------
# Header: chon ngon ngu dat RIENG 1 hang tren cung, gan sat GOC TRAI cua
# trang (truoc ca tieu de) - khong con nam giua tieu de va dong ho nua.
# ---------------------------------------------------------------------------
col_lang, _col_lang_spacer = st.columns([1, 5])
with col_lang:
    st.radio(
        t("lang_label"),
        options=["vi", "en"],
        format_func=lambda x: "VN" if x == "vi" else "EN",
        horizontal=True,
        key="lang",
        label_visibility="collapsed",
    )

col_title, col_clock = st.columns([3, 1.3])

with col_title:
    st.title("🌙 Bảng báo chiêm tinh")
    st.caption(t("app_caption"))

with col_clock:
    render_clock()

st.button(t("refresh_button"))

with st.expander(t("explain_title"), expanded=False):
    st.markdown(t("explain_body"))

st.divider()

# ---------------------------------------------------------------------------
# Sidebar: trang thai chiem tinh hom nay + lich tin vi mo
# ---------------------------------------------------------------------------
today = datetime.date.today()  # ngay theo lich cua may tinh dang chay app (local, khong phai UTC)
today_signal = score_engine.daily_signal(today)

with st.sidebar:
    # -----------------------------------------------------------------
    # Vi tri quan sat CO DINH = Ha Noi, Viet Nam (UTC+7) - khong can nhieu
    # tuy chon dia diem/toa do tu nhap nua, chi dung 1 khung gio Viet Nam
    # duy nhat theo yeu cau. Toa do nay chi anh huong song nang luong theo
    # gio (Ascendant + do cao Mat Trang); chi bao 30 ngay khong phu thuoc
    # vi tri quan sat nen khong bi anh huong.
    st.session_state.obs_lat = houses.DEFAULT_LOCATIONS["hanoi"]["lat"]
    st.session_state.obs_lon = houses.DEFAULT_LOCATIONS["hanoi"]["lon"]
    st.caption(f"{t('location_label')}: {houses.DEFAULT_LOCATIONS['hanoi'][f'label_{st.session_state.lang}']} (UTC+7)")

    st.divider()
    st.subheader(t("sidebar_status_title"))
    st.markdown(f"### {today_signal['moon_emoji']} {moon_label(today_signal['moon_phase_key'])}")
    st.caption(f"{t('moon_sign_label')}: {zodiac_label(today_signal['moon_sign'])}")
    st.progress(
        today_signal["illumination"],
        text=f"{t('illum_label')}: {today_signal['illumination']*100:.1f}%",
    )

    for p in score_engine.NOTABLE_RETRO_PLANETS:
        if astro.is_planet_retrograde(p, today):
            st.error(f"{PLANET_SYMBOLS[p]} " + t("retro_planet_active", planet=planet_label(p)))
    if "mercury" not in today_signal["retrograde_planets"]:
        nxt = astro.next_mercury_retrograde(today)
        if nxt:
            st.info(t("retro_next", start=nxt["start"].strftime("%d/%m/%Y"), end=nxt["end"].strftime("%d/%m/%Y")))

    eclipse_today_kind = astro.eclipse_on(today)
    if eclipse_today_kind:
        st.warning(t("eclipse_today", desc=eclipse_label(eclipse_today_kind)))

    st.divider()
    st.subheader(t("sidebar_macro_title"))
    st.caption(t("sidebar_macro_caption", date=macro_calendar.last_verified()))
    upcoming = macro_calendar.events_in_range(today, today + datetime.timedelta(days=30))
    if upcoming:
        for e in upcoming:
            d = datetime.date.fromisoformat(e["date"])
            impact_icon = "🔴" if e["impact"] == "high" else "🟠"
            local_dt = macro_calendar.event_local_datetime(e)
            time_part = f" {local_dt.strftime('%H:%M')}" if local_dt else ""
            st.markdown(f"{impact_icon} **{d.strftime('%d/%m')}**{time_part} — {macro_name(e)}")
    else:
        st.caption(t("sidebar_macro_none"))

# ---------------------------------------------------------------------------
# Tang 1: bieu do 30 ngay (vach xanh/do, cao = manh)
# ---------------------------------------------------------------------------
if "active_date" not in st.session_state:
    st.session_state.active_date = today.isoformat()

# QUAN TRONG: doc ket qua click cua LAN RERUN TRUOC ngay tu dau (truoc khi
# ve lai bieu do), khong doi den sau khi goi st.plotly_chart() moi xu ly.
# Neu xu ly sau st.plotly_chart(), bieu do trong lan chay nay se duoc ve
# bang active_date CU (truoc cu click vua roi), khien nguoi dung thay ket
# qua bi "tre 1 nhip" - bam 1 lan chua thay doi, bam lan 2 moi thay lan 1
# duoc ap dung. Doc truoc tu st.session_state["bar_chart"] (state cua
# widget co key="bar_chart", da duoc Streamlit khoi phuc truoc khi script
# chay lai) giup ap dung ngay trong lan ve dau tien.
_prev_selection = st.session_state.get("bar_chart")
if _prev_selection is not None:
    try:
        _points = _prev_selection.selection.points
        if _points:
            _raw_x = str(_points[0]["x"])[:10]
            datetime.date.fromisoformat(_raw_x)  # validate dinh dang
            st.session_state.active_date = _raw_x
    except Exception:
        pass

st.subheader(t("chart_title"))
st.caption(t("chart_caption"))

signals = score_engine.range_signals(today, 30)

dates = [s["date"] for s in signals]
strengths = [s["strength"] for s in signals]
bar_colors = ["#2ecc71" if s["bias"] == "up" else "#e74c3c" for s in signals]

# danh dau ngay dang "active" (mac dinh = hom nay, ngay lan dau load trang)
# bang do dam/nhat (opacity): vach active len mau day du (1.0), cac vach
# con lai mo nhe (0.65) - du de nhan ra dau la ngay dang chon nhung van doc
# duoc gia tri cac vach khac - ap dung dong nhat ca luc moi load lan sau
# khi bam.
bar_opacities = [1.0 if s["date"] == st.session_state.active_date else 0.65 for s in signals]


def _tag_text(s: dict) -> str:
    parts = []
    for tag in s["tags"]:
        if tag["kind"] == "retrograde":
            sym = PLANET_SYMBOLS.get(tag["planet"], "")
            parts.append(f"{sym} {planet_label(tag['planet'])} {t('retrograde_tag')}")
        elif tag["kind"] == "eclipse":
            parts.append("🌑 " + eclipse_label(tag["eclipse_kind"]))
        elif tag["kind"] == "aspect":
            p1, p2 = planet_label(tag["body1"]), planet_label(tag["body2"])
            aspect_text = f"{ASPECT_SYMBOLS.get(tag['aspect_kind'], '')} {aspect_label(tag['aspect_kind'])}"
            parts.append(t("aspect_tag", p1=p1, aspect=aspect_text, p2=p2))
        elif tag["kind"] in ("macro-high", "macro"):
            ev = tag["primary_event"]
            extra = f" +{tag['extra_count']}" if tag["extra_count"] > 0 else ""
            parts.append(f"📅 {macro_name(ev)}{extra}")
    return "<br>".join(parts) if parts else t("hover_no_event")


hover_text = [
    f"<b>{s['date']}</b><br>{s['moon_emoji']} {moon_label(s['moon_phase_key'])}<br>"
    f"{t('hover_strength')}: {s['strength']}/5<br>{_tag_text(s)}"
    for s in signals
]

fig = go.Figure(
    data=[
        go.Bar(
            x=dates,
            y=strengths,
            marker=dict(color=bar_colors, opacity=bar_opacities),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=hover_text,
        )
    ]
)
fig.update_layout(
    height=380,
    yaxis=dict(title=t("chart_yaxis"), range=[0, 5.5], dtick=1),
    # type="category" QUAN TRONG: neu de Plotly tu nhan dien truc x la kieu
    # ngay/thoi gian (vi cac gia tri trong "dates" giong ISO date), su kien
    # click se tra ve x o dinh dang khac (vd co them gio "00:00:00"), khien
    # no khong con khop voi chuoi "YYYY-MM-DD" luu trong session_state va
    # lam TOAN BO cac vach bi mo di (loi "toi den" da gap phai).
    xaxis=dict(title=t("chart_xaxis"), tickangle=-45, type="category"),
    margin=dict(l=10, r=10, t=30, b=10),
    hovermode="closest",
    hoverlabel=dict(bgcolor="#1e1e1e", font=dict(color="white", size=13)),
    clickmode="event+select",
)
# bordercolor theo tung diem (mau xanh/do) chi ho tro o cap do trace, khong
# phai o cap do layout - nen phai set rieng qua update_traces
fig.update_traces(hoverlabel=dict(bordercolor=bar_colors))

# danh dau ngay co tin vi mo hoac nhat/nguyet thuc bang icon phia tren vach
annotations = []
for s in signals:
    icon = ""
    for tag in s["tags"]:
        if tag["kind"] in ("macro-high", "macro"):
            icon = "📅"
        elif tag["kind"] == "eclipse":
            icon = "🌑"
        elif tag["kind"] == "retrograde" and not icon:
            icon = "☿"
    if icon:
        annotations.append(dict(x=s["date"], y=s["strength"] + 0.3, text=icon, showarrow=False, font=dict(size=14)))
fig.update_layout(annotations=annotations)

st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    selection_mode="points",
    key="bar_chart",
)
# Luu y: khong xu ly ket qua click O DAY nua - da xu ly truoc do (xem ghi
# chu ben tren) de tranh do tre 1 nhip khi hien thi.

st.divider()

# ---------------------------------------------------------------------------
# Tang 2: drill-down theo gio cho ngay active
# Ben trai: lich dang o vuong theo thang (thay cho o nhap ngay don gian) de
# CHON ngay drill-down - moi o mau xanh/do theo dung bias cua ngay do, giong
# mau cua bieu do 30 vach o Tang 1 (KHONG thay the bieu do 30 vach, chi la
# 1 cach chon ngay khac, truc quan hon o date_input cu).
# Ben phai: song nang luong theo gio, ve dang "truc" duong/am quanh trung
# binh ngay (Song + mau xanh, Song - mau do, duong "Truc" mau hong o giua)
# giong anh mau nguoi dung gui, thay cho duong tim don sac truoc day.
# ---------------------------------------------------------------------------
if "cal_year" not in st.session_state:
    _active_dt0 = datetime.date.fromisoformat(st.session_state.active_date)
    st.session_state.cal_year = _active_dt0.year
    st.session_state.cal_month = _active_dt0.month

col_cal, col_wave = st.columns([1, 2])

with col_cal:
    st.markdown(f"**{t('calendar_title')}**")
    nav_l, nav_mid, nav_r = st.columns([1, 3, 1])
    with nav_l:
        if st.button(t("prev_month"), key="cal_prev", use_container_width=True):
            m, y = st.session_state.cal_month - 1, st.session_state.cal_year
            if m < 1:
                m, y = 12, y - 1
            st.session_state.cal_month, st.session_state.cal_year = m, y
    with nav_r:
        if st.button(t("next_month"), key="cal_next", use_container_width=True):
            m, y = st.session_state.cal_month + 1, st.session_state.cal_year
            if m > 12:
                m, y = 1, y + 1
            st.session_state.cal_month, st.session_state.cal_year = m, y
    with nav_mid:
        st.markdown(
            f"<div style='text-align:center; font-weight:700; padding-top:6px;'>"
            f"{t('month_label', m=st.session_state.cal_month, y=st.session_state.cal_year)}</div>",
            unsafe_allow_html=True,
        )

    cal_year, cal_month = st.session_state.cal_year, st.session_state.cal_month
    days_in_month = _calmod.monthrange(cal_year, cal_month)[1]
    day_numbers = list(range(1, days_in_month + 1))
    weeks = [day_numbers[i:i + 7] for i in range(0, len(day_numbers), 7)]

    style_rules = []
    # Boc trong 1 st.container co key="calendar_grid" de CSS o tren co the
    # nham dung khoi nay (.st-key-calendar_grid ...) va ep 7 cot/tuan luon
    # nam ngang tren mobile, khong bi Streamlit tu dong xep doc.
    with st.container(key="calendar_grid"):
        for week in weeks:
            cols = st.columns(7)
            for i, day_num in enumerate(week):
                date_obj = datetime.date(cal_year, cal_month, day_num)
                sig = score_engine.daily_signal(date_obj)
                is_today = date_obj == today
                is_active = date_obj.isoformat() == st.session_state.active_date
                # "Ngay do manh" (bias xuong / do) -> to do; xanh cho bias len.
                base_color = "#2ecc71" if sig["bias"] == "up" else "#e74c3c"

                if is_active:
                    bg, border, txt = "#e67e22", "#e67e22", "#ffffff"
                else:
                    bg, txt = base_color, "#ffffff"
                    border = "#f1c40f" if is_today else base_color

                key = f"cal2_{cal_year}_{cal_month}_{day_num}"
                style_rules.append(
                    f".st-key-{key} button {{ background-color:{bg} !important; "
                    f"border:2px solid {border} !important; color:{txt} !important; "
                    f"padding:2px 0 !important; }}"
                )
                with cols[i]:
                    tooltip = (
                        f"{sig['moon_emoji']} {moon_label(sig['moon_phase_key'])} · "
                        f"{t('hover_strength')}: {sig['strength']}/5"
                    )
                    if st.button(f"{day_num:02d}", key=key, use_container_width=True, help=tooltip):
                        st.session_state.active_date = date_obj.isoformat()

    st.markdown(f"<style>{''.join(style_rules)}</style>", unsafe_allow_html=True)

    foot_l, foot_r = st.columns([3, 2])
    with foot_l:
        st.caption(f"{t('today_prefix')} {today.isoformat()}")
    with foot_r:
        if st.button(t("goto_today"), key="cal_goto_today", use_container_width=True):
            st.session_state.cal_year, st.session_state.cal_month = today.year, today.month
            st.session_state.active_date = today.isoformat()

selected_date = datetime.date.fromisoformat(st.session_state.active_date)
hourly = score_engine.hourly_signal(selected_date, st.session_state.obs_lat, st.session_state.obs_lon)
day_signal = score_engine.daily_signal(selected_date)


def _pill_label(r: str) -> str:
    # "05:00-11:00" -> "5h-11h". Dung dau gach ngang "-" (khong phai mui
    # ten "→") de tach 2 dau khung gio - tranh nham voi mui ten xu huong
    # (▲▼◆) dat NGAY SAU no, khien nguoi xem tuong toan bo la 1 chuoi mui
    # ten "khung gio -> chi so" lien tuc rat kho hieu.
    start, end = r.split("-")
    return f"{int(start.split(':')[0])}h-{int(end.split(':')[0])}h"


def _pill_badges(ranges: list, bg: str) -> str:
    return "".join(
        f"<span style='display:inline-block; background:{bg}; color:white; "
        f"padding:4px 14px; border-radius:14px; margin:3px 6px 3px 0; "
        f"font-size:0.85rem; font-weight:600;'>{_pill_label(r)}</span>"
        for r in ranges
    )


# Mui ten xu huong trong tung khung gio song manh: song dao dong nhieu dinh
# trong ngay (Ascendant xoay qua nhieu goc chieu voi Mat Trang) nen chi ghi
# mon gio khong du - can them ky hieu "dang manh len / dang yeu di / tang
# roi giam" + gia tri dinh ngay tren the badge va tren bieu do, thay vi bat
# nguoi dung tu doan qua duong song nhieu dinh.
_TREND_ARROWS = {"rising": "▲", "falling": "▼", "peak_mid": "◆", "flat": "→"}


def _strong_pill_badges(details: list, bg: str) -> str:
    spans = []
    for d in details:
        arrow = _TREND_ARROWS.get(d["trend"], "")
        trend_text = t(f"trend_{d['trend']}")
        label = _pill_label(d["range"])
        # Ghi ro nhan "Dinh: X.XX" thay vi de bare so ngay sau mui ten xu
        # huong - neu khong nguoi xem de nham so do la tiep noi cua khung
        # gio phia truoc (dung 2 mui ten lien tiep gay hieu lam).
        spans.append(
            f"<span title='{trend_text} · {t('peak_label')}: {d['peak']:.2f}' "
            f"style='display:inline-block; background:{bg}; color:white; "
            f"padding:4px 14px; border-radius:14px; margin:3px 6px 3px 0; "
            f"font-size:0.85rem; font-weight:600;'>{label} {arrow} "
            f"{t('peak_label')} {d['peak']:.2f}</span>"
        )
    return "".join(spans)


with col_wave:
    st.markdown(f"**{t('drilldown_title', date=selected_date.strftime('%d/%m/%Y'))}**")

    if hourly["strong_hour_ranges"]:
        st.markdown(f"{t('strong_hours_title')}")
        st.markdown(_strong_pill_badges(hourly["strong_hour_details"], "#c0392b"), unsafe_allow_html=True)
        st.caption("▲ " + t("trend_rising") + " · ▼ " + t("trend_falling") + " · ◆ " + t("trend_peak_mid"))
    else:
        st.caption(t("strong_hours_none"))

    hour_labels = [f"{h:02d}:00" for h in range(24)]
    wave = hourly["wave"]
    avg = sum(wave) / len(wave)
    centered = [round(v - avg, 3) for v in wave]

    # Duong chinh phai la 1 DUONG LIEN TUC duy nhat (khong dut doan) giong
    # anh mau - chi phan mau vung to (fill) phia tren/duoi truc la doi mau.
    # De vung to xanh/do khop chinh xac diem cat truc (khong bi "bac thang"),
    # can noi them cac diem giao voi truc (y=0) tai vi tri NOI SUY giua 2
    # gio lien tiep khi dau (+/-) doi chieu - vi vay truc x phai la SO (gio
    # thap phan), khong the dung chuoi "00:00" dang category nhu truoc.
    fill_x, fill_y = [], []
    for i in range(24):
        fill_x.append(i)
        fill_y.append(centered[i])
        if i < 23:
            v0, v1 = centered[i], centered[i + 1]
            if (v0 > 0) != (v1 > 0) and v0 != v1:
                cross_t = i + (0 - v0) / (v1 - v0)
                fill_x.append(round(cross_t, 4))
                fill_y.append(0.0)
    pos_fill_y = [y if y >= 0 else 0.0 for y in fill_y]
    neg_fill_y = [y if y <= 0 else 0.0 for y in fill_y]

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=fill_x, y=pos_fill_y, mode="lines", line=dict(width=0),
        fill="tozeroy", fillcolor="rgba(46,204,113,0.25)",
        hoverinfo="skip", showlegend=False,
    ))
    fig2.add_trace(go.Scatter(
        x=fill_x, y=neg_fill_y, mode="lines", line=dict(width=0),
        fill="tozeroy", fillcolor="rgba(231,76,60,0.25)",
        hoverinfo="skip", showlegend=False,
    ))
    fig2.add_trace(go.Scatter(
        x=[0, 23], y=[0, 0], mode="lines", name=t("axis_label"),
        line=dict(color="#e84393", width=2), hoverinfo="skip",
    ))
    fig2.add_trace(go.Scatter(
        x=list(range(24)), y=centered, mode="lines+markers", name=t("wave_today_name"),
        line=dict(color="#2ecc71", width=3),
        marker=dict(size=5), customdata=wave,
        hovertemplate="%{text}<br>" + t("hourly_yaxis") + ": %{customdata:.2f}<extra></extra>",
        text=hour_labels,
    ))

    # To nen mon vang nhat cho tung "khung gio song manh" ngay tren bieu do,
    # kem mui ten xu huong (▲ manh len / ▼ yeu di / ◆ tang roi giam) dat tai
    # diem dinh cua khung - giup nhin bieu do la thay ngay khung nao dang
    # manh len/yeu di ma khong can doc rieng danh sach the badge ben tren.
    for d in hourly["strong_hour_details"]:
        fig2.add_vrect(
            x0=d["start_hour"] - 0.5, x1=d["end_hour"] + 0.5,
            fillcolor="rgba(230,126,34,0.12)", line_width=0, layer="below",
        )
        arrow = _TREND_ARROWS.get(d["trend"], "")
        peak_y = centered[d["peak_hour"]]
        fig2.add_annotation(
            x=d["peak_hour"], y=peak_y, text=arrow, showarrow=False,
            yshift=20 if peak_y >= 0 else -20,
            font=dict(size=16, color="#f39c12"),
        )

    fig2.update_layout(
        height=320,
        # fixedrange=True o ca 2 truc + dragmode=False: tat hoan toan zoom
        # (keo tha chon vung, scroll zoom, double-click zoom) tren bieu do
        # nay, vi day la bieu do 24 gio co dinh, khong can phong to/thu nho.
        yaxis=dict(title=t("hourly_yaxis"), zeroline=False, fixedrange=True),
        xaxis=dict(
            title=t("hourly_xaxis"),
            tickmode="array",
            tickvals=list(range(24)),
            ticktext=hour_labels,
            tickangle=-60,  # tranh 24 nhan gio de len nhau tren man hinh hep
            fixedrange=True,
        ),
        dragmode=False,
        margin=dict(l=10, r=10, t=30, b=10),
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        annotations=[
            dict(x=0.01, y=0.92, xref="paper", yref="paper", text=t("wave_positive_label"),
                 showarrow=False, font=dict(color="#2ecc71", size=12), xanchor="left"),
            dict(x=0.01, y=0.08, xref="paper", yref="paper", text=t("wave_negative_label"),
                 showarrow=False, font=dict(color="#e74c3c", size=12), xanchor="left"),
        ],
    )
    st.plotly_chart(
        fig2,
        use_container_width=True,
        config={
            "scrollZoom": False,
            "displayModeBar": True,
            "modeBarButtonsToRemove": [
                "zoom2d", "zoomIn2d", "zoomOut2d", "autoScale2d",
                "select2d", "lasso2d",
            ],
        },
    )

st.divider()

tag_cols = st.columns(4)
with tag_cols[0]:
    st.metric(t("metric_strength_label"), f"{day_signal['strength']}/5")
with tag_cols[1]:
    st.metric(t("metric_bias_label"), t("bias_up_text") if day_signal["bias"] == "up" else t("bias_down_text"))
with tag_cols[2]:
    st.metric(t("metric_moon_label"), f"{day_signal['moon_emoji']} {moon_label(day_signal['moon_phase_key'])}")
with tag_cols[3]:
    st.metric(t("moon_sign_label"), zodiac_label(day_signal["moon_sign"]))

rise_cols = st.columns(2)
with rise_cols[0]:
    st.metric(t("moonrise_label"), hourly["moon_rise"].strftime("%H:%M") if hourly["moon_rise"] else t("moon_not_rise_set"))
with rise_cols[1]:
    st.metric(t("moonset_label"), hourly["moon_set"].strftime("%H:%M") if hourly["moon_set"] else t("moon_not_rise_set"))

if hourly["voc_hour_ranges"]:
    st.markdown(f"**{t('voc_title')}**")
    st.markdown(_pill_badges(hourly["voc_hour_ranges"], "#7f8c8d"), unsafe_allow_html=True)
    st.caption(t("voc_hint"))
else:
    st.caption(t("voc_none"))

if day_signal["tags"]:
    st.markdown(f"**{t('tags_title')}**")
    st.markdown("- " + _tag_text(day_signal).replace("<br>", "\n- "))

if hourly["macro_events"]:
    st.markdown(f"**{t('macro_today_title')}**")
    for e in hourly["macro_events"]:
        local_dt = macro_calendar.event_local_datetime(e)
        time_part = f"{local_dt.strftime('%H:%M')} — " if local_dt else ""
        st.markdown(f"- {time_part}**{macro_name(e)}** ({e['source']})")

st.divider()
st.caption(t("footer_disclaimer"))
