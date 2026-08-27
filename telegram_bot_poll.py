"""
telegram_bot_poll.py
----------------------
Lang nghe lenh /start (dang ky nhan thong bao) va /stop (huy dang ky) tu
nguoi dung Telegram, bang cach GOI DINH KY (polling) Telegram Bot API
getUpdates - KHONG dung webhook, vi du an nay khong co server thuong truc
(Streamlit Cloud chi chay giao dien, khong nhan duoc request tu Telegram;
GitHub Actions runner chi la may ao TAM THOI, chay xong la mat).

Chay qua GitHub Actions moi 5 phut (xem .github/workflows/telegram_bot_poll.yml
- day la khoang cach toi thieu GitHub Actions ho tro cho lich chay dinh ky,
nen phan hoi /start co the tre vai phut, KHONG phai loi).

Vi runner la TAM THOI (khong giu duoc bien nho giua cac lan chay), 2 file
state duoi day PHAI duoc GIT COMMIT LAI vao repo sau moi lan chay (xem
buoc "Commit" trong workflow, dung GITHUB_TOKEN mac dinh cua Actions -
HOAN TOAN KHAC voi git tren may ban, khong lien quan gi den nhau):
  data/subscribers.json     - danh sach chat_id dang dang ky (dung chung
                               voi telegram_notifier.py)
  data/telegram_offset.json - update_id Telegram da xu ly gan nhat, tranh
                               xu ly lai 1 tin nhan nhieu lan

Muon workflow commit lai duoc, repo phai bat "Read and write permissions"
cho GITHUB_TOKEN: Settings > Actions > General > Workflow permissions
(xem huong dan trong README.md).
"""

import json
import os

import requests

import telegram_notifier as tn

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OFFSET_PATH = os.path.join(os.path.dirname(__file__), "data", "telegram_offset.json")

WELCOME_TEXT = (
    "🌙 <b>Chào mừng đến với Dự báo chiêm tinh!</b>\n\n"
    "Bạn đã đăng ký thành công, mỗi ngày sẽ nhận được:\n"
    "• Chỉ báo chiêm tinh (xanh/đỏ + quẻ)\n"
    "• Khung giờ sóng năng lượng mạnh trong ngày\n"
    "• Tin vĩ mô quan trọng (nhắc trước 1 ngày + đúng ngày diễn ra)\n\n"
    "Gõ /stop bất kỳ lúc nào để huỷ đăng ký.\n\n"
    f"{tn.APP_LINK_LINE}\n{tn.DISCLAIMER}"
)

ALREADY_SUBSCRIBED_TEXT = "✅ Bạn đã đăng ký từ trước rồi, sẽ tiếp tục nhận thông báo mỗi ngày."

GOODBYE_TEXT = (
    "👋 Bạn đã huỷ đăng ký, sẽ không nhận thông báo nữa.\n"
    "Gõ /start bất kỳ lúc nào để đăng ký lại."
)


def _load_offset() -> int:
    if not os.path.exists(OFFSET_PATH):
        return 0
    with open(OFFSET_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("last_update_id", 0)


def _save_offset(update_id: int) -> None:
    os.makedirs(os.path.dirname(OFFSET_PATH), exist_ok=True)
    with open(OFFSET_PATH, "w", encoding="utf-8") as f:
        json.dump({"last_update_id": update_id}, f)
        f.write("\n")


def poll_once() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit("Thieu TELEGRAM_BOT_TOKEN trong bien moi truong.")

    offset = _load_offset()
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    resp = requests.get(url, params={"offset": offset + 1, "timeout": 0}, timeout=15)
    resp.raise_for_status()
    updates = resp.json().get("result", [])

    max_update_id = offset
    for upd in updates:
        max_update_id = max(max_update_id, upd["update_id"])
        msg = upd.get("message") or upd.get("edited_message")
        if not msg or "text" not in msg:
            continue

        chat_id = msg["chat"]["id"]
        text = msg["text"].strip().lower()

        if text.startswith("/start"):
            is_new = tn.add_subscriber(chat_id)
            if is_new:
                print(f"[telegram_bot_poll] Dang ky moi: {chat_id}")
                tn.send_message(WELCOME_TEXT, chat_id=chat_id)
                # Gui luon ban tin hom nay ngay khi vua dang ky, de nguoi
                # dung thay ket qua ngay thay vi phai doi den 7h sang hom sau.
                tn.send_message(tn.build_daily_digest(), chat_id=chat_id)
            else:
                print(f"[telegram_bot_poll] {chat_id} da dang ky tu truoc.")
                tn.send_message(ALREADY_SUBSCRIBED_TEXT, chat_id=chat_id)
        elif text.startswith("/stop"):
            removed = tn.remove_subscriber(chat_id)
            if removed:
                print(f"[telegram_bot_poll] Huy dang ky: {chat_id}")
                tn.send_message(GOODBYE_TEXT, chat_id=chat_id)

    if max_update_id != offset:
        _save_offset(max_update_id)


if __name__ == "__main__":
    poll_once()
