/**
 * telegram_webhook.js
 * ---------------------
 * Cloudflare Worker lang nghe webhook TU TELEGRAM (KHONG polling) de xu ly
 * lenh /start (dang ky) va /stop (huy dang ky) - phan hoi TUC THI, khong
 * con do tre vai phut nhu cach cu (GitHub Actions cron moi 5 phut).
 *
 * Vi sao dung Cloudflare Worker: day la dich vu serverless CHAY THUONG
 * TRUC (khong bi "ngu" nhu Render free tier), MIEN PHI (100.000
 * request/ngay), va nhan duoc HTTP request tu Telegram NGAY LAP TUC khi
 * co tin nhan moi (webhook that su, khac han GitHub Actions chi chay
 * duoc theo lich dinh ky).
 *
 * Danh sach nguoi dang ky (subscribers) duoc luu trong Cloudflare KV (key
 * "chat_ids" -> mang JSON cac chat_id) - day la NGUON SU THAT DUY NHAT,
 * KHONG con dung file data/subscribers.json trong git nua (tranh het cac
 * van de git lock/nhanh main-master tung gap phai). Script
 * telegram_notifier.py (chay hang ngay/hang gio qua GitHub Actions) doc
 * lai danh sach nay qua Cloudflare KV REST API.
 *
 * CACH DEPLOY: xem huong dan chi tiet trong README.md muc "Thong bao qua
 * Telegram" - dan vao Cloudflare Dashboard, tao Worker moi, dan nguyen
 * noi dung file nay vao, gan KV namespace binding ten "SUBSCRIBERS_KV",
 * them bien moi truong (secret) "TELEGRAM_BOT_TOKEN", roi Deploy. Sau do
 * goi 1 lan API setWebhook de Telegram biet duong dan Worker nay.
 */

const WELCOME_TEXT =
  "🌙 <b>Chào mừng đến với Dự báo chiêm tinh!</b>\n\n" +
  "Bạn đã đăng ký thành công, mỗi ngày sẽ nhận được:\n" +
  "• Chỉ báo chiêm tinh (xanh/đỏ + quẻ)\n" +
  "• Khung giờ sóng năng lượng mạnh trong ngày\n" +
  "• Tin vĩ mô quan trọng (nhắc trước 1 ngày + đúng ngày diễn ra)\n\n" +
  "Gõ /stop bất kỳ lúc nào để huỷ đăng ký.\n\n" +
  "🔗 Truy cập https://dubaochiemtinh.streamlit.app/ để xem chi tiết chiêm tinh\n" +
  "⚠️ Công cụ tham khảo mang tính chiêm tinh, không phải lời khuyên đầu tư.";

const ALREADY_SUBSCRIBED_TEXT =
  "✅ Bạn đã đăng ký từ trước rồi, sẽ tiếp tục nhận thông báo mỗi ngày.";

const GOODBYE_TEXT =
  "👋 Bạn đã huỷ đăng ký, sẽ không nhận thông báo nữa.\n" +
  "Gõ /start bất kỳ lúc nào để đăng ký lại.";

const NOT_SUBSCRIBED_TEXT = "Bạn hiện chưa đăng ký nhận thông báo nào cả.";

const SUBSCRIBERS_KEY = "chat_ids";

async function getSubscribers(env) {
  const raw = await env.SUBSCRIBERS_KV.get(SUBSCRIBERS_KEY);
  return raw ? JSON.parse(raw) : [];
}

async function saveSubscribers(env, ids) {
  const unique = Array.from(new Set(ids));
  await env.SUBSCRIBERS_KV.put(SUBSCRIBERS_KEY, JSON.stringify(unique));
}

async function sendMessage(env, chatId, text) {
  const url = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`;
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chat_id: chatId,
      text,
      parse_mode: "HTML",
      disable_web_page_preview: true,
    }),
  });
  if (!resp.ok) {
    console.log("Loi gui tin toi " + chatId + ": " + resp.status + " " + (await resp.text()));
  }
}

export default {
  async fetch(request, env) {
    if (request.method !== "POST") {
      // Cho phep GET de test nhanh Worker con song khong (vd mo thang
      // trinh duyet vao URL Worker), khong lien quan gi den Telegram.
      return new Response("astro telegram webhook: OK", { status: 200 });
    }

    let update;
    try {
      update = await request.json();
    } catch (err) {
      return new Response("bad request", { status: 400 });
    }

    const msg = update.message || update.edited_message;
    // Telegram yeu cau webhook LUON tra ve 200 nhanh, ke ca voi cac loai
    // update khong lien quan (sticker, anh, thanh vien moi vao nhom...)
    // de tranh Telegram nghi la loi va retry lien tuc.
    if (!msg || !msg.text) {
      return new Response("ok", { status: 200 });
    }

    const chatId = msg.chat.id;
    const text = msg.text.trim().toLowerCase();

    if (text.startsWith("/start")) {
      const ids = await getSubscribers(env);
      if (ids.includes(chatId)) {
        await sendMessage(env, chatId, ALREADY_SUBSCRIBED_TEXT);
      } else {
        ids.push(chatId);
        await saveSubscribers(env, ids);
        await sendMessage(env, chatId, WELCOME_TEXT);
      }
    } else if (text.startsWith("/stop")) {
      const ids = await getSubscribers(env);
      if (ids.includes(chatId)) {
        await saveSubscribers(env, ids.filter((id) => id !== chatId));
        await sendMessage(env, chatId, GOODBYE_TEXT);
      } else {
        await sendMessage(env, chatId, NOT_SUBSCRIBED_TEXT);
      }
    }

    return new Response("ok", { status: 200 });
  },
};
