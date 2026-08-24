"""
score_engine.py
----------------
Chuyen tin hieu chiem tinh (astro.py) + nhan dien ngay co tin vi mo
(macro_calendar.py) thanh 1 "chi bao chiem tinh" moi ngay:

    - strength  : so vach 1..5 (muc manh/yeu cua tin hieu)
    - bias      : "up" (xanh) hay "down" (do)
    - tags      : cac nhan dac biet trong ngay (sao Thuy nghich hanh, nhat/
                  nguyet thuc, co tin vi mo quan trong)

QUAN TRONG: day la chi bao MANG TINH THAM KHAO/CHIEM TINH, duoc suy ra tu
pha Mat Trang va goc chieu hanh tinh tuong trung - KHONG dua tren gia cua
bat ky san giao dich nao va KHONG phai loi khuyen dau tu.
"""

import datetime

import astro
import macro_calendar


def daily_signal(d: datetime.date) -> dict:
    noon = datetime.datetime(d.year, d.month, d.day, 12, tzinfo=datetime.timezone.utc)

    mp = astro.moon_phase(noon)
    aspect = astro.planetary_aspect_strength(noon)
    retro = astro.is_mercury_retrograde(d)
    eclipse = astro.eclipse_on(d)
    macro_today = macro_calendar.events_on(d)

    # do "manh" = ket hop do lech pha trang khoi diem trung tinh (0.5)
    # voi do manh goc chieu hanh tinh tuong trung
    phase_extremity = abs(mp["illumination"] - 0.5) * 2  # 0..1
    magnitude = 0.55 * phase_extremity + 0.45 * aspect

    if eclipse:
        magnitude = max(magnitude, 0.9)  # ngay nhat/nguyet thuc luon duoc coi la manh

    strength = max(1, min(5, round(magnitude * 5) or 1))

    bias = "up" if mp["waxing"] else "down"
    if retro:
        bias = "down"  # quy uoc chiem tinh pho bien: nghich hanh = than trong / tieu cuc

    tags = []
    if retro:
        tags.append({"label": "☿ Nghich hanh", "kind": "retrograde"})
    if eclipse:
        tags.append({"label": f"🌑 {eclipse}", "kind": "eclipse"})
    if macro_today:
        high = any(e.get("impact") == "high" for e in macro_today)
        tags.append({
            "label": f"📅 {macro_today[0]['name']}" + (f" +{len(macro_today)-1}" if len(macro_today) > 1 else ""),
            "kind": "macro-high" if high else "macro",
        })

    return {
        "date": d.isoformat(),
        "strength": strength,
        "bias": bias,
        "moon_name": mp["name"],
        "moon_emoji": mp["emoji"],
        "illumination": mp["illumination"],
        "aspect_strength": aspect,
        "tags": tags,
        "macro_events": macro_today,
    }


def range_signals(start: datetime.date, days: int) -> list:
    return [daily_signal(start + datetime.timedelta(days=i)) for i in range(days)]


def hourly_signal(d: datetime.date) -> dict:
    """Song nang luong theo gio cho 1 ngay + xac dinh 'khung gio song manh'."""
    wave = astro.hourly_wave(d)
    threshold = sorted(wave, reverse=True)[max(0, len(wave) // 4 - 1)]  # top ~25% gio
    strong_hours = [h for h, v in enumerate(wave) if v >= threshold]

    # gom thanh cac khoang gio lien tuc de hien thi dep hon: "08:00-11:00"
    ranges = []
    start = None
    prev = None
    for h in strong_hours:
        if start is None:
            start = h
        elif prev is not None and h != prev + 1:
            ranges.append((start, prev))
            start = h
        prev = h
    if start is not None:
        ranges.append((start, prev))

    range_labels = [f"{s:02d}:00-{e+1:02d}:00 UTC" for s, e in ranges]

    macro_today = macro_calendar.events_on(d)

    return {
        "date": d.isoformat(),
        "wave": wave,
        "strong_hour_ranges": range_labels,
        "macro_events": macro_today,
    }
