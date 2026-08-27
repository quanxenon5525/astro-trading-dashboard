"""
moon_events.py
--------------
Gio Mat Trang moc/lan THAT theo toa do quan sat (dung kinh do/vi do hoang
dao that cua Mat Trang tu astro.py, quy doi sang do cao chan troi), va xac
dinh khung gio "Void-of-Course" (VoC) - khai niem chiem tinh truyen thong:
khoang thoi gian Mat Trang KHONG con tao them goc chieu chinh nao truoc khi
doi sang cung hoang dao ke tiep, thuong duoc coi la luc khong thuan loi de
bat dau viec quan trong/giao dich lon.
"""

import datetime
import math

import astro
import houses
from aspects import ASPECTS, BODIES as _ALL_BODIES, separation

MOON_OTHER_BODIES = [b for b in _ALL_BODIES if b != "moon"]

# Nguong do cao chan troi dung cho moc/lan cua Mat Trang (do), xap xi trung
# binh cho khuc xa khi quyen + thi sai + ban kinh goc Mat Trang.
_MOON_HORIZON_ALT = 0.125


def _ecliptic_to_equatorial(lon_deg: float, lat_deg: float, eps_deg: float):
    lon, lat, eps = math.radians(lon_deg), math.radians(lat_deg), math.radians(eps_deg)
    sin_dec = math.sin(lat) * math.cos(eps) + math.cos(lat) * math.sin(eps) * math.sin(lon)
    dec = math.asin(sin_dec)
    y = math.sin(lon) * math.cos(eps) - math.tan(lat) * math.sin(eps)
    x = math.cos(lon)
    ra = math.atan2(y, x) % (2 * math.pi)
    return math.degrees(ra), math.degrees(dec)


def moon_equatorial(dt: datetime.datetime):
    lon = astro.moon_longitude(dt)
    lat = astro.moon_latitude(dt)
    eps = houses.obliquity(dt)
    return _ecliptic_to_equatorial(lon, lat, eps)


def moon_altitude(dt: datetime.datetime, lat_deg: float, lon_east_deg: float) -> float:
    ra, dec = moon_equatorial(dt)
    lst = houses.local_sidereal_time(dt, lon_east_deg)
    H = math.radians(lst - ra)
    phi, dec_r = math.radians(lat_deg), math.radians(dec)
    sin_alt = math.sin(phi) * math.sin(dec_r) + math.cos(phi) * math.cos(dec_r) * math.cos(H)
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_alt))))


def moon_rise_set(date: datetime.date, lat_deg: float, lon_east_deg: float):
    """Tim gio Mat Trang moc/lan trong ngay (theo lich LOCAL cua may tinh),
    quet so bo moi 5 phut roi noi suy tuyen tinh - du chinh xac o muc vai
    phut cho muc dich hien thi theo khung gio. Tra ve dict {rise, set} voi
    gia tri la datetime (aware, cung tz he thong) hoac None neu khong
    moc/lan trong ngay do (hiem, gan cuc)."""
    start = datetime.datetime(date.year, date.month, date.day, 0).astimezone()
    step = datetime.timedelta(minutes=5)
    n_steps = int(24 * 60 / 5)

    times, alts = [], []
    t = start
    for _ in range(n_steps + 1):
        times.append(t)
        alts.append(moon_altitude(t, lat_deg, lon_east_deg) - _MOON_HORIZON_ALT)
        t += step

    rise, set_ = None, None
    for i in range(len(alts) - 1):
        if alts[i] < 0 <= alts[i + 1] and rise is None:
            frac = -alts[i] / (alts[i + 1] - alts[i])
            rise = times[i] + (times[i + 1] - times[i]) * frac
        if alts[i] >= 0 > alts[i + 1] and set_ is None:
            frac = alts[i] / (alts[i] - alts[i + 1])
            set_ = times[i] + (times[i + 1] - times[i]) * frac
    return {"rise": rise, "set": set_}


def _next_sign_change(dt: datetime.datetime, step_minutes: int = 20, max_hours: int = 96):
    """Tra ve (thoi_diem_doi_cung, danh_sach_thoi_diem, danh_sach_kinh_do_da_unwrap)."""
    lon0 = astro.moon_longitude(dt)
    boundary = (int(lon0 // 30) + 1) * 30
    steps = int(max_hours * 60 / step_minutes)
    step = datetime.timedelta(minutes=step_minutes)

    times, lons = [dt], [lon0]
    offset = 0.0
    prev_raw = lon0
    t = dt
    for _ in range(steps):
        t = t + step
        raw = astro.moon_longitude(t)
        if raw < prev_raw - 180:
            offset += 360
        unwrapped = raw + offset
        times.append(t)
        lons.append(unwrapped)
        prev_raw = raw
        if unwrapped >= boundary:
            return t, times, lons
    return times[-1], times, lons  # khong tim thay trong pham vi quet (hiem)


def is_void_of_course(dt: datetime.datetime) -> bool:
    """True neu Mat Trang KHONG con tao them goc chieu chinh nao (voi Mat
    Troi/Thuy/Kim/Hoa/Moc/Tho) truoc khi doi sang cung hoang dao ke tiep."""
    sign_change_time, times, _ = _next_sign_change(dt)
    if sign_change_time <= dt:
        return False

    step_minutes = 20
    t = dt
    step = datetime.timedelta(minutes=step_minutes)
    prev_seps = {b: separation(astro.moon_longitude(t), _body_longitude(b, t)) for b in MOON_OTHER_BODIES}
    while t < sign_change_time:
        t2 = min(t + step, sign_change_time)
        cur_seps = {b: separation(astro.moon_longitude(t2), _body_longitude(b, t2)) for b in MOON_OTHER_BODIES}
        for b in MOON_OTHER_BODIES:
            for asp in ASPECTS:
                angle = asp["angle"]
                if (prev_seps[b] - angle) == 0 or (prev_seps[b] - angle) * (cur_seps[b] - angle) < 0:
                    return False  # co cat qua 1 goc chieu chinh -> chua Void
        prev_seps = cur_seps
        t = t2
    return True


def _body_longitude(body: str, dt: datetime.datetime) -> float:
    import aspects as _aspects_mod
    return _aspects_mod._longitude(body, dt)
