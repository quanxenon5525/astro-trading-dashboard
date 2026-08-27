"""
planets.py
----------
Tinh vi tri hanh tinh THAT (khong bia dat, khong can API/internet) bang
phuong phap "Keplerian Elements for Approximate Positions of the Major
Planets" (Standish, JPL/NASA) - phuong phap chuan duoc dung rong rai cho
cac cong cu thien van/chiem tinh do chinh xac thap (sai so vai phut cung
~arc-minutes, thua du cho viec tinh goc chieu voi dung sai/orb vai do).

Cho ket qua: kinh do hoang dao dia tam (geocentric ecliptic longitude) cua
Sao Thuy, Sao Kim, Sao Hoa, Sao Moc, Sao Tho, va kinh do Mat Troi - dung de
tinh goc chieu that (aspects.py) va tu dong phat hien nghich hanh (khong
can go tay ngay thang tung nam).

Nguon tham so quy dao: bang J2000 chuan (hop le tot cho khoang nam
1800-2050), cong bo boi JPL Solar System Dynamics.
"""

import datetime
import math

# a (AU), e, I (deg), L (deg), long.peri (deg), long.node (deg) - va toc do
# bien thien /the ky (Julian century) cho tung tham so.
_ELEMENTS = {
    "mercury": dict(
        a=(0.38709927, 0.00000037), e=(0.20563593, 0.00001906), I=(7.00497902, -0.00594749),
        L=(252.25032350, 149472.67411175), peri=(77.45779628, 0.16047689), node=(48.33076593, -0.12534081),
    ),
    "venus": dict(
        a=(0.72333566, 0.00000390), e=(0.00677672, -0.00004107), I=(3.39467605, -0.00078890),
        L=(181.97909950, 58517.81538729), peri=(131.60246718, 0.00268329), node=(76.67984255, -0.27769418),
    ),
    "earth": dict(
        a=(1.00000261, 0.00000562), e=(0.01671123, -0.00004392), I=(-0.00001531, -0.01294668),
        L=(100.46457166, 35999.37244981), peri=(102.93768193, 0.32327364), node=(0.0, 0.0),
    ),
    "mars": dict(
        a=(1.52371034, 0.00001847), e=(0.09339410, 0.00007882), I=(1.84969142, -0.00813131),
        L=(-4.55343205, 19140.30268499), peri=(-23.94362959, 0.44441088), node=(49.55953891, -0.29257343),
    ),
    "jupiter": dict(
        a=(5.20288700, -0.00011607), e=(0.04838624, -0.00013253), I=(1.30439695, -0.00183714),
        L=(34.39644051, 3034.74612775), peri=(14.72847983, 0.21252668), node=(100.47390909, 0.20469106),
    ),
    "saturn": dict(
        a=(9.53667594, -0.00125060), e=(0.05386179, -0.00050991), I=(2.48599187, 0.00193609),
        L=(49.95424423, 1222.49362201), peri=(92.59887831, -0.41897216), node=(113.66242448, -0.28867794),
    ),
}

PLANET_NAMES = ["mercury", "venus", "mars", "jupiter", "saturn"]


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


def _centuries_since_j2000(dt: datetime.datetime) -> float:
    return (_julian_day(dt) - 2451545.0) / 36525.0


def _norm360(deg: float) -> float:
    return deg % 360.0


def _norm180(deg: float) -> float:
    d = deg % 360.0
    return d - 360.0 if d > 180.0 else d


def _solve_kepler(M_deg: float, e: float) -> float:
    """Giai phuong trinh Kepler M = E - e*sin(E) (Newton-Raphson), tra ve E (do)."""
    e_star = math.degrees(e)
    M = _norm180(M_deg)
    E = M + e_star * math.sin(math.radians(M))
    for _ in range(30):
        dM = M - (E - e_star * math.sin(math.radians(E)))
        dE = dM / (1 - e * math.cos(math.radians(E)))
        E += dE
        if abs(dE) < 1e-7:
            break
    return E


def _heliocentric_ecliptic(planet: str, T: float):
    """Tra ve (x, y, z) nhat tam hoang dao (AU) cho 1 hanh tinh tai thoi diem T
    (so the ky Julian tinh tu J2000)."""
    el = _ELEMENTS[planet]
    a = el["a"][0] + el["a"][1] * T
    e = el["e"][0] + el["e"][1] * T
    I = el["I"][0] + el["I"][1] * T
    L = el["L"][0] + el["L"][1] * T
    peri = el["peri"][0] + el["peri"][1] * T
    node = el["node"][0] + el["node"][1] * T

    omega = peri - node  # argument of perihelion (deg)
    M = _norm180(L - peri)
    E = _solve_kepler(M, e)

    x_p = a * (math.cos(math.radians(E)) - e)
    y_p = a * math.sqrt(max(0.0, 1 - e * e)) * math.sin(math.radians(E))

    om, Om, Ir = math.radians(omega), math.radians(node), math.radians(I)
    cos_om, sin_om = math.cos(om), math.sin(om)
    cos_Om, sin_Om = math.cos(Om), math.sin(Om)
    cos_I, sin_I = math.cos(Ir), math.sin(Ir)

    x = (cos_om * cos_Om - sin_om * sin_Om * cos_I) * x_p + (-sin_om * cos_Om - cos_om * sin_Om * cos_I) * y_p
    y = (cos_om * sin_Om + sin_om * cos_Om * cos_I) * x_p + (-sin_om * sin_Om + cos_om * cos_Om * cos_I) * y_p
    z = (sin_om * sin_I) * x_p + (cos_om * sin_I) * y_p
    return x, y, z


def _geocentric_longitude(planet: str, T: float) -> float:
    xp, yp, zp = _heliocentric_ecliptic(planet, T)
    xe, ye, ze = _heliocentric_ecliptic("earth", T)
    xg, yg = xp - xe, yp - ye
    return _norm360(math.degrees(math.atan2(yg, xg)))


def sun_longitude(dt: datetime.datetime) -> float:
    """Kinh do hoang dao dia tam cua Mat Troi (do), tinh tu vi tri nhat tam
    cua Trai Dat (Mat Troi nhin tu Trai Dat nam o huong doi dien)."""
    T = _centuries_since_j2000(dt)
    xe, ye, ze = _heliocentric_ecliptic("earth", T)
    return _norm360(math.degrees(math.atan2(-ye, -xe)))


def planet_longitude(planet: str, dt: datetime.datetime) -> float:
    """Kinh do hoang dao dia tam (do, 0-360) cua 1 hanh tinh tai thoi diem dt."""
    T = _centuries_since_j2000(dt)
    return _geocentric_longitude(planet, T)


def is_retrograde(planet: str, dt: datetime.datetime) -> bool:
    """Tu dong xac dinh hanh tinh co dang nghich hanh khong, bang cach so
    sanh kinh do dia tam tai dt va dt+1 ngay (sai phan chuyen dong biểu
    kien). Khong can bang ngay thang go san - dung cho MOI nam."""
    lon1 = planet_longitude(planet, dt)
    lon2 = planet_longitude(planet, dt + datetime.timedelta(days=1))
    return _norm180(lon2 - lon1) < 0
