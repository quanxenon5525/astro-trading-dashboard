"""
i18n.py
-------
Bang du lieu song ngu VN/EN cho toan bo giao dien app.py, tach rieng khoi
logic tinh toan (astro.py / score_engine.py chi tra ve "key" canonical,
khong phu thuoc ngon ngu). Phan tieng Viet dung day du dau theo yeu cau.
"""

MOON_PHASE_LABELS = {
    "vi": {
        "new_moon": "Trăng non (New Moon)",
        "waxing_crescent": "Trăng lưỡi liềm đầu tháng, đang tròn dần",
        "waxing_gibbous": "Trăng khuyết cuối tháng, đang tròn dần",
        "full_moon": "Trăng tròn (Full Moon)",
        "waning_gibbous": "Trăng khuyết đầu tháng, đang khuyết dần",
        "waning_crescent": "Trăng lưỡi liềm cuối tháng, đang khuyết dần",
    },
    "en": {
        "new_moon": "New Moon",
        "waxing_crescent": "Waxing Crescent",
        "waxing_gibbous": "Waxing Gibbous",
        "full_moon": "Full Moon",
        "waning_gibbous": "Waning Gibbous",
        "waning_crescent": "Waning Crescent",
    },
}

PLANET_LABELS = {
    "vi": {
        "sun": "Mặt Trời", "moon": "Mặt Trăng", "mercury": "Sao Thủy",
        "venus": "Sao Kim", "mars": "Sao Hỏa", "jupiter": "Sao Mộc", "saturn": "Sao Thổ",
    },
    "en": {
        "sun": "Sun", "moon": "Moon", "mercury": "Mercury",
        "venus": "Venus", "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn",
    },
}

PLANET_SYMBOLS = {
    "sun": "☉", "moon": "☽", "mercury": "☿", "venus": "♀",
    "mars": "♂", "jupiter": "♃", "saturn": "♄",
}

ASPECT_LABELS = {
    "vi": {
        "conjunction": "Hợp", "sextile": "Lục hợp", "square": "Vuông",
        "trine": "Tam hợp", "opposition": "Đối đỉnh",
    },
    "en": {
        "conjunction": "Conjunction", "sextile": "Sextile", "square": "Square",
        "trine": "Trine", "opposition": "Opposition",
    },
}

ASPECT_SYMBOLS = {
    "conjunction": "☌", "sextile": "⚹", "square": "□", "trine": "△", "opposition": "☍",
}

ZODIAC_LABELS = {
    "vi": {
        "aries": "Bạch Dương", "taurus": "Kim Ngưu", "gemini": "Song Tử", "cancer": "Cự Giải",
        "leo": "Sư Tử", "virgo": "Xử Nữ", "libra": "Thiên Bình", "scorpio": "Bọ Cạp",
        "sagittarius": "Nhân Mã", "capricorn": "Ma Kết", "aquarius": "Bảo Bình", "pisces": "Song Ngư",
    },
    "en": {
        "aries": "Aries", "taurus": "Taurus", "gemini": "Gemini", "cancer": "Cancer",
        "leo": "Leo", "virgo": "Virgo", "libra": "Libra", "scorpio": "Scorpio",
        "sagittarius": "Sagittarius", "capricorn": "Capricorn", "aquarius": "Aquarius", "pisces": "Pisces",
    },
}

ECLIPSE_LABELS = {
    "vi": {
        "annular_solar": "Nhật thực hình khuyên",
        "total_lunar": "Nguyệt thực toàn phần",
        "total_solar": "Nhật thực toàn phần",
        "partial_lunar_blood": "Nguyệt thực một phần (Blood Moon)",
    },
    "en": {
        "annular_solar": "Annular Solar Eclipse",
        "total_lunar": "Total Lunar Eclipse",
        "total_solar": "Total Solar Eclipse",
        "partial_lunar_blood": "Partial Lunar Eclipse (Blood Moon)",
    },
}

I18N = {
    "vi": {
        "app_caption": "Chỉ báo chiêm tinh tài chính + lịch tin vĩ mô thật — không lấy giá sàn giao dịch",
        "refresh_button": "🔄 Làm mới dữ liệu",
        "clock_label": "Giờ hiện tại (theo máy tính của bạn)",
        "explain_title": "📖 Tài chính chiêm tinh (Financial Astrology) là gì?",
        "explain_body": """
**Tài chính chiêm tinh** là trường phái sử dụng vị trí Mặt Trăng, các hành
tinh và góc chiếu giữa chúng (aspect) để suy đoán tâm lý đám đông và biến
động thị trường tài chính — ví dụ: trăng tròn/trăng non thường gắn với điểm
đảo chiều tâm lý, sao Thủy nghịch hành (Mercury retrograde) được một số
trader cho là giai đoạn dễ xảy ra sai sót giao dịch/tín hiệu nhiễu.

⚠️ **Đây KHÔNG phải phương pháp được khoa học hay tài chính học chính thống
công nhận.** Không có bằng chứng thống kê vững chắc cho thấy vị trí hành
tinh ảnh hưởng giá tài sản. Đây chỉ là một lớp dữ liệu tham khảo thêm mà
một bộ phận nhỏ trader/nhà đầu tư quan tâm sử dụng bên cạnh phân tích kỹ
thuật/cơ bản. Các chỉ số trong dashboard này được tính 100% từ công thức
thiên văn thật (không bịa đặt), nhưng *cách diễn giải* thành "tín hiệu
xanh/đỏ" là quy ước chiêm tinh phổ biến, không phải dự báo có cơ sở khoa học.
""",
        "sidebar_status_title": "🔮 Trạng thái hôm nay",
        "illum_label": "Độ sáng trăng",
        "retro_active": "☿ Sao Thủy đang NGHỊCH HÀNH",
        "retro_next": "☿ Nghịch hành tiếp theo: {start} → {end}",
        "eclipse_today": "🌑 Hôm nay: {desc}",
        "sidebar_macro_title": "📅 Lịch tin vĩ mô (30 ngày tới)",
        "sidebar_macro_caption": "Dữ liệu xác minh lần cuối: {date}",
        "sidebar_macro_none": "Không có sự kiện nào trong data/macro_calendar.json cho khoảng này.",
        "chart_title": "📊 Chỉ báo chiêm tinh 30 ngày",
        "chart_caption": "Mỗi vạch = 1 ngày. Chiều cao vạch = độ mạnh tín hiệu (1-5). Xanh = pha trăng đang tròn dần (waxing), Đỏ = đang khuyết dần (waning) hoặc sao Thủy nghịch hành. Vạch đậm/nổi bật = ngày đang được chọn (mặc định là hôm nay). Di chuột vào vạch để xem chi tiết, bấm vào vạch để drill-down theo giờ bên dưới.",
        "chart_yaxis": "Độ mạnh (1-5)",
        "chart_xaxis": "Ngày",
        "hover_strength": "Độ mạnh",
        "hover_no_event": "Không có sự kiện đặc biệt",
        "drilldown_title": "⏱️ Sóng năng lượng theo giờ — {date}",
        "date_input_label": "Hoặc chọn ngày thủ công",
        "hourly_yaxis": "Năng lượng (0-1)",
        "hourly_xaxis": "Giờ",
        "metric_strength_label": "Độ mạnh ngày",
        "metric_bias_label": "Xu hướng pha trăng",
        "metric_moon_label": "Mặt Trăng",
        "bias_up_text": "Tròn dần (Xanh)",
        "bias_down_text": "Khuyết dần (Đỏ)",
        "strong_hours_title": "📈 Khoảng thời gian thị trường sóng mạnh:",
        "strong_hours_none": "Không xác định được khung giờ nổi bật.",
        "tags_title": "Sự kiện / nhãn đặc biệt trong ngày:",
        "macro_today_title": "📅 Tin vĩ mô trong ngày này:",
        "footer_disclaimer": (
            "⚠️ Công cụ tham khảo mang tính chiêm tinh, không phải lời khuyên đầu tư. "
            "Dữ liệu pha trăng / nghịch hành / nhật-nguyệt thực và lịch tin vĩ mô là dữ liệu thật, "
            "nhưng việc diễn giải thành tín hiệu 'mạnh/yếu', 'xanh/đỏ' là quy ước chiêm tinh, không có cơ sở khoa học."
        ),
        "lang_label": "Ngôn ngữ",
        "retrograde_tag": "Nghịch hành",
        "retro_planet_active": "{planet} đang NGHỊCH HÀNH",
        "moon_sign_label": "Cung Mặt Trăng",
        "aspect_tag": "{p1} {aspect} {p2}",
        "moonrise_label": "🌙⬆️ Mặt Trăng mọc",
        "moonset_label": "🌙⬇️ Mặt Trăng lặn",
        "moon_not_rise_set": "Không mọc/lặn trong ngày này",
        "calendar_title": "📅 Chiêm tinh",
        "month_label": "Tháng {m}/{y}",
        "choose_date_label": "Chọn ngày:",
        "today_prefix": "Hôm nay:",
        "prev_month": "◀",
        "next_month": "▶",
        "goto_today": "Hôm nay",
        "wave_positive_label": "Sóng +",
        "wave_negative_label": "Sóng -",
        "wave_today_name": "Sóng Hôm Nay",
        "axis_label": "Trục",
        "voc_title": "🌀 Khung giờ Mặt Trăng Void-of-Course (VoC):",
        "voc_none": "Không có khung giờ Void-of-Course trong ngày này.",
        "voc_hint": "VoC: Mặt Trăng không còn tạo góc chiếu chính nào trước khi đổi cung — chiêm tinh truyền thống coi là giờ nên tránh quyết định lớn.",
        "location_label": "📍 Vị trí quan sát (ảnh hưởng sóng theo giờ)",
        "location_custom": "Tuỳ chỉnh (nhập toạ độ)",
        "location_lat": "Vĩ độ",
        "location_lon": "Kinh độ",
        "trend_rising": "Đang mạnh dần lên",
        "trend_falling": "Đang yếu dần đi",
        "trend_peak_mid": "Tăng rồi giảm trong khung",
        "trend_flat": "Ổn định",
        "peak_label": "Đỉnh",
        "loading_text": "🌙 Đang tải dữ liệu chiêm tinh...",
    },
    "en": {
        "app_caption": "Financial astrology signals + real macro news calendar — no exchange prices used",
        "refresh_button": "🔄 Refresh data",
        "clock_label": "Current time (your computer's clock)",
        "explain_title": "📖 What is Financial Astrology?",
        "explain_body": """
**Financial astrology** is a school of thought that uses the position of the
Moon, planets, and the angles between them (aspects) to speculate about crowd
psychology and financial market movements — for example, full/new moons are
often associated with psychological turning points, and Mercury retrograde is
considered by some traders to be a period prone to trading mistakes and noisy
signals.

⚠️ **This is NOT a method recognized by mainstream science or finance.**
There is no robust statistical evidence that planetary positions affect asset
prices. This is simply an extra reference layer that a small subset of
traders/investors use alongside technical/fundamental analysis. The figures in
this dashboard are computed 100% from real astronomical formulas (nothing is
invented), but the *interpretation* into "green/red signals" is a common
astrological convention, not a scientifically grounded forecast.
""",
        "sidebar_status_title": "🔮 Today's status",
        "illum_label": "Moon illumination",
        "retro_active": "☿ Mercury is currently RETROGRADE",
        "retro_next": "☿ Next retrograde: {start} → {end}",
        "eclipse_today": "🌑 Today: {desc}",
        "sidebar_macro_title": "📅 Macro news calendar (next 30 days)",
        "sidebar_macro_caption": "Data last verified: {date}",
        "sidebar_macro_none": "No events found in data/macro_calendar.json for this range.",
        "chart_title": "📊 30-Day Astro Signal Indicator",
        "chart_caption": "Each bar = 1 day. Bar height = signal strength (1-5). Green = waxing moon, Red = waning moon or Mercury retrograde. The bold/highlighted bar = currently selected day (defaults to today). Hover over a bar for details, click it to drill down into the hourly view below.",
        "chart_yaxis": "Strength (1-5)",
        "chart_xaxis": "Date",
        "hover_strength": "Strength",
        "hover_no_event": "No special event",
        "drilldown_title": "⏱️ Hourly Energy Wave — {date}",
        "date_input_label": "Or pick a date manually",
        "hourly_yaxis": "Energy (0-1)",
        "hourly_xaxis": "Hour",
        "metric_strength_label": "Daily strength",
        "metric_bias_label": "Moon phase trend",
        "metric_moon_label": "Moon",
        "bias_up_text": "Waxing (Green)",
        "bias_down_text": "Waning (Red)",
        "strong_hours_title": "📈 Strong market wave periods:",
        "strong_hours_none": "No standout hours detected.",
        "tags_title": "Special events / tags for this day:",
        "macro_today_title": "📅 Macro news on this day:",
        "footer_disclaimer": (
            "⚠️ Reference tool of an astrological nature, not investment advice. "
            "Moon phase / retrograde / eclipse data and the macro news calendar are real data, "
            "but interpreting them as 'strong/weak' or 'green/red' signals is an astrological "
            "convention with no scientific basis."
        ),
        "lang_label": "Language",
        "retrograde_tag": "Retrograde",
        "retro_planet_active": "{planet} is currently RETROGRADE",
        "moon_sign_label": "Moon Sign",
        "aspect_tag": "{p1} {aspect} {p2}",
        "moonrise_label": "🌙⬆️ Moonrise",
        "moonset_label": "🌙⬇️ Moonset",
        "moon_not_rise_set": "Does not rise/set on this day",
        "calendar_title": "📅 Astrology",
        "month_label": "Month {m}/{y}",
        "choose_date_label": "Choose a date:",
        "today_prefix": "Today:",
        "prev_month": "◀",
        "next_month": "▶",
        "goto_today": "Today",
        "wave_positive_label": "Wave +",
        "wave_negative_label": "Wave -",
        "wave_today_name": "Today's Wave",
        "axis_label": "Axis",
        "voc_title": "🌀 Void-of-Course (VoC) Moon hours:",
        "voc_none": "No Void-of-Course window on this day.",
        "voc_hint": "VoC: the Moon makes no more major aspects before changing sign — traditionally considered a time to avoid big decisions.",
        "location_label": "📍 Observer location (affects the hourly wave)",
        "location_custom": "Custom (enter coordinates)",
        "location_lat": "Latitude",
        "location_lon": "Longitude",
        "trend_rising": "Getting stronger",
        "trend_falling": "Weakening",
        "trend_peak_mid": "Rises then falls in this window",
        "trend_flat": "Steady",
        "peak_label": "Peak",
        "loading_text": "🌙 Loading astrology data...",
    },
}
