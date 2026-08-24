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
| `astro.py` | Tinh pha trang that bang cong thuc thien van Meeus (khong can API/internet) + lich sao Thuy nghich hanh, nhat/nguyet thuc 2026 |
| `macro_calendar.py` | Doc lich tin vi mo tu file JSON |
| `data/macro_calendar.json` | Du lieu that: NFP, PPI, CPI, FOMC — **can tu cap nhat hang thang** (xem huong dan trong file) |
| `score_engine.py` | Chuyen tin hieu chiem tinh thanh chi bao "vach xanh/do" 1-5 + song nang luong theo gio |
| `app.py` | Dashboard Streamlit chinh (bieu do 30 ngay + drill-down theo gio) |

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
