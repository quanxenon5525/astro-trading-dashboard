"""
aspects.py
----------
Tinh GOC CHIEU THAT (aspects) giua Mat Troi, Mat Trang va cac hanh tinh
Thuy/Kim/Hoa/Moc/Tho tai 1 thoi diem, dua tren kinh do hoang dao dia tam
THAT (planets.py + astro.py) - thay the hoan toan cho ham
`planetary_aspect_strength` gia lap truoc day (chi bien doi lai pha trang).

Cac loai goc chieu chinh (nguon: quy uoc chiem tinh pho thong):
    0 do   - Hop        (conjunction) - trung tinh, tang cuong nang luong
    60 do  - Luc hop     (sextile)    - thuan
    90 do  - Vuong       (square)     - nghich/cang thang
    120 do - Tam hop      (trine)     - thuan
    180 do - Doi dinh     (opposition)- nghich/cang thang
"""

import datetime
import itertools

import astro
import planets

ASPECTS = [
    {"angle": 0, "kind": "conjunction", "nature": "neutral", "orb": 8},
    {"angle": 60, "kind": "sextile", "nature": "harmonious", "orb": 4},
    {"angle": 90, "kind": "square", "nature": "challenging", "orb": 6},
    {"angle": 120, "kind": "trine", "nature": "harmonious", "orb": 6},
    {"angle": 180, "kind": "opposition", "nature": "challenging", "orb": 8},
]

BODIES = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]


def _longitude(body: str, dt: datetime.datetime) -> float:
    if body == "sun":
        return planets.sun_longitude(dt)
    if body == "moon":
        return astro.moon_longitude(dt)
    return planets.planet_longitude(body, dt)


def _separation(lon1: float, lon2: float) -> float:
    diff = abs(lon1 - lon2) % 360
    return diff if diff <= 180 else 360 - diff


# Alias cong khai - cac module khac (score_engine.py) dung ham nay de tinh
# do lech goc giua Ascendant va Mat Trang trong song nang luong theo gio.
separation = _separation


def compute_aspects(dt: datetime.datetime, bodies=None) -> list:
    """Tra ve danh sach goc chieu THAT dang "trong dung sai" (orb) tai thoi
    diem dt, moi phan tu la dict:
        body1, body2 (ma canonical), kind, nature, orb_diff (do lech so
        voi goc chuan), exactness (0..1, 1 = dung khop tuyet doi).
    """
    bodies = bodies or BODIES
    longitudes = {b: _longitude(b, dt) for b in bodies}
    found = []
    for b1, b2 in itertools.combinations(bodies, 2):
        sep = _separation(longitudes[b1], longitudes[b2])
        best = None
        for asp in ASPECTS:
            diff = abs(sep - asp["angle"])
            if diff <= asp["orb"]:
                exactness = 1 - diff / asp["orb"]
                if best is None or exactness > best["exactness"]:
                    best = {
                        "body1": b1, "body2": b2,
                        "kind": asp["kind"], "nature": asp["nature"],
                        "orb_diff": round(diff, 2),
                        "exactness": round(exactness, 3),
                    }
        if best:
            found.append(best)
    return sorted(found, key=lambda a: -a["exactness"])


def aspect_strength(dt: datetime.datetime) -> float:
    """Diem 'do manh goc chieu' 0..1 tai thoi diem dt = do khop (exactness)
    cua goc chieu manh nhat dang hoat dong. Dung thay cho ham gia lap cu."""
    found = compute_aspects(dt)
    return round(found[0]["exactness"], 3) if found else 0.0
