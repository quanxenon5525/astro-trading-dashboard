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
"""

import datetime
import json
import os
from zoneinfo import ZoneInfo

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "macro_calendar.json")
_ET_ZONE = ZoneInfo("America/New_York")
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


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


def events_in_range(start: datetime.date, end: datetime.date) -> list:
    out = []
    for e in all_events():
        d = datetime.date.fromisoformat(e["date"])
        if start <= d <= end:
            out.append(e)
    out.extend(_recurring_events_in_range(start, end))
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
