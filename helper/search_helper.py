import os
from urllib.parse import quote_plus


# ---------------------------------------------------------------------------
# Platform definitions
# Each entry: (id, display_name, ico_filename, url_template)
# Use {kw} as the keyword placeholder inside url_template.
# ---------------------------------------------------------------------------
PLATFORMS = [
    {
        "id":       "adobe_stock",
        "name":     "Adobe Stock",
        "ico":      "adobe_stock.ico",
        "url":      "https://stock.adobe.com/search?k={kw}&search_type=usertyped",
    },
    {
        "id":       "shutterstock",
        "name":     "Shutterstock",
        "ico":      "shutterstock.ico",
        "url":      "https://www.shutterstock.com/search/{kw}",
    },
    {
        "id":       "freepik",
        "name":     "Freepik",
        "ico":      "freepik.ico",
        "url":      "https://www.freepik.com/search?query={kw}",
    },
    {
        "id":       "vecteezy",
        "name":     "Vecteezy",
        "ico":      "vecteezy.ico",
        "url":      "https://www.vecteezy.com/search?qterm={kw}&content_type=image",
    },
    {
        "id":       "miricanvas",
        "name":     "MiriCanvas",
        "ico":      "miricanvas.ico",
        "url":      "https://www.miricanvas.com/en/template/all-types?keyword={kw}",
    },
    {
        "id":       "istock",
        "name":     "iStock",
        "ico":      "istock.ico",
        "url":      "https://www.istockphoto.com/search/2/image?phrase={kw}",
    },
    {
        "id":       "depositphotos",
        "name":     "DepositPhotos",
        "ico":      "depositphotos.ico",
        "url":      "https://depositphotos.com/stock-photos/{kw}.html",
    },
    {
        "id":       "dreamstime",
        "name":     "Dreamstime",
        "ico":      "dreamstime.ico",
        "url":      "https://www.dreamstime.com/search.php?srh_field={kw}",
    },
]

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def build_url(platform_id: str, keyword: str) -> str:
    """Return search URL for *platform_id* using *keyword*."""
    kw_encoded = quote_plus(keyword.strip())
    for p in PLATFORMS:
        if p["id"] == platform_id:
            return p["url"].format(kw=kw_encoded)
    raise KeyError(f"Unknown platform id: {platform_id!r}")


def ico_path(platform_id: str) -> str:
    """Return absolute path to the platform ICO file (may or may not exist)."""
    for p in PLATFORMS:
        if p["id"] == platform_id:
            return os.path.join(_ASSETS_DIR, p["ico"])
    raise KeyError(f"Unknown platform id: {platform_id!r}")


def platform_by_id(platform_id: str) -> dict:
    for p in PLATFORMS:
        if p["id"] == platform_id:
            return p
    raise KeyError(f"Unknown platform id: {platform_id!r}")
