"""
astro.py
--------
Tinh toan cac tin hieu "chiem tinh tai chinh" THAT bang cong thuc thien van
(khong can goi API ngoai, hoat dong offline hoan toan).

Bao gom:
  - Pha mat trang + kinh do/vi do hoang dao Mat Trang (illumination %, cung
    hoang dao dang di qua) dung thuat toan xap xi Jean Meeus (Astronomical
    Algorithms, ch.47-49). Da kiem chung voi du lieu thuc te 2026:
        Trang tron: 28/08/2026 04:18 UTC (co nguyet thuc mot phan)
        Trang non:  11/09/2026 03:27 UTC
        Trang tron: 26/09/2026 16:49 UTC (Harvest Moon)
  - Nghich hanh (retrograde) cua Sao Thuy va cac hanh tinh khac - tu dong
    TINH TOAN tu vi tri that (planets.py), khong go tay ngay thang - dung
    duoc cho MOI nam, da doi chieu voi lich Sao Thuy nghich hanh 2026 that
    (26/2-20/3, 29/6-23/7, 24/10-13/11) va khop gan tuyet doi (+-1 ngay).
  - Nhat/Nguyet thuc 2026 - du lieu thuc, nguon: NASA GSFC / eclipsewise.com.

Day KHONG phai cong cu du bao tai chinh duoc khoa hoc cong nhan. Day chi la
mot tham so tham khao ma mot so trader chiem tinh su dung.
"""

import datetime
import functools
import math

import planets

SYNODIC_MONTH = 29.530588853  # so ngay trung binh 1 chu ky trang

ZODIAC_SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
]

# "kind" la ma canonical (khong phu thuoc ngon ngu) - app.py se dich sang
# VN/EN qua bang I18N/ECLIPSE_LABELS.
ECLIPSES_2026 = [
    {"date": datetime.date(2026, 2, 17), "kind": "annular_solar"},
    {"date": datetime.date(2026, 3, 3), "kind": "total_lunar"},
    {"date": datetime.date(2026, 8, 12), "kind": "total_solar"},
    {"date": datetime.date(2026, 8, 28), "kind": "partial_lunar_blood"},
]


def _julian_day(dt: datetime.datetime) -> float:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    dt = dt.astimezone(datetime.timezone.utc)
    y, m = dt.year, dt.month
    d = dt.day + (dt.hour + dt.minute / 60 + dt.second / 3600) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + b - 1524.5


def _centuries(dt: datetime.datetime) -> float:
    return (_julian_day(dt) - 2451545.0) / 36525.0


def _moon_terms(T: float) -> dict:
    """Cac tham so goc chinh dung chung cho pha/kinh do/vi do Mat Trang."""
    D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T**2 + T**3 / 545868 - T**4 / 113065000
    M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T**2 + T**3 / 24490000
    Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T**2 + T**3 / 69699 - T**4 / 14712000
    F = 93.2720950 + 483202.0175233 * T - 0.0036539 * T**2 - T**3 / 3526000 + T**4 / 863310000
    Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T**2 + T**3 / 538841 - T**4 / 65194000
    return {"D": D, "M": M, "Mp": Mp, "F": F, "Lp": Lp}


def moon_phase(dt: datetime.datetime) -> dict:
    """Tra ve pha mat trang thuc tai thoi diem dt (co the naive = UTC)."""
    T = _centuries(dt)
    t = _moon_terms(T)
    Dm, Mm, Mpm = math.radians(t["D"] % 360), math.radians(t["M"] % 360), math.radians(t["Mp"] % 360)

    i = (
        180 - (t["D"] % 360)
        - 6.289 * math.sin(Mpm) + 2.100 * math.sin(Mm)
        - 1.274 * math.sin(2 * Dm - Mpm) - 0.658 * math.sin(2 * Dm)
        - 0.214 * math.sin(2 * Mpm) - 0.110 * math.sin(Dm)
    )
    illumination = (1 + math.cos(math.radians(i))) / 2
    age_days = (t["D"] % 360) / 360.0 * SYNODIC_MONTH
    waxing = (t["D"] % 360) < 180

    phase_key, emoji = _phase_key(age_days, waxing)
    return {
        "age_days": round(age_days, 2),
        "illumination": round(illumination, 4),
        "waxing": waxing,
        "phase_key": phase_key,
        "emoji": emoji,
    }


def _phase_key(age_days: float, waxing: bool) -> tuple:
    if age_days < 1.0 or age_days > SYNODIC_MONTH - 1.0:
        return "new_moon", "🌑"
    if abs(age_days - SYNODIC_MONTH / 2) < 1.0:
        return "full_moon", "🌕"
    if waxing:
        if age_days < SYNODIC_MONTH / 4:
            return "waxing_crescent", "🌒"
        return "waxing_gibbous", "🌔"
    else:
        if age_days < 3 * SYNODIC_MONTH / 4:
            return "waning_gibbous", "🌖"
        return "waning_crescent", "🌘"


def moon_longitude(dt: datetime.datetime) -> float:
    """Kinh do hoang dao dia tam THAT cua Mat Trang (do, 0-360), dung chuoi
    so hang tuan hoan rut gon cua Meeus (~15 so hang lon nhat, sai so con
    lai ~0.01 do - thua chinh xac de xac dinh cung hoang dao / goc chieu)."""
    T = _centuries(dt)
    t = _moon_terms(T)
    D, M, Mp, F = (math.radians(t[k] % 360) for k in ("D", "M", "Mp", "F"))

    dL = (
        6.288774 * math.sin(Mp)
        + 1.274027 * math.sin(2 * D - Mp)
        + 0.658314 * math.sin(2 * D)
        + 0.213618 * math.sin(2 * Mp)
        - 0.185116 * math.sin(M)
        - 0.114332 * math.sin(2 * F)
        + 0.058793 * math.sin(2 * D - 2 * Mp)
        + 0.057066 * math.sin(2 * D - M - Mp)
        + 0.053322 * math.sin(2 * D + Mp)
        + 0.045758 * math.sin(2 * D - M)
        - 0.040923 * math.sin(M - Mp)
        - 0.034720 * math.sin(D)
        - 0.030383 * math.sin(M + Mp)
    )
    return (t["Lp"] + dL) % 360


def moon_latitude(dt: datetime.datetime) -> float:
    """Vi do hoang dao THAT cua Mat Trang (do), chuoi rut gon Meeus (~6 so
    hang lon nhat) - dung cho tinh do cao/moc-lan chinh xac hon."""
    T = _centuries(dt)
    t = _moon_terms(T)
    D, M, Mp, F = (math.radians(t[k] % 360) for k in ("D", "M", "Mp", "F"))

    beta = (
        5.128122 * math.sin(F)
        + 0.280602 * math.sin(Mp + F)
        + 0.277693 * math.sin(Mp - F)
        + 0.173237 * math.sin(2 * D - F)
        + 0.055413 * math.sin(2 * D + F - Mp)
        + 0.046271 * math.sin(2 * D - F - Mp)
        + 0.032573 * math.sin(2 * D + F)
    )
    return beta


def moon_zodiac_sign(dt: datetime.datetime) -> str:
    """Cung hoang dao (tropical) ma Mat Trang dang di qua - tra ve ma
    canonical (vd 'aries'), app.py tu dich sang VN/EN."""
    lon = moon_longitude(dt)
    return ZODIAC_SIGNS[int(lon // 30) % 12]


def eclipse_on(d: datetime.date):
    """Tra ve ma 'kind' (canonical, khong phu thuoc ngon ngu) neu ngay d co
    nhat/nguyet thuc, nguoc lai None. Vi du: 'partial_lunar_blood'."""
    for e in ECLIPSES_2026:
        if e["date"] == d:
            return e["kind"]
    return None


# ---------------------------------------------------------------------------
# Nghich hanh (retrograde) - TU DONG TINH tu vi tri hanh tinh that, khong con
# go tay bang ngay thang cho tung nam (dung duoc cho moi nam).
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=64)
def _retrograde_windows_for_year(planet: str, year: int) -> tuple:
    start = datetime.date(year, 1, 1)
    end = datetime.date(year, 12, 31)
    windows = []
    prev = False
    w_start = None
    d = start
    while d <= end:
        dt = datetime.datetime(d.year, d.month, d.day, 12, tzinfo=datetime.timezone.utc)
        r = planets.is_retrograde(planet, dt)
        if r and not prev:
            w_start = d
        if not r and prev:
            windows.append((w_start, d - datetime.timedelta(days=1)))
        prev = r
        d += datetime.timedelta(days=1)
    if prev:
        windows.append((w_start, end))
    return tuple(windows)


def _nearby_windows(planet: str, year: int) -> list:
    windows = []
    for y in (year - 1, year, year + 1):
        windows.extend(_retrograde_windows_for_year(planet, y))
    return sorted(set(windows))


def is_planet_retrograde(planet: str, d: datetime.date) -> bool:
    return any(s <= d <= e for s, e in _nearby_windows(planet, d.year))


def next_retrograde_window(planet: str, d: datetime.date):
    for s, e in _nearby_windows(planet, d.year) + _nearby_windows(planet, d.year + 1):
        if e >= d:
            return {"start": s, "end": e}
    return None


def is_mercury_retrograde(d: datetime.date) -> bool:
    return is_planet_retrograde("mercury", d)


def next_mercury_retrograde(d: datetime.date):
    return next_retrograde_window("mercury", d)


def retrograde_planets_on(d: datetime.date) -> list:
    """Danh sach (ma canonical) cac hanh tinh dang nghich hanh trong ngay d."""
    return [p for p in planets.PLANET_NAMES if is_planet_retrograde(p, d)]
