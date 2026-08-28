"""
macro_calendar.py
------------------
Doc lich tin vi mo THAT tu data/macro_calendar.json.

CACH CAP NHAT HANG THANG (thu cong, khong can API tra phi):
  1. Mo bls.gov/schedule/news_release/current_year.asp de lay ngay NFP/CPI/PPI.
  2. Mo federalreserve.gov/newsevents/calendar.htm de lay ngay hop FOMC.
  3. Them/sua cac object trong data/macro_calendar.json theo dung format mau.

Module nay khong goi bat ky API tra phi/gioi han nao - du lieu la file JSON
tinh, ban tu duy tri, dam bao ung dung chay duoc 100% offline.

Gio phat hanh (time_et) duoc luu theo gio mien Dong Hoa Ky (America/New_York,
tu dong xu ly EST/EDT) vi day la quy uoc chung cua BLS/Fed. ham
event_local_datetime() chuyen no sang GIO VIET NAM (Asia/Ho_Chi_Minh,
UTC+7 co dinh) - KHONG dung gio he thong cua server nua, vi ung dung da
deploy len Streamlit Cloud/Render (chay o UTC hoac mui gio bat ky) va vi
tri quan sat da co dinh la Ha Noi, nen tin tuc cung phai luon hien thi
theo dung gio Viet Nam du chay o dau.

BO SUNG TU DONG (ForexFactory): ngoai file JSON tinh (chi co NFP/CPI/PPI/
FOMC, phai tu cap nhat hang thang) va quy tac lap lai (Jobless Claims),
module nay con TU DONG tai them cac su kien kinh te My TAM QUAN TRONG CAO
(tuong duong "3 sao" tren investing.com) tu file JSON cong khai, mien phi
cua ForexFactory (nfs.faireconomy.media) - vd PCE, ISM PMI, Retail Sales,
Housing Starts... la nhung tin ma file tinh khong theo doi het.

KHONG dung truc tiep investing.com vi trang do (1) can chay JavaScript
moi hien du lieu that (fetch don gian khong doc duoc) va (2) dieu khoan
su dung noi ro khong cho phep tu dong sao chep/luu tru du lieu cua ho.
Feed ForexFactory la file JSON cong khai, duoc rat nhieu bot giao dich
dung tu lau, KHONG bi han che tuong tu.

LUU Y quan trong: feed ForexFactory chi co du lieu "tuan nay" +
"tuan sau" (khong co ca thang), va MOI chi gioi han toi da 2 request/5
phut (theo huong dan chinh thuc cua ho) - vi vay co 1 cache trong bo nho
(module-level, TTL 30 phut) de tranh goi qua nhieu lan khi app.py tu lam
moi trang lien tuc. Neu fetch loi (mat mang, doi dinh dang...) chi LOG
canh bao, KHONG lam crash ca ung dung - danh sach tinh + quy tac lap lai
van hoat dong binh thuong du thieu phan bo sung nay.
"""

import datetime
import json
import os
import sys
import time
from zoneinfo import ZoneInfo

import requests

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "macro_calendar.json")
_ET_ZONE = ZoneInfo("America/New_York")
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

_FF_BASE_URL = "https://nfs.faireconomy.media"
_FF_CACHE_TTL_SECONDS = 30 * 60  # 30 phut - tranh vuot gioi han 2 request/5 phut cua ForexFactory
_ff_cache: dict = {}  # {"thisweek": {"ts": <epoch>, "raw": [...]}, "nextweek": {...}}


def _load_raw() -> dict:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def all_events() -> list:
    raw = _load_raw()
    events = raw.get("events", [])
    return sorted(events, key=lambda e: e["date"])


def _recurring_events_in_range(start: datetime.date, end: datetime.date) -> list:
    """Cac su kien LAP LAI DINH KY hang tuan - hien tai la Initial Jobless
    Claims (so nguoi nop don xin tro cap that nghiep lan dau), Bo Lao Dong
    My cong bo THU NAM hang tuan luc 8:30 ET gan nhu khong doi. Sinh TU
    DONG cho khoang [start, end] thay vi phai tu tay them tung tuan vao
    file JSON tinh (khong thuc te voi su kien lap lai 52 lan/nam) nhu cac
    su kien hang thang/hang quy khac (NFP/CPI/PPI/FOMC).

    Luu y: vai dip co ngay le lien ke, BLS doi cong bo sang THU TU - truong
    hop hiem nay khong duoc xu ly tu dong o day, neu biet truoc thi them
    ghi chu/sua ngay thu cong."""
    events = []
    d = start
    while d <= end:
        if d.weekday() == 3:  # Thu Hai=0 ... Thu Nam=3
            events.append({
                "date": d.isoformat(),
                "time_et": "08:30",
                "name_vi": "Số người nộp đơn xin trợ cấp thất nghiệp lần đầu (Initial Jobless Claims)",
                "name_en": "Initial Jobless Claims",
                "impact": "medium",
                "source": "U.S. Department of Labor",
            })
        d += datetime.timedelta(days=1)
    return events


def _fetch_forexfactory_feed(name: str) -> list:
    """Tai 1 file JSON tho tu ForexFactory ('thisweek' hoac 'nextweek'),
    co cache 30 phut (module-level) de khong goi qua thuong xuyen. Tra ve
    [] neu loi (mat mang, doi dinh dang, bi chan...) - KHONG raise, vi day
    chi la nguon BO SUNG, khong duoc lam hong ca ung dung neu ForexFactory
    gap su co."""
    cached = _ff_cache.get(name)
    now = time.time()
    if cached and (now - cached["ts"] < _FF_CACHE_TTL_SECONDS):
        return cached["raw"]

    url = f"{_FF_BASE_URL}/ff_calendar_{name}.json"
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        raw = resp.json()
        if not isinstance(raw, list):
            raw = []
        _ff_cache[name] = {"ts": now, "raw": raw}  # chi cap nhat "ts" khi THANH CONG
        return raw
    except Exception as exc:  # noqa: BLE001 - co y bat rong, day la nguon bo sung
        print(f"[macro_calendar] Loi tai ForexFactory feed '{name}': {exc}", file=sys.stderr)
        # KHONG cap nhat "ts" - de lan goi ke tiep thu lai som, khong phai
        # doi du 30 phut moi duoc thu lai sau 1 lan loi.
        return cached["raw"] if cached else []


def _normalize_ff_event(raw: dict):
    """Chuyen 1 dong du lieu tho ForexFactory sang dung format su dung
    trong app. CHI GIU su kien cua My (USD) va tam quan trong CAO ("High"
    - tuong duong 3 sao tren investing.com). Tra ve None neu khong khop
    dieu kien hoac thieu du truong (dinh dang cua ForexFactory co the doi
    khac di theo thoi gian - ham nay thu vai ten truong pho bien, neu vao
    tuong lai ho doi dinh dang thi chi phan bo sung nay ngung hoat dong,
    KHONG anh huong danh sach tinh/quy tac lap lai)."""
    currency = str(raw.get("currency") or raw.get("country") or "").strip().upper()
    impact = str(raw.get("impact") or raw.get("impactTitle") or "").strip().lower()
    if currency != "USD" or "high" not in impact:
        return None

    date_str = raw.get("date")
    if not date_str:
        return None
    try:
        dt = datetime.datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_ET_ZONE)
    except ValueError:
        return None
    et_dt = dt.astimezone(_ET_ZONE)

    title = str(raw.get("title") or raw.get("event") or "Sự kiện kinh tế Mỹ").strip()
    return {
        "date": et_dt.date().isoformat(),
        "time_et": et_dt.strftime("%H:%M"),
        # ForexFactory chi co ten tieng Anh, chua co ban dich VN rieng.
        "name_vi": title,
        "name_en": title,
        "impact": "high",
        "source": "Forex Factory",
    }


def _forexfactory_events_in_range(start: datetime.date, end: datetime.date) -> list:
    events = []
    for feed_name in ("thisweek", "nextweek"):
        for raw in _fetch_forexfactory_feed(feed_name):
            ev = _normalize_ff_event(raw)
            if not ev:
                continue
            d = datetime.date.fromisoformat(ev["date"])
            if start <= d <= end:
                events.append(ev)
    return events


def events_in_range(start: datetime.date, end: datetime.date) -> list:
    out = []
    for e in all_events():
        d = datetime.date.fromisoformat(e["date"])
        if start <= d <= end:
            out.append(e)
    out.extend(_recurring_events_in_range(start, end))

    # Bo sung tu ForexFactory, TRANH TRUNG LAP voi su kien da co (vd NFP da
    # co san trong file JSON tinh voi ten tieng Viet chuan) bang cach so
    # sanh (ngay, gio) - neu da co roi thi bo qua ban ForexFactory.
    existing_keys = {(e["date"], e.get("time_et")) for e in out}
    for e in _forexfactory_events_in_range(start, end):
        key = (e["date"], e.get("time_et"))
        if key not in existing_keys:
            out.append(e)
            existing_keys.add(key)

    return sorted(out, key=lambda e: (e["date"], e.get("time_et") or ""))


def events_on(d: datetime.date) -> list:
    return events_in_range(d, d)


def next_high_impact(from_date: datetime.date):
    for e in all_events():
        d = datetime.date.fromisoformat(e["date"])
        if d >= from_date and e.get("impact") == "high":
            return e
    return None


def event_local_datetime(event: dict):
    """Chuyen 'time_et' (gio Dong Hoa Ky) cua 1 su kien sang datetime theo
    GIO VIET NAM (Asia/Ho_Chi_Minh, UTC+7 co dinh khong DST) - LUON co dinh,
    khong phu thuoc mui gio cua server dang chay app (Streamlit Cloud/Render
    thuong chay o UTC). Tra ve None neu su kien khong co gio cu the (time_et
    la '-')."""
    t = event.get("time_et")
    if not t or t == "-":
        return None
    d = datetime.date.fromisoformat(event["date"])
    hh, mm = (int(x) for x in t.split(":"))
    ny_dt = datetime.datetime(d.year, d.month, d.day, hh, mm, tzinfo=_ET_ZONE)
    return ny_dt.astimezone(VN_TZ)


def last_verified() -> str:
    raw = _load_raw()
    return raw.get("_meta", {}).get("last_verified", "khong ro")
