"""
scripts/patch_og_tags.py
------------------------
Streamlit KHONG ho tro san the <meta property="og:..."> vi trang chay dang
single-page-app (noi dung do Python sinh ra chi den qua WebSocket SAU KHI
JS da tai xong, nen cac bot xem-truoc-link nhu Facebook/Zalo/Messenger/
Slack - von KHONG chay JavaScript - se khong bao gio thay duoc noi dung
do). Cach duy nhat de co anh thumbnail khi chia se link la CHINH SUA truc
tiep file index.html tinh cua chinh goi Streamlit da cai (file nay MOI la
thu duoc gui ve dau tien, truoc khi JS chay).

Script nay chay 1 LAN vao luc BUILD tren Render (xem render.yaml), sau
buoc "pip install -r requirements.txt" va truoc khi server khoi dong -
tu dong tim dung file index.html cua ban Streamlit vua duoc cai, chen
them cac the OG/Twitter card vao <head>, va doi lai <title>.

An toan chay lai nhieu lan (idempotent): neu da patch roi thi bo qua,
tranh chen trung lap khi Render build lai nhieu lan.
"""

import os

try:
    import streamlit
except ImportError:
    raise SystemExit("Khong tim thay streamlit - hay chay script nay SAU buoc pip install.")

INDEX_HTML = os.path.join(os.path.dirname(streamlit.__file__), "static", "index.html")

MARKER = "<!-- astro-og-tags-patched -->"

PAGE_TITLE = "Bảng báo chiêm tinh"
OG_TITLE = "Bảng báo chiêm tinh - Astro Financial Signal Dashboard"
OG_DESCRIPTION = "Chỉ báo chiêm tinh tài chính + lịch tin vĩ mô thật — không lấy giá sàn giao dịch."

# APP_BASE_URL nen duoc set trong Render > Environment (vi du:
# https://astro-trading-dashboard.onrender.com hoac domain rieng cua ban)
# de anh thumbnail co URL TUYET DOI - hau het cac nen tang (Facebook, Zalo,
# Slack...) yeu cau URL tuyet doi cho og:image, URL tuong doi co the khong
# hien duoc anh. Neu chua set, fallback ve duong dan tuong doi (van tot hon
# khong co gi, mot so nen tang van doc duoc).
BASE_URL = os.environ.get("APP_BASE_URL", "").rstrip("/")
OG_IMAGE = f"{BASE_URL}/app/static/og-image.png" if BASE_URL else "/app/static/og-image.png"

OG_TAGS = f"""{MARKER}
    <meta property="og:type" content="website" />
    <meta property="og:title" content="{OG_TITLE}" />
    <meta property="og:description" content="{OG_DESCRIPTION}" />
    <meta property="og:image" content="{OG_IMAGE}" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{OG_TITLE}" />
    <meta name="twitter:description" content="{OG_DESCRIPTION}" />
    <meta name="twitter:image" content="{OG_IMAGE}" />
"""


def main() -> None:
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    if MARKER in html:
        print(f"[patch_og_tags] Da patch tu truoc, bo qua. ({INDEX_HTML})")
        return

    if "<title>Streamlit</title>" in html:
        html = html.replace("<title>Streamlit</title>", f"<title>{PAGE_TITLE}</title>")
    elif "<title>" in html:
        # De phong truong hop title mac dinh khac ban da test
        start = html.index("<title>")
        end = html.index("</title>", start) + len("</title>")
        html = html[:start] + f"<title>{PAGE_TITLE}</title>" + html[end:]

    head_close_idx = html.index("</head>")
    html = html[:head_close_idx] + OG_TAGS + html[head_close_idx:]

    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[patch_og_tags] Da them the OG/Twitter card vao {INDEX_HTML}")
    print(f"[patch_og_tags] og:image = {OG_IMAGE}")
    if not BASE_URL:
        print(
            "[patch_og_tags] CANH BAO: chua set bien moi truong APP_BASE_URL "
            "nen og:image dang la duong dan tuong doi - vao Render > "
            "Environment de them APP_BASE_URL = https://<domain-cua-ban> "
            "roi deploy lai de anh preview hien chinh xac tren moi nen tang."
        )


if __name__ == "__main__":
    main()
