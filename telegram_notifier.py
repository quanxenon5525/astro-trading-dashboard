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

NHIEU NGUOI DUNG: khong con gui toi 1 TELEGRAM_CHAT_ID co dinh nua. Danh
sach nguoi da dang ky duoc luu trong data/subscribers.json (list chat_id),
ai cung co the tu dang ky bang cach nhan /start cho bot - xem
telegram_bot_poll.py (script rieng, chay qua telegram_bot_poll.yml, lang
nghe lenh /start va /stop) de biet cach danh sach nay duoc cap nhat.
send_message() o day se gui cho TAT CA nguoi trong danh sach khi khong
truyen chat_id cu the.

QUAN TRONG ve mui gio: script nay co the chay tren server o BAT KY mui gio
nao (vd GitHub Actions chay UTC), nen moi thoi diem trong file nay deu ep
ro rang ve GIO VIET NAM (Asia/Ho_Chi_Minh, UTC+7 khong doi DST) bang
ZoneInfo, dam bao dung gio du chay o dau. macro_calendar.event_local_datetime()
gio cung da lam dung dieu nay (dung chung 1 cho, khong con tinh rieng o day).

Bien moi truong can co (dat trong GitHub repo Settings > Secrets and
variables > Actions):
  TELEGRAM_BOT_TOKEN - token bot lay tu @BotFather (secret TELEGRAM_CHAT_ID
  cu khong con can thiet nua, co the xoa)

Cach chay thu cong (debug):
  TELEGRAM_BOT_TOKEN=xxx python telegram_notifier.py daily
  TELEGRAM_BOT_TOKEN=xxx python telegram_notifier.py hourly
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
SUBSCRIBERS_PATH = os.path.join(os.path.dirname(__file__), "data", "subscribers.json")

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
    '/start - Dang ky nhan thong bao chiem tinh hang ngay'). Goi lai
    nhieu lan khong sao - Telegram luon GHI DE bang danh sach moi nhat,
    nen ham nay duoc goi moi lan telegram_bot_poll.py chay de menu luon
    dong bo voi code, khong can vao BotFather chinh tay."""
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    resp = requests.post(url, json={"commands": BOT_COMMANDS}, timeout=15)
    if not resp.ok:
        print(f"[telegram_notifier] Loi dang ky bo lenh: {resp.status_code} {resp.text}", file=sys.stderr)


def load_subscribers() -> list:
    """Doc danh sach chat_id da dang ky nhan thong bao. Tra ve [] neu file
    chua ton tai (chua ai dang ky) - khong loi."""
    if not os.path.exists(SUBSCRIBERS_PATH):
        return []
    with open(SUBSCRIBERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("chat_ids", [])


def save_subscribers(chat_ids: list) -> None:
    os.makedirs(os.path.dirname(SUBSCRIBERS_PATH), exist_ok=True)
    with open(SUBSCRIBERS_PATH, "w", encoding="utf-8") as f:
        json.dump({"chat_ids": sorted(set(chat_ids))}, f, ensure_ascii=False, indent=2)
        f.write("\n")


def add_subscriber(chat_id: int) -> bool:
    """Them 1 nguoi dang ky moi. Tra ve True neu la nguoi MOI (chua co
    truoc do), False neu da dang ky roi (idempotent - nhan /start nhieu
    lan khong bi trung)."""
    ids = load_subscribers()
    if chat_id in ids:
        return False
    ids.append(chat_id)
    save_subscribers(ids)
    return True


def remove_subscriber(chat_id: int) -> bool:
    """Xoa 1 nguoi dang ky (lenh /stop). Tra ve True neu thuc su co xoa."""
    ids = load_subscribers()
    if chat_id not in ids:
        return False
    ids.remove(chat_id)
    save_subscribers(ids)
    return True


def send_message(text: str, chat_id: int = None) -> None:
    """Gui 1 tin nhan. Neu chat_id=None (mac dinh), gui BROADCAST cho TOAN
    BO danh sach da dang ky trong data/subscribers.json. Loi khi gui cho 1
    nguoi (vd ho da chan/xoa bot) chi duoc LOG lai, KHONG lam dung ca vong
    lap - nhung nguoi con lai van phai nhan duoc tin."""
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit(
            "Thieu TELEGRAM_BOT_TOKEN trong bien moi truong "
            "(xem huong dan trong README.md muc 'Thong bao qua Telegram')."
        )
    targets = [chat_id] if chat_id is not None else load_subscribers()
    if not targets:
        print("[telegram_notifier] Chua co ai dang ky nhan tin (data/subscribers.json rong) - khong gui.")
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
    else:
        raise SystemExit(f"Mode khong hop le: '{mode}' (dung 'daily' hoac 'hourly')")


if __name__ == "__main__":
    main()
