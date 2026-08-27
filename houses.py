"""
houses.py
---------
Tinh gio sao dia phuong (Local Sidereal Time) va diem Moc (Ascendant) theo
toa do quan sat THAT - day la nguon bien dong nhanh nhat va "that" nhat
trong ngay (Trai Dat tu quay ~15 do/gio => Ascendant quay du 360 do moi
ngay), dung de tao "song nang luong theo gio" co y nghia thien van thuc su
thay vi duong sin trang tri nhu truoc.

Cong thuc chuan (Meeus / cac tai lieu chiem tinh ky thuat pho bien).
"""

import datetime
import math

import astro  # de dung _julian_day / _centuries dung chung


def _jd(dt: datetime.datetime) -> float:
    return astro._julian_day(dt)


def _T(dt: datetime.datetime) -> float:
    return (_jd(dt) - 2451545.0) / 36525.0


def obliquity(dt: datetime.datetime) -> float:
    """Do nghieng hoang dao (do), xap xi bac thap - du chinh xac cho tinh
    Ascendant (sai so co the bo qua trong pham vi vai the ky quanh J2000)."""
    T = _T(dt)
    return 23.43929111 - 0.0130042 * T


def greenwich_sidereal_time(dt: datetime.datetime) -> float:
    """Gio sao trung binh tai Greenwich (GMST), tra ve do (0-360)."""
    jd = _jd(dt)
    T = _T(dt)
    gmst = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T**2 - T**3 / 38710000
    return gmst % 360


def local_sidereal_time(dt: datetime.datetime, longitude_east_deg: float) -> float:
    """Gio sao dia phuong (do), longitude_east_deg duong = Dong, am = Tay."""
    return (greenwich_sidereal_time(dt) + longitude_east_deg) % 360


def ascendant_longitude(dt: datetime.datetime, lat_deg: float, lon_east_deg: float) -> float:
    """Kinh do hoang dao THAT cua diem Moc (Ascendant) tai toa do quan sat,
    tai thoi diem dt - day la diem hoang dao dang moc len o chan troi Dong,
    thay doi lien tuc theo vong quay Trai Dat (~1 do/4 phut)."""
    ramc = math.radians(local_sidereal_time(dt, lon_east_deg))
    eps = math.radians(obliquity(dt))
    phi = math.radians(lat_deg)

    y = math.cos(ramc)
    x = -(math.sin(ramc) * math.cos(eps) + math.tan(phi) * math.sin(eps))
    asc = math.degrees(math.atan2(y, x))
    return asc % 360


# Vai vi tri quan sat mac dinh (thanh pho lon VN) de nguoi dung chon nhanh
# trong app.py, khong bat buoc phai tu nhap toa do.
DEFAULT_LOCATIONS = {
    "hanoi": {"label_vi": "Hà Nội", "label_en": "Hanoi", "lat": 21.0285, "lon": 105.8542},
    "hcmc": {"label_vi": "TP. Hồ Chí Minh", "label_en": "Ho Chi Minh City", "lat": 10.8231, "lon": 106.6297},
    "danang": {"label_vi": "Đà Nẵng", "label_en": "Da Nang", "lat": 16.0544, "lon": 108.2022},
    "cantho": {"label_vi": "Cần Thơ", "label_en": "Can Tho", "lat": 10.0452, "lon": 105.7469},
}
