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
| `macro_calendar.py` | Doc lich tin vi mo tu file JSON |
| `data/macro_calendar.json` | Du lieu that: NFP, PPI, CPI, FOMC — **can tu cap nhat hang thang** (xem huong dan trong file) |
| `score_engine.py` | Ghep tat ca thanh chi bao "vach xanh/do" 1-5/ngay + song nang luong that theo gio (Ascendant-Mat Trang + do cao Mat Trang + Void-of-Course) |
| `i18n.py` | Toan bo nhan/nhan song ngu VN-EN (hanh tinh, goc chieu, cung hoang dao, giao dien...) |
| `app.py` | Dashboard Streamlit chinh (bieu do 30 ngay + drill-down theo gio + chon vi tri quan sat) |

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
