"""
telegram_notifier.py
---------------------
Gui thong bao qua Telegram Bot ve:
  1. Tin vi mo: nhac truoc 1 ngay + nhac lai dung ngay xay ra (ban tin sang,
     'daily'), CONG THEM 2 canh bao THOI GIAN THUC qua che do 'hourly':
       a. Truoc ~2 gio khi 1 tin sap dien ra (Ky vong + Truoc do).
       b. Ngay khi co so lieu Thuc te vua duoc ForexFactory cong bo.
     Ca 2 canh bao nay dung Cloudflare KV de danh dau da bao, tranh gui
     trung lap qua nhieu lan chay cron hang gio (xem
     build_macro_pre_alerts/build_macro_actual_alerts).
  2. Chi bao chiem tinh trong ngay: xanh/do + "que" (Dai Cat/Cat/Tieu Cat/
     Binh/Tieu Hung/Hung/Dai Hung) suy tu do manh tin hieu (1-5) + bias -
     dung DUNG cac gia tri co san tu score_engine.daily_signal(), khong
     tinh toan rieng.
  3. Song nang luong theo gio: bao ngay tu tong quan buoi sang (Tang 1),
     va bao THOI GIAN THUC ngay khi bat dau 1 khung gio song manh (Tang 2).

Chay DOC LAP - khong phu thuoc Streamlit dang chay hay khong, vi tinh toan
chiem tinh 100% offline (dung lai score_engine.py/astro.py/macro_calendar.py
co san). Thiet ke de chay qua GitHub Actions scheduled workflow (xem
.github/workflows/telegram_daily.yml va telegram_hourly.yml) - KHONG dung
Render Cron Job vi tinh nang do khong co trong goi Render mien phi.

NHIEU NGUOI DUNG: khong con gui toi 1 TELEGRAM_CHAT_ID co dinh nua. Ai
cung co the tu dang ky bang cach nhan /start cho bot - lenh nay duoc xu ly
TUC THI boi Cloudflare Worker (xem cloudflare/telegram_webhook.js), KHONG
con polling qua GitHub Actions nua (cach cu co do tre vai phut, khong on
dinh). Danh sach chat_id da dang ky duoc Worker luu trong Cloudflare KV -
day la NGUON SU THAT DUY NHAT, KHONG con la file data/subscribers.json
trong git (tranh het cac van de git lock/lech nhanh main-master). Ham
load_subscribers() o day GOI QUA Cloudflare KV REST API de doc lai danh
sach nay khi gui ban tin hang ngay/hang gio.

QUAN TRONG ve mui gio: script nay co the chay tren server o BAT KY mui gio
nao (vd GitHub Actions chay UTC), nen moi thoi diem trong file nay deu ep
ro rang ve GIO VIET NAM (Asia/Ho_Chi_Minh, UTC+7 khong doi DST) bang
ZoneInfo, dam bao dung gio du chay o dau. macro_calendar.event_local_datetime()
gio cung da lam dung dieu nay (dung chung 1 cho, khong con tinh rieng o day).

Bien moi truong can co (dat trong GitHub repo Settings > Secrets and
variables > Actions) - xem huong dan tao trong README.md muc "Thong bao
qua Telegram":
  TELEGRAM_BOT_TOKEN  - token bot lay tu @BotFather
  CF_ACCOUNT_ID       - Account ID cua Cloudflare (Dashboard > sidebar phai)
  CF_KV_NAMESPACE_ID  - ID cua KV namespace da tao va gan cho Worker
  CF_API_TOKEN        - API Token Cloudflare co quyen doc/ghi Workers KV

Cach chay thu cong (debug):
  TELEGRAM_BOT_TOKEN=xxx CF_ACCOUNT_ID=xxx CF_KV_NAMESPACE_ID=xxx CF_API_TOKEN=xxx python telegram_notifier.py daily
  TELEGRAM_BOT_TOKEN=xxx CF_ACCOUNT_ID=xxx CF_KV_NAMESPACE_ID=xxx CF_API_TOKEN=xxx python telegram_notifier.py hourly
  TELEGRAM_BOT_TOKEN=xxx python telegram_notifier.py setcommands   # dang ky menu lenh /, chi can chay 1 lan
"""

import datetime
import json
import os
import sys
from zoneinfo import ZoneInfo

import requests

import macro_calendar
import score_engine
from i18n import ECLIPSE_LABELS, MOON_PHASE_LABELS, ZODIAC_LABELS

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
LANG = "vi"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")
CF_KV_NAMESPACE_ID = os.environ.get("CF_KV_NAMESPACE_ID", "")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
CF_SUBSCRIBERS_KEY = "chat_ids"
CF_DIGEST_CACHE_KEY = "latest_digest"
CF_MACRO_STATE_KEY = "macro_notified_state"

# Bao truoc bao nhieu gio khi co 1 tin vi mo sap dien ra (theo yeu cau).
MACRO_PRE_ALERT_HOURS = 2.0
# Do rong "cua so" quanh moc MACRO_PRE_ALERT_HOURS (vi cron chay MOI GIO 1
# lan - xem telegram_hourly.yml - nen phai co 1 khoang du rong de chac chan
# co 1 lan chay roi vao dung khoang "~2 gio truoc", khong bi troi qua mat).
MACRO_PRE_ALERT_WINDOW_HOURS = 0.6

DISCLAIMER = "⚠️ Công cụ tham khảo mang tính chiêm tinh, không phải lời khuyên đầu tư."
APP_URL = "https://dubaochiemtinh.streamlit.app/"
APP_LINK_LINE = f"🔗 Truy cập {APP_URL} để xem chi tiết chiêm tinh"

BOT_COMMANDS = [
    {"command": "start", "description": "Đăng ký nhận thông báo chiêm tinh hàng ngày"},
    {"command": "stop", "description": "Huỷ đăng ký, ngừng nhận thông báo"},
    {"command": "check", "description": "Xem ngay chỉ báo chiêm tinh hôm nay"},
]

_TREND_ARROWS = {"rising": "▲", "falling": "▼", "peak_mid": "◆", "flat": "→"}
_TREND_LABELS = {
    "rising": "Đang mạnh dần lên",
    "falling": "Đang yếu dần đi",
    "peak_mid": "Tăng rồi giảm trong khung",
    "flat": "Ổn định",
}


def now_vn() -> datetime.datetime:
    return datetime.datetime.now(VN_TZ)


def set_bot_commands() -> None:
    """Dang ky danh sach lenh trong BOT_COMMANDS voi Telegram, de khi
    nguoi dung go '/' trong khung chat se hien menu goi y kem mo ta (vd
    '/start - Dang ky nhan thong bao chiem tinh hang ngay'). CHI CAN goi 1
    LAN DUY NHAT sau khi tao bot (vd qua 'python telegram_notifier.py
    setcommands') - Telegram luu vinh vien, khong can goi lai moi lan
    gui tin. Khong lien quan gi den Cloudflare Worker xu ly /start, /stop."""
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    resp = requests.post(url, json={"commands": BOT_COMMANDS}, timeout=15)
    if not resp.ok:
        print(f"[telegram_notifier] Loi dang ky bo lenh: {resp.status_code} {resp.text}", file=sys.stderr)


def load_subscribers() -> list:
    """Doc danh sach chat_id da dang ky, qua Cloudflare KV REST API (nguon
    su that duy nhat - duoc Cloudflare Worker ghi vao NGAY khi co nguoi
    /start hoac /stop, xem cloudflare/telegram_webhook.js). Tra ve [] neu
    thieu cau hinh Cloudflare hoac chua co ai dang ky - khong loi, chi in
    canh bao de de debug."""
    if not (CF_ACCOUNT_ID and CF_KV_NAMESPACE_ID and CF_API_TOKEN):
        print(
            "[telegram_notifier] Thieu CF_ACCOUNT_ID/CF_KV_NAMESPACE_ID/CF_API_TOKEN "
            "- khong doc duoc danh sach dang ky tu Cloudflare KV.",
            file=sys.stderr,
        )
        return []
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"
        f"/storage/kv/namespaces/{CF_KV_NAMESPACE_ID}/values/{CF_SUBSCRIBERS_KEY}"
    )
    resp = requests.get(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}, timeout=15)
    if resp.status_code == 404:
        # Chua tung co ai /start (key chua duoc Worker tao) - khong phai loi.
        return []
    if not resp.ok:
        print(f"[telegram_notifier] Loi doc Cloudflare KV: {resp.status_code} {resp.text}", file=sys.stderr)
        return []
    try:
        return resp.json()
    except ValueError:
        return []


def save_digest_cache(text: str) -> None:
    """Luu ban tin chiem tinh hom nay vao Cloudflare KV (key
    "latest_digest"), de lenh /check tren Telegram (xu ly boi Cloudflare
    Worker - xem cloudflare/telegram_webhook.js) tra loi TUC THI ma
    khong can cho GitHub Actions chay lai. An toan de cache: noi dung
    build_daily_digest() hoan toan xac dinh THEO NGAY (khong phu thuoc
    gio trong ngay, vi app khong lay du lieu gia/thi truong nao ca), nen
    cache khong bao gio bi "sai lech" trong ngay - chi can lam moi it
    nhat 1 lan/ngay. Ham nay duoc goi o CA 2 che do 'daily' va 'hourly'
    trong main() de cache luon duoc lam moi hang gio (dam bao ngay sau
    khi qua nua dem, cache cung nhanh chong duoc cap nhat sang ngay moi
    ma khong phai doi den 7h sang)."""
    if not (CF_ACCOUNT_ID and CF_KV_NAMESPACE_ID and CF_API_TOKEN):
        return
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"
        f"/storage/kv/namespaces/{CF_KV_NAMESPACE_ID}/values/{CF_DIGEST_CACHE_KEY}"
    )
    resp = requests.put(
        url,
        headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
        data=text.encode("utf-8"),
        timeout=15,
    )
    if not resp.ok:
        print(f"[telegram_notifier] Loi luu cache ban tin: {resp.status_code} {resp.text}", file=sys.stderr)


def load_macro_notified_state() -> dict:
    """Doc trang thai 'da bao tin vi mo nao roi' tu Cloudflare KV (key
    "macro_notified_state") - CAN co bo nho nay vi GitHub Actions chay
    "khong trang thai" (moi lan chay la 1 may ao moi), nen phai luu vao
    Cloudflare KV (giong subscribers/digest cache) de KHONG bao lai trung
    lap cung 1 tin qua nhieu lan chay hang gio. Tra ve cau truc rong neu
    thieu cau hinh Cloudflare hoac chua tung luu - khong loi, chi co nguy
    co bao lai 1-2 lan trong truong hop hiem nay (uu tien khong crash)."""
    empty = {"pre2h": [], "actual": []}
    if not (CF_ACCOUNT_ID and CF_KV_NAMESPACE_ID and CF_API_TOKEN):
        return empty
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"
        f"/storage/kv/namespaces/{CF_KV_NAMESPACE_ID}/values/{CF_MACRO_STATE_KEY}"
    )
    resp = requests.get(url, headers={"Authorization": f"Bearer {CF_API_TOKEN}"}, timeout=15)
    if resp.status_code == 404:
        return empty
    if not resp.ok:
        print(f"[telegram_notifier] Loi doc trang thai tin vi mo: {resp.status_code} {resp.text}", file=sys.stderr)
        return empty
    try:
        data = resp.json()
        data.setdefault("pre2h", [])
        data.setdefault("actual", [])
        return data
    except ValueError:
        return empty


def save_macro_notified_state(state: dict) -> None:
    if not (CF_ACCOUNT_ID and CF_KV_NAMESPACE_ID and CF_API_TOKEN):
        return
    url = (
        f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}"
        f"/storage/kv/namespaces/{CF_KV_NAMESPACE_ID}/values/{CF_MACRO_STATE_KEY}"
    )
    resp = requests.put(
        url,
        headers={"Authorization": f"Bearer {CF_API_TOKEN}"},
        data=json.dumps(state).encode("utf-8"),
        timeout=15,
    )
    if not resp.ok:
        print(f"[telegram_notifier] Loi luu trang thai tin vi mo: {resp.status_code} {resp.text}", file=sys.stderr)


def send_message(text: str, chat_id: int = None) -> None:
    """Gui 1 tin nhan. Neu chat_id=None (mac dinh), gui BROADCAST cho TOAN
    BO danh sach dang ky doc tu Cloudflare KV. Loi khi gui cho 1 nguoi (vd
    ho da chan/xoa bot) chi duoc LOG lai, KHONG lam dung ca vong lap -
    nhung nguoi con lai van phai nhan duoc tin."""
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit(
            "Thieu TELEGRAM_BOT_TOKEN trong bien moi truong "
            "(xem huong dan trong README.md muc 'Thong bao qua Telegram')."
        )
    targets = [chat_id] if chat_id is not None else load_subscribers()
    if not targets:
        print("[telegram_notifier] Chua co ai dang ky nhan tin - khong gui.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for cid in targets:
        resp = requests.post(
            url,
            json={
                "chat_id": cid,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        if not resp.ok:
            print(f"[telegram_notifier] Loi gui toi {cid}: {resp.status_code} {resp.text}", file=sys.stderr)
            continue
        print(f"[telegram_notifier] Da gui toi {cid}.")


# ---------------------------------------------------------------------------
# "Que" chiem tinh: suy TRUC TIEP tu do manh tin hieu (1-5, score_engine.py)
# + bias (len/xuong) - dung thuat ngu gieo que truyen thong de de hinh dung,
# khong phai 1 phep tinh moi, chi la CACH DAT TEN cho gia tri co san.
# ---------------------------------------------------------------------------
def que_label(strength: int, bias: str) -> str:
    if bias == "up":
        return {5: "🟢 Đại Cát", 4: "🟢 Cát", 3: "🟢 Tiểu Cát"}.get(strength, "⚪ Bình")
    return {5: "🔴 Đại Hung", 4: "🔴 Hung", 3: "🔴 Tiểu Hung"}.get(strength, "⚪ Bình")


def _macro_line(e: dict) -> str:
    vn_dt = macro_calendar.event_local_datetime(e)
    time_part = f" {vn_dt.strftime('%H:%M')}" if vn_dt else ""
    icon = "🔴" if e.get("impact") == "high" else "🟠"
    name = e.get("name_vi") or e.get("name_en", "")
    # Ky vong / Truoc do / Thuc te - doc truc tiep tu du lieu da chuan hoa
    # trong macro_calendar.py (forecast/previous/actual); su kien tinh
    # (NFP/CPI/PPI/FOMC trong file JSON) mac dinh la "-" ca 3 truong, chi
    # su kien tu ForexFactory moi co gia tri that.
    kv = e.get("forecast", "-")
    td = e.get("previous", "-")
    tt = e.get("actual", "-")
    return f"{icon}{time_part} — {name}\n   KV: {kv} · TĐ: {td} · TT: {tt}"


def _hour_range_label(range_str: str) -> str:
    start_s, end_s = range_str.split("-")
    return f"{int(start_s.split(':')[0])}h → {int(end_s.split(':')[0])}h"


def _macro_event_key(e: dict) -> str:
    """Khoa duy nhat cho 1 su kien vi mo, dung de chong bao TRUNG LAP qua
    Cloudflare KV - ghep ngay + gio ET + ten tieng Anh (on dinh hon ten VN
    vi co the sua lai cau chu ma khong doi ban chat su kien)."""
    return f"{e['date']}|{e.get('time_et', '-')}|{e.get('name_en') or e.get('name_vi', '')}"


def _prune_macro_state(state: dict, today: datetime.date, keep_days: int = 10) -> dict:
    """Xoa cac khoa qua cu (ngay nam ngoai [today - keep_days, today]) khoi
    trang thai da bao, tranh danh sach phinh to vo han theo thoi gian."""
    cutoff = today - datetime.timedelta(days=keep_days)

    def _keep(key: str) -> bool:
        try:
            d = datetime.date.fromisoformat(key.split("|", 1)[0])
        except ValueError:
            return True
        return d >= cutoff

    return {
        "pre2h": [k for k in state.get("pre2h", []) if _keep(k)],
        "actual": [k for k in state.get("actual", []) if _keep(k)],
    }


def build_macro_pre_alerts() -> list:
    """Bao TRUOC 2 GIO khi co 1 tin vi mo sap dien ra (theo yeu cau) - chi
    ap dung cho su kien co GIO CU THE (time_et khac '-'), vi khong the tinh
    'con bao nhieu gio nua' cho su kien chi co ngay (vd FOMC ngay 1/2). Dung
    Cloudflare KV de danh dau da bao roi, tranh gui trung lap qua nhieu lan
    chay cron hang gio."""
    now = now_vn()
    today = now.date()
    state = load_macro_notified_state()
    already_sent = set(state.get("pre2h", []))
    lo = MACRO_PRE_ALERT_HOURS - MACRO_PRE_ALERT_WINDOW_HOURS
    hi = MACRO_PRE_ALERT_HOURS + MACRO_PRE_ALERT_WINDOW_HOURS

    alerts = []
    new_keys = []
    for offset in range(-1, 3):  # tu HOM QUA (theo ngay ET) den 2 ngay toi
        # QUAN TRONG: "date" cua su kien la ngay theo GIO ET (xem
        # macro_calendar.py), nhung "today" o day la ngay theo GIO VN - 1
        # su kien cong bo cuoi ngay ET (vd FOMC 14:00 ET ~ 01:00 sang hom
        # sau gio VN) se co "date" (ET) LUI 1 NGAY so voi ngay VN luc no
        # thuc su dien ra - phai quet ca "hom qua" (theo ET) moi khong bi
        # sot cac truong hop nay.
        for e in macro_calendar.events_on(today + datetime.timedelta(days=offset)):
            local_dt = macro_calendar.event_local_datetime(e)
            if not local_dt:
                continue
            diff_hours = (local_dt - now).total_seconds() / 3600.0
            if not (lo <= diff_hours <= hi):
                continue
            key = _macro_event_key(e)
            if key in already_sent:
                continue
            name = e.get("name_vi") or e.get("name_en", "")
            lines = [
                "⏰ <b>Sắp có tin vĩ mô!</b>",
                f"{name}",
                f"Thời gian: <b>{local_dt.strftime('%H:%M %d/%m')}</b> (giờ VN) — còn khoảng {MACRO_PRE_ALERT_HOURS:.0f} giờ nữa",
                f"Kỳ vọng: {e.get('forecast', '-')} · Trước đó: {e.get('previous', '-')}",
                "",
                APP_LINK_LINE,
                DISCLAIMER,
            ]
            alerts.append("\n".join(lines))
            new_keys.append(key)

    if new_keys:
        state["pre2h"] = list(already_sent | set(new_keys))
        state = _prune_macro_state(state, today)
        save_macro_notified_state(state)
    return alerts


def build_macro_actual_alerts() -> list:
    """Bao NGAY KHI co so lieu Thuc te vua duoc cong bo (so voi lan fetch
    truoc do tu ForexFactory van con la '-') - vi cron chay moi gio (xem
    telegram_hourly.yml), do tre toi da la ~1 gio ke tu luc tin cong bo
    thuc su, cham nhat la khi feed ForexFactory cap nhat gia tri 'actual'.
    Dung Cloudflare KV de chi bao DUNG 1 LAN cho moi su kien."""
    now = now_vn()
    today = now.date()
    state = load_macro_notified_state()
    already_sent = set(state.get("actual", []))

    alerts = []
    new_keys = []
    for offset in range(-2, 1):  # tin cong bo tu 2 ngay truoc den hom nay
        for e in macro_calendar.events_on(today + datetime.timedelta(days=offset)):
            local_dt = macro_calendar.event_local_datetime(e)
            if not local_dt or local_dt > now:
                continue  # chua toi gio cong bo thi chua co so lieu thuc te
            actual = e.get("actual", "-")
            if not actual or actual == "-":
                continue  # ForexFactory chua cap nhat gia tri that
            key = _macro_event_key(e)
            if key in already_sent:
                continue
            name = e.get("name_vi") or e.get("name_en", "")
            lines = [
                "📊 <b>Đã có số liệu thực tế!</b>",
                f"{name}",
                f"Thời gian công bố: {local_dt.strftime('%H:%M %d/%m')} (giờ VN)",
                f"Thực tế: <b>{actual}</b> · Kỳ vọng: {e.get('forecast', '-')} · Trước đó: {e.get('previous', '-')}",
                "",
                APP_LINK_LINE,
                DISCLAIMER,
            ]
            alerts.append("\n".join(lines))
            new_keys.append(key)

    if new_keys:
        state["actual"] = list(already_sent | set(new_keys))
        state = _prune_macro_state(state, today)
        save_macro_notified_state(state)
    return alerts


def build_daily_digest() -> str:
    """Bao 1 lan/ngay (buoi sang): chi bao chiem tinh hom nay + tin vi mo
    ngay mai (nhac truoc 1 ngay) + tin vi mo hom nay (nhac dung ngay) + toan
    bo khung gio song manh du kien trong ngay (xem truoc, chi tiet thuc te
    se duoc bao rieng luc bat dau tung khung qua che do 'hourly')."""
    today = now_vn().date()
    tomorrow = today + datetime.timedelta(days=1)

    sig = score_engine.daily_signal(today)
    bias_text = "🟢 Xanh (tăng)" if sig["bias"] == "up" else "🔴 Đỏ (giảm)"
    que = que_label(sig["strength"], sig["bias"])

    lines = [
        f"🌙 <b>Chỉ báo chiêm tinh — {today.strftime('%d/%m/%Y')}</b>",
        "",
        f"Xu hướng: <b>{bias_text}</b> · Độ mạnh {sig['strength']}/5",
        f"Quẻ: <b>{que}</b>",
        f"{sig['moon_emoji']} {MOON_PHASE_LABELS[LANG][sig['moon_phase_key']]} · Cung: {ZODIAC_LABELS[LANG][sig['moon_sign']]}",
    ]

    eclipse_tag = next((tg for tg in sig["tags"] if tg["kind"] == "eclipse"), None)
    if eclipse_tag:
        lines.append(f"🌑 {ECLIPSE_LABELS[LANG][eclipse_tag['eclipse_kind']]}")

    hourly = score_engine.hourly_signal(today)
    lines.append("")
    lines.append("📈 <b>Khung giờ sóng mạnh dự kiến hôm nay:</b>")
    if hourly["strong_hour_details"]:
        for d in hourly["strong_hour_details"]:
            arrow = _TREND_ARROWS.get(d["trend"], "")
            lines.append(f"• {_hour_range_label(d['range'])} {arrow} (đỉnh {d['peak']:.2f})")
    else:
        lines.append("Không có khung giờ nổi bật.")

    tomorrow_events = macro_calendar.events_on(tomorrow)
    lines.append("")
    lines.append(f"📅 <b>Tin vĩ mô ngày mai ({tomorrow.strftime('%d/%m')}):</b>")
    lines.extend([_macro_line(e) for e in tomorrow_events] if tomorrow_events else ["Không có sự kiện nào."])

    today_events = macro_calendar.events_on(today)
    lines.append("")
    lines.append(f"📅 <b>Tin vĩ mô hôm nay ({today.strftime('%d/%m')}):</b>")
    lines.extend([_macro_line(e) for e in today_events] if today_events else ["Không có sự kiện nào."])

    lines.append("")
    lines.append(APP_LINK_LINE)
    lines.append(DISCLAIMER)
    return "\n".join(lines)


def build_hourly_alert():
    """Bao THOI GIAN THUC: chay moi gio, chi gui tin khi GIO HIEN TAI (theo
    gio VN) la GIO BAT DAU cua 1 khung gio song manh trong ngay - moi khung
    chi bao dung 1 lan (luc bat dau), khong lap lai moi gio trong khung."""
    now = now_vn()
    today = now.date()
    current_hour = now.hour

    hourly = score_engine.hourly_signal(today)
    detail = next(
        (d for d in hourly["strong_hour_details"] if d["start_hour"] == current_hour),
        None,
    )
    if not detail:
        return None

    arrow = _TREND_ARROWS.get(detail["trend"], "")
    trend_text = _TREND_LABELS.get(detail["trend"], "")

    lines = [
        "📈 <b>Sóng năng lượng mạnh!</b>",
        f"Khung giờ: <b>{_hour_range_label(detail['range'])}</b>",
        f"Xu hướng: {arrow} {trend_text}",
        f"Đỉnh năng lượng: {detail['peak']:.2f}",
        "",
        APP_LINK_LINE,
        DISCLAIMER,
    ]
    return "\n".join(lines)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    if mode == "daily":
        digest = build_daily_digest()
        send_message(digest)
        save_digest_cache(digest)
    elif mode == "hourly":
        msg = build_hourly_alert()
        if msg:
            send_message(msg)
        else:
            print("[telegram_notifier] Giờ hiện tại không phải đầu 1 khung giờ sóng mạnh - không gửi.")

        # Canh bao tin vi mo: truoc ~2 gio khi tin sap dien ra, VA ngay khi
        # co so lieu Thuc te vua duoc cong bo - moi tin chi bao dung 1 lan
        # cho moi loai (xem build_macro_pre_alerts/build_macro_actual_alerts).
        for alert in build_macro_pre_alerts():
            send_message(alert)
        for alert in build_macro_actual_alerts():
            send_message(alert)

        # Luon lam moi cache ban tin hang ngay o day (moi gio), de lenh
        # /check tren Telegram luon co san du lieu tuong doi moi, khong
        # phai cho den 7h sang hom sau.
        save_digest_cache(build_daily_digest())
    elif mode == "setcommands":
        # Chi can chay 1 LAN DUY NHAT (thu cong) sau khi tao bot - dang ky
        # menu lenh "/" hien tren Telegram. Khong lien quan gi den viec
        # gui ban tin hang ngay/hang gio.
        set_bot_commands()
        print("[telegram_notifier] Da dang ky menu lenh /start, /stop, /check.")
    else:
        raise SystemExit(f"Mode khong hop le: '{mode}' (dung 'daily', 'hourly' hoac 'setcommands')")


if __name__ == "__main__":
    main()
