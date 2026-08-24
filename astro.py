"""
astro.py
--------
Tinh toan cac tin hieu "chiem tinh tai chinh" THAT bang cong thuc thien van
(khong can goi API ngoai, hoat dong offline hoan toan).

Bao gom:
  - Pha mat trang (illumination %, ten pha: Trang non/Trang tron/...) dung
    thuat toan xap xi bac thap cua Jean Meeus (Astronomical Algorithms, ch.47-49).
    Da kiem chung voi du lieu thuc te 2026:
        Trang tron: 28/08/2026 04:18 UTC (co nguyet thuc mot phan)
        Trang non:  11/09/2026 03:27 UTC
        Trang tron: 26/09/2026 16:49 UTC (Harvest Moon)
  - Sao Thuy nghich hanh (Mercury retrograde) - lich thuc 2026, nguon: Old
    Farmer's Almanac / CHANI 2026 key dates.
  - Nhat/Nguyet thuc 2026 - nguon: NASA GSFC / eclipsewise.com.

Day KHONG phai cong cu du bao tai chinh duoc khoa hoc cong nhan. Day chi la
mot tham so tham khao ma mot so trader chiem tinh su dung.
"""

import datetime
import math

SYNODIC_MONTH = 29.530588853  # so ngay trung binh 1 chu ky trang

# ---------------------------------------------------------------------------
# Du lieu thuc 2026 (da xac minh qua tim kiem thang 8/2026)
# ---------------------------------------------------------------------------

MERCURY_RETROGRADE_2026 = [
    {"start": datetime.date(2026, 2, 26), "end": datetime.date(2026, 3, 20)},
    {"start": datetime.date(2026, 6, 29), "end": datetime.date(2026, 7, 23)},
    {"start": datetime.date(2026, 10, 24), "end": datetime.date(2026, 11, 13)},
]

ECLIPSES_2026 = [
    {"date": datetime.date(2026, 2, 17), "type": "Nhat thuc hinh khuyen (Annular Solar)"},
    {"date": datetime.date(2026, 3, 3), "type": "Nguyet thuc toan phan (Total Lunar)"},
    {"date": datetime.date(2026, 8, 12), "type": "Nhat thuc toan phan (Total Solar)"},
    {"date": datetime.date(2026, 8, 28), "type": "Nguyet thuc mot phan (Partial Lunar / Blood Moon)"},
]


def _julian_day(dt: datetime.datetime) -> float:
    dt = dt.astimezone(datetime.timezone.utc)
    y, m = dt.year, dt.month
    d = dt.day + (dt.hour + dt.minute / 60 + dt.second / 3600) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    jd = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5
    return jd


def moon_phase(dt: datetime.datetime) -> dict:
    """Tra ve pha mat trang thuc tai thoi diem dt (co the naive = UTC).

    Dung cong thuc xap xi Meeus (mean elongation D, mean anomaly Mat troi/Mat trang)
    de tinh goc pha va ty le chieu sang - khong can thu vien ephemeris / API.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    jd = _julian_day(dt)
    T = (jd - 2451545.0) / 36525.0

    D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T**2 + T**3 / 545868 - T**4 / 113065000
    M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T**2 + T**3 / 24490000
    Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T**2 + T**3 / 69699 - T**4 / 14712000

    Dm = math.radians(D % 360)
    Mm = math.radians(M % 360)
    Mpm = math.radians(Mp % 360)

    i = (
        180
        - (D % 360)
        - 6.289 * math.sin(Mpm)
        + 2.100 * math.sin(Mm)
        - 1.274 * math.sin(2 * Dm - Mpm)
        - 0.658 * math.sin(2 * Dm)
        - 0.214 * math.sin(2 * Mpm)
        - 0.110 * math.sin(Dm)
    )
    illumination = (1 + math.cos(math.radians(i))) / 2
    age_days = (D % 360) / 360.0 * SYNODIC_MONTH
    waxing = (D % 360) < 180  # elongation < 180 -> trang dang tron dan

    name, emoji = _phase_name(age_days, waxing)

    return {
        "age_days": round(age_days, 2),
        "illumination": round(illumination, 4),
        "waxing": waxing,
        "name": name,
        "emoji": emoji,
    }


def _phase_name(age_days: float, waxing: bool) -> tuple:
    if age_days < 1.0 or age_days > SYNODIC_MONTH - 1.0:
        return "Trang non (New Moon)", "🌑"
    if abs(age_days - SYNODIC_MONTH / 2) < 1.0:
        return "Trang tron (Full Moon)", "🌕"
    if waxing:
        if age_days < SYNODIC_MONTH / 4:
            return "Trang khuyet dau thang (Waxing Crescent)", "🌒"
        return "Trang khuyet cuoi thang (Waxing Gibbous)", "🌔"
    else:
        if age_days < 3 * SYNODIC_MONTH / 4:
            return "Trang khuyet dau thang (Waning Gibbous)", "🌖"
        return "Trang khuyet cuoi thang (Waning Crescent)", "🌘"


def is_mercury_retrograde(d: datetime.date) -> bool:
    return any(p["start"] <= d <= p["end"] for p in MERCURY_RETROGRADE_2026)


def next_mercury_retrograde(d: datetime.date):
    upcoming = [p for p in MERCURY_RETROGRADE_2026 if p["start"] >= d]
    return upcoming[0] if upcoming else None


def eclipse_on(d: datetime.date):
    for e in ECLIPSES_2026:
        if e["date"] == d:
            return e["type"]
    return None


def planetary_aspect_strength(dt: datetime.datetime) -> float:
    """Uoc luong 'do manh goc chieu hanh tinh' trong ngay dua tren pha trang
    (kinh do Mat Trang - Mat Troi). Day la mot chi so tuong trung don gian
    hoa, KHONG phai vi tri hanh tinh day du (can ephemeris day du cho viec do).
    Tra ve gia tri 0..1.
    """
    mp = moon_phase(dt)
    d = mp["age_days"] % SYNODIC_MONTH
    # cang gan goc "vuong" (90/270 do, ~7.4 va ~22.1 ngay) hoac "doi dinh" (0/180)
    # thi coi la goc chieu manh hon (theo quy uoc chiem tinh pho bien)
    angle_deg = (d / SYNODIC_MONTH) * 360
    key_angles = [0, 90, 180, 270, 360]
    dist = min(abs(angle_deg - k) for k in key_angles)
    strength = max(0.0, 1 - dist / 45.0)
    return round(strength, 3)


def hourly_wave(date: datetime.date) -> list:
    """Tao 'song nang luong theo gio' cho 1 ngay - ket hop pha trang thay doi
    trong ngay + goc chieu hanh tinh tuong trung, tra ve 24 gia tri 0..1
    (0h -> 23h, gio UTC).
    """
    wave = []
    for h in range(24):
        dt = datetime.datetime(date.year, date.month, date.day, h, tzinfo=datetime.timezone.utc)
        mp = moon_phase(dt)
        aspect = planetary_aspect_strength(dt)
        # ket hop: pha trang + goc chieu tuong trung + dao dong hinh sin theo gio trong ngay
        diurnal = 0.5 + 0.5 * math.sin(math.radians((h / 24.0) * 360 - 90))
        value = 0.35 * mp["illumination"] + 0.35 * aspect + 0.3 * diurnal
        wave.append(round(min(max(value, 0.0), 1.0), 3))
    return wave
