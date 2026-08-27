"""
telegram_notifier.py
---------------------
Gui thong bao qua Telegram Bot ve:
  1. Tin vi mo: nhac truoc 1 ngay + nhac lai dung ngay xay ra.
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

DISCLAIMER = "⚠️ Công cụ tham khảo mang tính chiêm tinh, không phải lời khuyên đầu tư."
APP_URL = "https://dubaochiemtinh.streamlit.app/"
APP_LINK_LINE = f"🔗 Truy cập {APP_URL} để xem chi tiết chiêm tinh"

BOT_COMMANDS = [
    {"command": "start", "description": "Đăng ký nhận thông báo chiêm tinh hàng ngày"},
    {"command": "stop", "description": "Huỷ đăng ký, ngừng nhận thông báo"},
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
    return f"{icon}{time_part} — {name}"


def _hour_range_label(range_str: str) -> str:
    start_s, end_s = range_str.split("-")
    return f"{int(start_s.split(':')[0])}h → {int(end_s.split(':')[0])}h"


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
        send_message(build_daily_digest())
    elif mode == "hourly":
        msg = build_hourly_alert()
        if msg:
            send_message(msg)
        else:
            print("[telegram_notifier] Giờ hiện tại không phải đầu 1 khung giờ sóng mạnh - không gửi.")
    elif mode == "setcommands":
        # Chi can chay 1 LAN DUY NHAT (thu cong) sau khi tao bot - dang ky
        # menu lenh "/" hien tren Telegram. Khong lien quan gi den viec
        # gui ban tin hang ngay/hang gio.
        set_bot_commands()
        print("[telegram_notifier] Da dang ky menu lenh /start, /stop.")
    else:
        raise SystemExit(f"Mode khong hop le: '{mode}' (dung 'daily', 'hourly' hoac 'setcommands')")


if __name__ == "__main__":
    main()
