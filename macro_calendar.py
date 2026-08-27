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
event_local_datetime() chuyen no sang GIO MAY TINH dang chay app (dung
zoneinfo, khong hardcode offset) de hien thi dung yeu cau "chi hien thi
gio may tinh".
"""

import datetime
import json
import os
from zoneinfo import ZoneInfo

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "macro_calendar.json")
_ET_ZONE = ZoneInfo("America/New_York")


def _load_raw() -> dict:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def all_events() -> list:
    raw = _load_raw()
    events = raw.get("events", [])
    return sorted(events, key=lambda e: e["date"])


def events_in_range(start: datetime.date, end: datetime.date) -> list:
    out = []
    for e in all_events():
        d = datetime.date.fromisoformat(e["date"])
        if start <= d <= end:
            out.append(e)
    return out


def events_on(d: datetime.date) -> list:
    ds = d.isoformat()
    return [e for e in all_events() if e["date"] == ds]


def next_high_impact(from_date: datetime.date):
    for e in all_events():
        d = datetime.date.fromisoformat(e["date"])
        if d >= from_date and e.get("impact") == "high":
            return e
    return None


def event_local_datetime(event: dict):
    """Chuyen 'time_et' (gio Dong Hoa Ky) cua 1 su kien sang datetime theo
    GIO MAY TINH dang chay app (dung timezone that cua he thong, tu dong
    tinh dung EST/EDT cho tung ngay). Tra ve None neu su kien khong co gio
    cu the (time_et la '-')."""
    t = event.get("time_et")
    if not t or t == "-":
        return None
    d = datetime.date.fromisoformat(event["date"])
    hh, mm = (int(x) for x in t.split(":"))
    ny_dt = datetime.datetime(d.year, d.month, d.day, hh, mm, tzinfo=_ET_ZONE)
    return ny_dt.astimezone()  # khong truyen tz -> Python tu doi ve gio he thong


def last_verified() -> str:
    raw = _load_raw()
    return raw.get("_meta", {}).get("last_verified", "khong ro")
