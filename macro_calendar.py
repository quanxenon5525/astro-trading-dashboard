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
"""

import datetime
import json
import os

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "macro_calendar.json")


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


def last_verified() -> str:
    raw = _load_raw()
    return raw.get("_meta", {}).get("last_verified", "khong ro")
