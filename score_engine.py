"""
score_engine.py
----------------
Chuyen tin hieu chiem tinh THAT (astro.py + aspects.py + houses.py +
moon_events.py) + nhan dien ngay co tin vi mo (macro_calendar.py) thanh 1
"chi bao chiem tinh" moi ngay va 1 "song nang luong theo gio":

    - strength  : so vach 1..5 (muc manh/yeu cua tin hieu), tinh tu do lech
                  pha trang + goc chieu hanh tinh THAT (khong con la proxy
                  gia lap nhu truoc).
    - bias      : "up" (xanh, trang dang tron dan) hay "down" (do, trang
                  dang khuyet dan / co hanh tinh nghich hanh).
    - tags      : cac nhan dac biet trong ngay (nghich hanh, nhat/nguyet
                  thuc, goc chieu that noi bat, tin vi mo), dang du lieu CO
                  CAU TRUC de app.py tu dich sang VN/EN.
    - wave gio  : dua tren dieu that thay doi nhanh nhat trong ngay - vong
                  quay Trai Dat (diem Moc/Ascendant xoay ~15 do/gio) ket
                  hop do cao That cua Mat Trang tren chan troi va khung gio
                  Void-of-Course - KHONG con la duong sin trang tri.

QUAN TRONG: day la chi bao MANG TINH THAM KHAO/CHIEM TINH - KHONG dua tren
gia cua bat ky san giao dich nao va KHONG phai loi khuyen dau tu.
"""

import datetime
import math

import aspects
import astro
import houses
import macro_calendar
import moon_events

DEFAULT_LOCATION = houses.DEFAULT_LOCATIONS["hanoi"]

# Cac hanh tinh "ca nhan" ma nghich hanh la su kien dang chu y (hiem, ro
# rang) - Moc/Tho nghich hanh gan nhu 4-5 thang/nam nen KHONG dua vao tag
# de tranh gay nhieu, nhung van duoc tinh vao do manh goc chieu chung.
NOTABLE_RETRO_PLANETS = ["mercury", "venus", "mars"]
TOP_ASPECT_MIN_EXACTNESS = 0.6


def _resolve_location(lat, lon):
    if lat is None or lon is None:
        return DEFAULT_LOCATION["lat"], DEFAULT_LOCATION["lon"]
    return lat, lon


def _group_hour_spans(flags: list) -> list:
    """Gom cac gio lien tuc co flags[h]=True thanh list tuple (start,end) gio
    nguyen (inclusive) - dung chung cho ca 'khung gio song manh' va 'khung
    gio Void-of-Course', va la nen tang de tinh them dinh/xu huong."""
    ranges = []
    start = None
    prev = None
    for h, v in enumerate(flags):
        if v:
            if start is None:
                start = h
            elif prev is not None and h != prev + 1:
                ranges.append((start, prev))
                start = h
            prev = h
        else:
            if start is not None:
                ranges.append((start, prev))
                start = None
    if start is not None:
        ranges.append((start, prev))
    return ranges


def _group_hours(flags: list) -> list:
    """Gom cac gio lien tuc thanh list chuoi 'HH:00-HH:00' - dung cho khung
    gio Void-of-Course (khong can tinh dinh/xu huong nhu khung song manh)."""
    return [f"{s:02d}:00-{e + 1:02d}:00" for s, e in _group_hour_spans(flags)]


def _strong_hour_details(flags: list, wave: list) -> list:
    """Nhu _group_hours nhung cho 'khung gio song manh': vi song nang luong
    dao dong nhieu dinh trong ngay (Ascendant xoay qua nhieu goc chieu voi
    Mat Trang), chi hien thi mon gio khong du de biet khung nao dang MANH
    DAN LEN hay YEU DAN DI - nen moi khung duoc tra ve them GIA TRI DINH
    (peak) va XU HUONG:
      - "rising"    : dinh nam o CUOI khung -> dang manh dan len
      - "falling"   : dinh nam o DAU khung -> dang yeu dan di
      - "peak_mid"  : dinh nam o GIUA khung -> tang roi giam trong khung
      - "flat"      : khung chi co 1 gio
    """
    details = []
    for s, e in _group_hour_spans(flags):
        values = wave[s:e + 1]
        peak = max(values)
        peak_idx = values.index(peak)
        n = len(values)
        if n == 1:
            trend = "flat"
        elif peak_idx == 0:
            trend = "falling"
        elif peak_idx == n - 1:
            trend = "rising"
        else:
            trend = "peak_mid"
        details.append({
            "range": f"{s:02d}:00-{e + 1:02d}:00",
            "start_hour": s,
            "end_hour": e,
            "peak": peak,
            "peak_hour": s + peak_idx,
            "trend": trend,
        })
    return details


def daily_signal(d: datetime.date, lat: float = None, lon: float = None) -> dict:
    lat, lon = _resolve_location(lat, lon)
    # 12h trua theo GIO MAY TINH dang chay app (khong phai UTC) - dat naive
    # datetime roi goi .astimezone() de Python tu gan dung offset he thong.
    noon = datetime.datetime(d.year, d.month, d.day, 12).astimezone()

    mp = astro.moon_phase(noon)
    moon_sign = astro.moon_zodiac_sign(noon)
    asp_strength = aspects.aspect_strength(noon)
    top_aspects = [a for a in aspects.compute_aspects(noon) if a["exactness"] >= TOP_ASPECT_MIN_EXACTNESS][:2]
    retro_planets = [p for p in NOTABLE_RETRO_PLANETS if astro.is_planet_retrograde(p, d)]
    eclipse_kind = astro.eclipse_on(d)
    macro_today = macro_calendar.events_on(d)

    # do "manh" = ket hop do lech pha trang khoi diem trung tinh (0.5) voi
    # do manh goc chieu hanh tinh THAT (aspects.py) - khong con la proxy.
    phase_extremity = abs(mp["illumination"] - 0.5) * 2  # 0..1
    magnitude = 0.5 * phase_extremity + 0.5 * asp_strength

    if eclipse_kind:
        magnitude = max(magnitude, 0.9)  # ngay nhat/nguyet thuc luon duoc coi la manh

    strength = max(1, min(5, round(magnitude * 5) or 1))

    bias = "up" if mp["waxing"] else "down"
    if "mercury" in retro_planets:
        bias = "down"  # quy uoc chiem tinh pho bien: nghich hanh = than trong / tieu cuc

    tags = []
    for p in retro_planets:
        tags.append({"kind": "retrograde", "planet": p})
    if eclipse_kind:
        tags.append({"kind": "eclipse", "eclipse_kind": eclipse_kind})
    for a in top_aspects:
        # LUU Y: khong dung {"kind": "aspect", **a} vi a["kind"] (vd "trine")
        # se ghi de len "aspect" do thu tu key trong dict literal - phai
        # doi ten field cua goc chieu thanh "aspect_kind" de tranh dung do.
        tags.append({
            "kind": "aspect",
            "aspect_kind": a["kind"],
            "body1": a["body1"],
            "body2": a["body2"],
            "nature": a["nature"],
            "exactness": a["exactness"],
            "orb_diff": a["orb_diff"],
        })
    if macro_today:
        high = any(e.get("impact") == "high" for e in macro_today)
        tags.append({
            "kind": "macro-high" if high else "macro",
            "primary_event": macro_today[0],
            "extra_count": len(macro_today) - 1,
        })

    return {
        "date": d.isoformat(),
        "strength": strength,
        "bias": bias,
        "moon_phase_key": mp["phase_key"],
        "moon_emoji": mp["emoji"],
        "illumination": mp["illumination"],
        "moon_sign": moon_sign,
        "aspect_strength": asp_strength,
        "top_aspects": top_aspects,
        "retrograde_planets": retro_planets,
        "tags": tags,
        "macro_events": macro_today,
    }


def range_signals(start: datetime.date, days: int, lat: float = None, lon: float = None) -> list:
    return [daily_signal(start + datetime.timedelta(days=i), lat, lon) for i in range(days)]


def hourly_signal(d: datetime.date, lat: float = None, lon: float = None) -> dict:
    """Song nang luong theo gio THAT, dua tren:
      - Goc chieu giua diem Moc (Ascendant, xoay ~15 do/gio do Trai Dat tu
        quay) va Mat Trang - nguon bien dong nhanh nhat va that nhat trong
        ngay.
      - Do cao That cua Mat Trang tren chan troi tai toa do quan sat (Mat
        Trang o tren chan troi duoc coi la "hoat hoa" hon).
      - Khung gio Void-of-Course lam giam nang luong (Mat Trang khong con
        tao goc chieu nao truoc khi doi cung).
    """
    lat, lon = _resolve_location(lat, lon)

    wave = []
    voc_flags = []
    for h in range(24):
        dt = datetime.datetime(d.year, d.month, d.day, h).astimezone()

        asc = houses.ascendant_longitude(dt, lat, lon)
        moon_lon = astro.moon_longitude(dt)
        sep = aspects.separation(asc, moon_lon)
        dist = min(abs(sep - k) for k in (0, 60, 90, 120, 180))
        asc_moon_strength = max(0.0, 1 - dist / 20.0)

        alt = moon_events.moon_altitude(dt, lat, lon)
        alt_norm = (math.sin(math.radians(alt)) + 1) / 2  # 0..1, >0.5 = tren chan troi

        voc = moon_events.is_void_of_course(dt)
        voc_flags.append(voc)

        value = 0.55 * asc_moon_strength + 0.45 * alt_norm
        if voc:
            value *= 0.5  # Void-of-Course lam "mo di" nang luong trong gio do
        wave.append(round(min(max(value, 0.0), 1.0), 3))

    threshold = sorted(wave, reverse=True)[max(0, len(wave) // 4 - 1)]  # top ~25% gio
    strong_flags = [v >= threshold for v in wave]
    range_labels = _group_hours(strong_flags)
    strong_details = _strong_hour_details(strong_flags, wave)
    voc_range_labels = _group_hours(voc_flags)

    moon_rs = moon_events.moon_rise_set(d, lat, lon)
    macro_today = macro_calendar.events_on(d)

    return {
        "date": d.isoformat(),
        "wave": wave,
        "strong_hour_ranges": range_labels,
        "strong_hour_details": strong_details,
        "voc_hour_ranges": voc_range_labels,
        "moon_rise": moon_rs["rise"],
        "moon_set": moon_rs["set"],
        "macro_events": macro_today,
    }
