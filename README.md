# 🌙 Astro Financial Signal Dashboard

Dashboard Streamlit hien thi **thoi gian thuc + lich tin vi mo that + chi bao
chiem tinh tai chinh** (pha trang, sao Thuy nghich hanh, nhat/nguyet thuc).

**Khong lay/hien thi gia cua bat ky san giao dich nao** — chi tap trung vao
thoi gian, tin tuc vi mo va tin hieu chiem tinh, theo dung yeu cau.

⚠️ Day la cong cu tham khao mang tinh chiem tinh/giai tri, **khong duoc khoa
hoc/tai chinh hoc chinh thong cong nhan** va **khong phai loi khuyen dau tu**.

## Cau truc project

| File | Vai tro |
|---|---|
| `astro.py` | Pha trang, kinh do/vi do Mat Trang, cung hoang dao that (cong thuc Meeus) + nghich hanh **tu dong tinh** cho moi hanh tinh/moi nam (khong con go tay ngay thang) + du lieu nhat/nguyet thuc 2026 |
| `planets.py` | Vi tri that cua Sao Thuy/Kim/Hoa/Moc/Tho bang phuong phap Kepler Elements (chuan JPL/NASA, offline 100%) |
| `aspects.py` | Goc chieu THAT (hop/luc hop/vuong/tam hop/doi dinh) giua Mat Troi/Mat Trang/5 hanh tinh, co dung sai (orb) va do "khop" (exactness) |
| `houses.py` | Gio sao dia phuong + diem Moc (Ascendant) THAT theo toa do quan sat - nguon bien dong nhanh nhat trong ngay (Trai Dat tu quay) |
| `moon_events.py` | Gio Mat Trang moc/lan THAT theo toa do + xac dinh khung gio Void-of-Course |
| `macro_calendar.py` | Doc lich tin vi mo: file JSON tinh (NFP/CPI/PPI/FOMC) + quy tac lap lai (Jobless Claims hang tuan) + **tu dong bo sung** cac tin My tam quan trong cao khac (PCE, ISM PMI, Retail Sales...) tu feed cong khai cua ForexFactory |
| `data/macro_calendar.json` | Du lieu tinh: NFP, PPI, CPI, FOMC — **can tu cap nhat hang thang** (xem huong dan trong file) |
| `score_engine.py` | Ghep tat ca thanh chi bao "vach xanh/do" 1-5/ngay + song nang luong that theo gio (Ascendant-Mat Trang + do cao Mat Trang + Void-of-Course) |
| `i18n.py` | Toan bo nhan/nhan song ngu VN-EN (hanh tinh, goc chieu, cung hoang dao, giao dien...) |
| `app.py` | Dashboard Streamlit chinh (bieu do 30 ngay + drill-down theo gio + chon vi tri quan sat) |
| `telegram_notifier.py` | Gui ban tin Telegram hang ngay/hang gio (chay qua GitHub Actions), doc danh sach nguoi dang ky tu Cloudflare KV |
| `cloudflare/telegram_webhook.js` | Cloudflare Worker xu ly lenh `/start`/`/stop` TUC THI (webhook that, khong polling) - xem huong dan deploy trong muc "Thong bao qua Telegram" |

### Do chinh xac da kiem chung (thang 8/2026)
- Nghich hanh Sao Thuy 2026 tu tinh toan: 26/2-19/3, 29/6-22/7, 24/10-12/11 — khop +-1 ngay voi lich thuc da xac minh (26/2-20/3, 29/6-23/7, 24/10-13/11).
- Sao Kim nghich hanh 1 lan trong 2026 (03/10-13/11, ~42 ngay) va Sao Hoa khong nghich hanh lan nao trong 2026 — dung theo chu ky that (Kim ~18 thang/lan, Hoa ~26 thang/lan).
- Pha trang khop voi trang tron/trang non thuc 2026 (xem ghi chu trong `astro.py`).

## Chay local (tren may ban)

```bash
cd astro_dashboard
pip install -r requirements.txt
streamlit run app.py
```

Trinh duyet se tu mo tai `http://localhost:8501`.

## Vi sao khong the chay "luon tai day"?

Cowork chay tren cloud cua Anthropic, tach biet hoan toan voi may ban va
khong mo duoc cong (port) de ban xem giao dien Streamlit truc tiep tu chat.
Muon Claude thao tac/chay lenh ngay tren may ban, can dung **Claude Code**.

**Cach nhanh nhat de co 1 link web dung tu xa, mien phi:**

1. Tai toan bo thu muc `astro_dashboard/` ve may (nut tai file ben duoi).
2. Tao 1 repo moi tren GitHub (github.com/new), upload cac file nay len
   qua giao dien web (khong can cai gi ca).
3. Vao **share.streamlit.io** → "New app" → chon repo vua tao → chon
   `app.py` lam file chinh → Deploy.

Sau vai phut se co link dang `https://<ten-app>.streamlit.app` dung duoc tu
bat ky dau, du lieu thoi gian/pha trang duoc tinh real-time moi lan tai lai
trang (co the bam nut lam moi hoac trang tu lam moi moi 60 giay).

## Cap nhat lich tin vi mo hang thang

Sua truc tiep `data/macro_calendar.json` theo mau co san. Nguon tra cuu:
- NFP/CPI/PPI: bls.gov/schedule/news_release/current_year.asp
- FOMC: federalreserve.gov/newsevents/calendar.htm

## Tin vi mo tu dong bo sung (ForexFactory)

Ngoai file JSON tinh o tren, `macro_calendar.py` con TU DONG tai them cac
tin kinh te My **tam quan trong cao** (tuong duong 3 sao tren
investing.com) tu feed JSON cong khai, mien phi cua ForexFactory
(`nfs.faireconomy.media`) - vi du PCE, ISM PMI, Retail Sales, Housing
Starts... la nhung tin ma file tinh khong theo doi het.

Ly do khong dung truc tiep investing.com: trang do can chay JavaScript
moi hien du lieu that (khong the tu dong doc bang script don gian), va
dieu khoan su dung cua ho khong cho phep tu dong sao chep/luu tru du
lieu. ForexFactory cung cap san 1 file JSON cong khai duoc rat nhieu bot
giao dich su dung, khong bi han che tuong tu.

**Gioi han can biet:**
- Feed nay chi co du lieu "tuan nay" + "tuan sau" (khong co ca thang), nen
  chi bo sung duoc tin trong ~2 tuan toi - xa hon van chi dua vao file
  JSON tinh.
- Neu ForexFactory gap su co (mat mang, doi dinh dang du lieu...), phan
  bo sung nay tu dong bo qua (co log canh bao), KHONG lam hong ung dung -
  danh sach tinh + Jobless Claims van hoat dong binh thuong.
- Sandbox cua Claude (moi truong lam viec cua Cowork) chan duoc ket noi
  toi domain nay nen KHONG the tu kiem tra truc tiep du lieu that - da
  test bang du lieu gia lap (mock) va xac nhan logic loc/gop/cache dung,
  nhung CAN chay thu qua GitHub Actions (moi truong do co mang binh
  thuong) de xac nhan dinh dang du lieu that khop voi code. Neu sau khi
  chay thu ma khong thay tin ForexFactory nao xuat hien, gui lai log cua
  buoc `python telegram_notifier.py daily` de dieu chinh lai cach doc du
  lieu cho dung.

## Deploy len Render + gan domain rieng

Da co san `render.yaml` — vao render.com > New > Blueprint > chon repo nay
la Render tu doc cau hinh va deploy. Sau khi co URL that (`*.onrender.com`
hoac domain rieng), vao Render > Environment > sua bien `APP_BASE_URL`
thanh dung URL do roi deploy lai, de anh thumbnail khi chia se link
(xem muc duoi) hien dung.

## Anh thumbnail khi chia se link (Open Graph)

Streamlit khong ho tro san the `<meta property="og:image">` vi trang chay
dang single-page-app. `scripts/patch_og_tags.py` tu dong chen the nay vao
file `index.html` tinh cua goi Streamlit ngay luc build tren Render (xem
`buildCommand` trong `render.yaml`), dung anh `static/og-image.png`. Muon
doi anh, thay file `static/og-image.png` (nen 1200x630px) roi deploy lai.

## Thong bao qua Telegram

`telegram_notifier.py` tu dong gui 3 loai thong bao vao Telegram qua
**GitHub Actions** (chay doc lap, khong can Render dang thuc hay khong -
Render Cron Job la tinh nang tra phi nen khong dung):

- **Hang ngay (~6h sang, VN)** — `telegram_daily.yml`: chi bao chiem tinh
  hom nay (xanh/do + "que" Dai Cat/Cat/Tieu Cat/Binh/Tieu Hung/Hung/Dai
  Hung), toan bo khung gio song manh du kien trong ngay, tin vi mo NGAY
  MAI (nhac truoc 1 ngay) va tin vi mo HOM NAY (nhac dung ngay).
- **Hang gio** — `telegram_hourly.yml`: bao thoi gian thuc dung luc BAT
  DAU 1 khung gio song manh (khong lap lai trong cung 1 khung).

Ca 2 loai tren duoc **BROADCAST cho MOI NGUOI da dang ky** (khong con gioi
han 1 nguoi duy nhat) - xem phan dang ky nhieu nguoi ben duoi.

### Cach thiet lap bot (1 lan duy nhat)

1. **Tao bot**: nhan tin cho [@BotFather](https://t.me/BotFather) tren
   Telegram, go `/newbot`, dat ten → BotFather tra ve 1 **token** dang
   `123456:ABC-...`.
2. Vao repo GitHub → **Settings** → **Secrets and variables** → **Actions**
   → **New repository secret**, tao secret `TELEGRAM_BOT_TOKEN` = token o
   buoc 1 (secret `TELEGRAM_CHAT_ID` cu, neu co, khong con dung nua - co
   the xoa).
3. Lam theo muc "Cho phep nhieu nguoi dang ky" ben duoi de thiet lap
   Cloudflare Worker - **BAT BUOC** phai xong buoc nay thi `telegram_daily.yml`/
   `telegram_hourly.yml` moi doc duoc danh sach nguoi dang ky (khong con
   file JSON trong repo nua).
4. Muon test ngay khong doi lich, vao tab **Actions** tren GitHub → chon
   "Telegram Daily Digest" hoac "Telegram Hourly Energy Check" → **Run
   workflow**.

### Cho phep nhieu nguoi dang ky (lenh /start, /stop) - phan hoi TUC THI

Lenh `/start`/`/stop` duoc xu ly boi **Cloudflare Worker**
(`cloudflare/telegram_webhook.js`) thay vi GitHub Actions - vi Telegram
GOI THANG toi Worker ngay khi co tin nhan moi (webhook that su), khong
con kieu "cho toi lich chay dinh ky moi 5 phut" nhu truoc (co the tre vai
chuc phut, khong dang tin cay). Cloudflare Workers mien phi, chay 24/7,
khong bi "ngu" nhu Render free tier.

**Thiet lap (1 lan duy nhat, khoang 10 phut):**

1. Tao tai khoan mien phi tai [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up)
   (chi can email, khong can the tin dung).
2. Trong Cloudflare Dashboard → **Workers & Pages** → **Create** → **Create
   Worker** → dat ten (vd `astro-telegram-bot`) → **Deploy** (dung template
   mac dinh truoc, sua sau).
3. Vao Worker vua tao → **Edit code** → xoa het code mau, dan toan bo noi
   dung file `cloudflare/telegram_webhook.js` trong repo vao → **Deploy**.
4. Tao KV namespace de luu danh sach dang ky: **Workers & Pages** →
   **KV** → **Create a namespace** → dat ten (vd `astro-subscribers`) →
   Create.
5. Gan KV vao Worker: vao lai Worker → **Settings** → **Variables and
   Secrets** (hoac **Bindings**) → **Add binding** → chon **KV
   Namespace** → Variable name go dung `SUBSCRIBERS_KV` → chon namespace
   vua tao o buoc 4 → Save.
6. Them secret bot token: van o **Settings** → **Variables and Secrets**
   → **Add variable** → Name: `TELEGRAM_BOT_TOKEN`, Value: token bot cua
   ban, nho tick **Encrypt** → Save and deploy.
7. Lay URL cua Worker (dang `https://astro-telegram-bot.<ten-cua-ban>.workers.dev`)
   hien o dau trang Worker.
8. Bao Telegram goi ve dung URL nay - mo trinh duyet (hoac dung `curl`) vao:
   ```
   https://api.telegram.org/bot<TOKEN>/setWebhook?url=<URL_WORKER_O_BUOC_7>
   ```
   (thay `<TOKEN>` va `<URL_WORKER_O_BUOC_7>` cho dung) - thay xuat hien
   `"ok":true` la thanh cong.
9. Dang ky menu lenh `/` hien goi y tren Telegram (chi can 1 lan, khong
   lien quan Worker): chay tren may (hoac nho ai co Python chay ho):
   ```
   TELEGRAM_BOT_TOKEN=xxx python telegram_notifier.py setcommands
   ```
10. Lay 3 thong tin de GitHub Actions doc lai duoc danh sach dang ky tu
    Cloudflare KV, tao them 3 secret trong GitHub (**Settings** → **Secrets
    and variables** → **Actions**):
    - `CF_ACCOUNT_ID` — Cloudflare Dashboard, sidebar phai trang chu co
      **Account ID**.
    - `CF_KV_NAMESPACE_ID` — vao **Workers & Pages** → **KV** → bam vao
      namespace da tao o buoc 4, ID hien trong URL hoac trang chi tiet.
    - `CF_API_TOKEN` — **My Profile** (goc tren phai) → **API Tokens** →
      **Create Token** → chon template **"Edit Cloudflare Workers"** (co
      quyen doc/ghi KV) → Continue to summary → Create Token → copy gia
      tri (chi hien 1 lan duy nhat).

Xong 10 buoc tren: ai gui link bot (`t.me/<username_bot>`) cho nguoi khac,
ho bam `/start` se duoc dang ky **NGAY LAP TUC** (khong con do tre), va
`telegram_daily.yml`/`telegram_hourly.yml` se tu dong gui cho TOAN BO danh
sach nay moi khi chay.

Muon sua lai loi chao/huy dang ky, sua truc tiep trong
`cloudflare/telegram_webhook.js` (cac hang so `WELCOME_TEXT`,
`GOODBYE_TEXT`...) roi dan lai vao Worker → Deploy - khong lien quan gi
den `git push`/GitHub Actions ca, vi Worker la 1 dich vu doc lap.

### Lenh /check - xem ngay ban tin ma khong can doi

Go `/check` bat ky luc nao se tra loi **NGAY LAP TUC** ban tin chiem tinh
cua hom nay, khong can doi den 6h sang hay dang ky gi ca. Co che: moi lan
`telegram_daily.yml` (~6h sang) hoac `telegram_hourly.yml` (moi gio) chay,
`telegram_notifier.py` deu luu lai ban tin vao Cloudflare KV (key
`latest_digest`); Worker chi doc lai ban da luu san nay, khong tu tinh
toan chiem tinh (viec do can Python) nen dam bao tra loi tuc thi.

Vi da doi `BOT_COMMANDS` trong `telegram_notifier.py` (them `/check`),
can chay lai lenh dang ky menu 1 lan de menu "/" tren Telegram cap nhat:
```
TELEGRAM_BOT_TOKEN=xxx python telegram_notifier.py setcommands
```
