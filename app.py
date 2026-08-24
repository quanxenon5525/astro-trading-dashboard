"""
app.py - Astro Trading Signal Dashboard
-----------------------------------------
Dashboard Streamlit hien thi:
  - Thoi gian thuc (dong ho, tu lam moi)
  - Tin tuc / lich vi mo THAT (NFP, PPI, CPI, FOMC...) - macro_calendar.py
  - Chi bao "chiem tinh tai chinh" (pha trang, sao Thuy nghich hanh, nhat/
    nguyet thuc, goc chieu hanh tinh tuong trung) - astro.py + score_engine.py

KHONG lay/hien thi gia cua bat ky san giao dich nao (theo yeu cau).
Day la cong cu THAM KHAO mang tinh giai tri/chiem tinh, KHONG phai loi
khuyen dau tu va khong duoc khoa hoc chinh thong cong nhan.

Chay: streamlit run app.py
"""

import datetime

import plotly.graph_objects as go
import streamlit as st

import astro
import macro_calendar
import score_engine

st.set_page_config(page_title="Astro Financial Signal Dashboard", page_icon="🌙", layout="wide")

# Tu lam moi trang moi 60s de dong ho / du lieu luon "real-time" (tuy chon,
# khong bat buoc thu vien ngoai - fallback im lang neu chua cai dat).
try:
    from streamlit_autorefresh import st_autorefresh

    st_autorefresh(interval=60_000, key="auto_refresh_60s")
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
now_utc = datetime.datetime.now(datetime.timezone.utc)
now_local = datetime.datetime.now()

col_title, col_clock = st.columns([3, 1])
with col_title:
    st.title("🌙 Astro Financial Signal Dashboard")
    st.caption("Chi bao chiem tinh tai chinh + lich tin vi mo that — KHONG lay gia san giao dich")
with col_clock:
    st.metric("Gio hien tai (UTC)", now_utc.strftime("%H:%M:%S"))
    st.caption(now_utc.strftime("%A, %d/%m/%Y"))

st.button("🔄 Lam moi ngay bay gio")

with st.expander("📖 Tai chinh chiem tinh (Financial Astrology) la gi?", expanded=False):
    st.markdown(
        """
**Tai chinh chiem tinh** la truong phai su dung vi tri Mat Trang, cac hanh tinh
va goc chieu giua chung (aspect) de suy doan tam ly dam dong va bien dong
thi truong tai chinh — vi du: trang tron/trang non thuong gan voi diem dao
chieu tam ly, sao Thuy nghich hanh (Mercury retrograde) duoc mot so trader
cho la giai doan de xay ra sai sot giao dich/tin hieu nhieu.

⚠️ **Day KHONG phai phuong phap duoc khoa hoc hay tai chinh hoc chinh thong
cong nhan.** Khong co bang chung thong ke vung chac cho thay vi tri hanh
tinh anh huong gia tai san. Day chi la mot lop du lieu tham khao them ma
mot bo phan nho trader/nha dau tu quan tam su dung ben canh phan tich ky
thuat/co ban. Cac chi so trong dashboard nay duoc tinh 100% tu cong thuc
thien van that (khong bia dat), nhung *cach dien giai* thanh "tin hieu
xanh/do" la quy uoc chiem tinh pho bien, khong phai du bao co co so khoa hoc.
        """
    )

st.divider()

# ---------------------------------------------------------------------------
# Sidebar: trang thai chiem tinh hom nay + lich tin vi mo
# ---------------------------------------------------------------------------
today = now_utc.date()
today_signal = score_engine.daily_signal(today)

with st.sidebar:
    st.subheader("🔮 Trang thai hom nay")
    st.markdown(f"### {today_signal['moon_emoji']} {today_signal['moon_name']}")
    st.progress(today_signal["illumination"], text=f"Do sang trang: {today_signal['illumination']*100:.1f}%")

    if astro.is_mercury_retrograde(today):
        st.error("☿ Sao Thuy dang NGHICH HANH")
    else:
        nxt = astro.next_mercury_retrograde(today)
        if nxt:
            st.info(f"☿ Nghich hanh tiep theo: {nxt['start'].strftime('%d/%m/%Y')} → {nxt['end'].strftime('%d/%m/%Y')}")

    eclipse_today = astro.eclipse_on(today)
    if eclipse_today:
        st.warning(f"🌑 Hom nay: {eclipse_today}")

    st.divider()
    st.subheader("📅 Lich tin vi mo (30 ngay toi)")
    st.caption(f"Du lieu xac minh lan cuoi: {macro_calendar.last_verified()}")
    upcoming = macro_calendar.events_in_range(today, today + datetime.timedelta(days=30))
    if upcoming:
        for e in upcoming:
            d = datetime.date.fromisoformat(e["date"])
            impact_icon = "🔴" if e["impact"] == "high" else "🟠"
            st.markdown(f"{impact_icon} **{d.strftime('%d/%m')}** {e['time_et']} ET — {e['name']}")
    else:
        st.caption("Khong co su kien nao trong data/macro_calendar.json cho khoang nay.")

# ---------------------------------------------------------------------------
# Tang 1: bieu do 30 ngay (vach xanh/do, cao = manh)
# ---------------------------------------------------------------------------
st.subheader("📊 Chi bao chiem tinh 30 ngay")
st.caption("Moi vach = 1 ngay. Chieu cao vach = do manh tin hieu (1-5). Xanh = pha trang dang tron dan (waxing), Do = dang khuyet dan (waning) hoac sao Thuy nghich hanh. Bam vao 1 vach de xem chi tiet song nang luong theo gio.")

signals = score_engine.range_signals(today, 30)

dates = [s["date"] for s in signals]
strengths = [s["strength"] for s in signals]
colors = ["#2ecc71" if s["bias"] == "up" else "#e74c3c" for s in signals]
hover_text = [
    f"{s['date']}<br>{s['moon_emoji']} {s['moon_name']}<br>Do manh: {s['strength']}/5<br>"
    + ("<br>".join(t["label"] for t in s["tags"]) if s["tags"] else "Khong co su kien dac biet")
    for s in signals
]

fig = go.Figure(
    data=[
        go.Bar(
            x=dates,
            y=strengths,
            marker_color=colors,
            hovertext=hover_text,
            hoverinfo="text",
        )
    ]
)
fig.update_layout(
    height=380,
    yaxis=dict(title="Do manh (1-5)", range=[0, 5.5], dtick=1),
    xaxis=dict(title="Ngay", tickangle=-45),
    margin=dict(l=10, r=10, t=10, b=10),
)

# danh dau ngay co tin vi mo hoac nhat/nguyet thuc bang icon phia tren vach
annotations = []
for s in signals:
    icon = ""
    for t in s["tags"]:
        if t["kind"] in ("macro-high", "macro"):
            icon = "📅"
        elif t["kind"] == "eclipse":
            icon = "🌑"
        elif t["kind"] == "retrograde" and not icon:
            icon = "☿"
    if icon:
        annotations.append(dict(x=s["date"], y=s["strength"] + 0.3, text=icon, showarrow=False, font=dict(size=14)))
fig.update_layout(annotations=annotations)

event = st.plotly_chart(
    fig,
    use_container_width=True,
    on_select="rerun",
    selection_mode="points",
    key="bar_chart",
)

# xac dinh ngay duoc chon (click) - fallback = hom nay
selected_date_str = today.isoformat()
try:
    points = event.selection.points if event else []
    if points:
        selected_date_str = points[0]["x"]
except Exception:
    pass

st.divider()

# ---------------------------------------------------------------------------
# Tang 2: drill-down theo gio cho ngay duoc chon
# ---------------------------------------------------------------------------
col_a, col_b = st.columns([2, 1])
with col_b:
    picked = st.date_input(
        "Hoac chon ngay thu cong",
        value=datetime.date.fromisoformat(selected_date_str),
        min_value=today,
        max_value=today + datetime.timedelta(days=29),
    )
    selected_date_str = picked.isoformat()

selected_date = datetime.date.fromisoformat(selected_date_str)
hourly = score_engine.hourly_signal(selected_date)
day_signal = score_engine.daily_signal(selected_date)

with col_a:
    st.subheader(f"⏱️ Song nang luong theo gio — {selected_date.strftime('%d/%m/%Y')}")

hours = [f"{h:02d}:00" for h in range(24)]
fig2 = go.Figure(
    data=[
        go.Scatter(
            x=hours,
            y=hourly["wave"],
            mode="lines+markers",
            line=dict(color="#8e44ad", width=3),
            fill="tozeroy",
            fillcolor="rgba(142,68,173,0.15)",
        )
    ]
)
fig2.update_layout(
    height=320,
    yaxis=dict(title="Nang luong (0-1)", range=[0, 1]),
    xaxis=dict(title="Gio (UTC)"),
    margin=dict(l=10, r=10, t=10, b=10),
)
st.plotly_chart(fig2, use_container_width=True)

tag_cols = st.columns(3)
with tag_cols[0]:
    st.metric("Do manh ngay", f"{day_signal['strength']}/5")
with tag_cols[1]:
    st.metric("Xu huong pha trang", "Tron dan (Xanh)" if day_signal["bias"] == "up" else "Khuyet dan (Do)")
with tag_cols[2]:
    st.metric("Mat Trang", f"{day_signal['moon_emoji']} {day_signal['moon_name']}")

if hourly["strong_hour_ranges"]:
    st.markdown("**🕐 Khung gio song manh (top ~25% trong ngay):**")
    st.markdown(" &nbsp; ".join(f"`{r}`" for r in hourly["strong_hour_ranges"]))
else:
    st.caption("Khong xac dinh duoc khung gio noi bat.")

if day_signal["tags"]:
    st.markdown("**Su kien / nhan dac biet trong ngay:**")
    for t in day_signal["tags"]:
        st.markdown(f"- {t['label']}")

if hourly["macro_events"]:
    st.markdown("**📅 Tin vi mo trong ngay nay:**")
    for e in hourly["macro_events"]:
        st.markdown(f"- {e['time_et']} ET — **{e['name']}** ({e['source']})")

st.divider()
st.caption(
    "⚠️ Cong cu tham khao mang tinh chiem tinh, khong phai loi khuyen dau tu. "
    "Du lieu pha trang / nghich hanh / nhat-nguyet thuc va lich tin vi mo la du lieu that, "
    "nhung viec dien giai thanh tin hieu 'manh/yeu', 'xanh/do' la quy uoc chiem tinh, khong co co so khoa hoc."
)
