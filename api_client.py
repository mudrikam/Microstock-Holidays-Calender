import urllib.request
import urllib.parse
import json
import ssl
import config_manager
from logger import logger


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


def _make_request(url: str) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=20, context=ctx) as response:
        raw_bytes = response.read()
        encoding = response.headers.get_content_charset("utf-8") or "utf-8"
        return raw_bytes.decode(encoding, errors="replace")


class CalendarificError(Exception):
    pass


def fetch_holidays(country: str, year: int, month: int) -> list:
    """Fetch holidays. month=0 means all year (no month filter)."""
    api_key = config_manager.get_api_key()
    if not api_key:
        raise CalendarificError("API key is not configured. Set your key in the Configuration tab.")

    base_url = config_manager.get_base_url()
    params = {
        "api_key": api_key,
        "country": country,
        "year": str(year),
        "type": "national,local,religious,observance"
    }
    if month and month != 0:
        params["month"] = str(month)
    url = f"{base_url}/holidays?{urllib.parse.urlencode(params)}"
    label = "all months" if not month else f"month={month}"
    logger.api(f"Requesting: {base_url}/holidays [country={country}, year={year}, {label}]")

    try:
        raw = _make_request(url)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise CalendarificError(f"HTTP {e.code}: {body[:300]}")
    except urllib.error.URLError as e:
        raise CalendarificError(f"Network error: {e.reason}")
    except Exception as e:
        raise CalendarificError(f"Request failed: {e}")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise CalendarificError(f"Invalid JSON response: {e}")

    meta = data.get("meta", {})
    code = meta.get("code", 0)
    if code != 200:
        msg = meta.get("error_detail", f"API error code {code}")
        raise CalendarificError(f"API returned error {code}: {msg}")

    response_obj = data.get("response", {})
    raw_holidays = response_obj.get("holidays", [])
    holidays = _normalize(raw_holidays)
    logger.success(f"Fetched {len(holidays)} holidays for {country} {year}/{month}")
    return holidays


def _parse_states(raw_states) -> str:
    if not raw_states:
        return "All"
    if isinstance(raw_states, str):
        return raw_states
    if isinstance(raw_states, list):
        if not raw_states:
            return "All"
        abbrevs = [s.get("abbrev") or s.get("name") or "" for s in raw_states if isinstance(s, dict)]
        abbrevs = [a for a in abbrevs if a]
        if abbrevs:
            joined = ", ".join(abbrevs)
            return joined if len(joined) <= 80 else f"{joined[:77]}..."
    return "All"


def _parse_states_full(raw_states) -> list:
    if isinstance(raw_states, str):
        return []
    if isinstance(raw_states, list):
        return [
            {"abbrev": s.get("abbrev", ""), "name": s.get("name", ""), "iso": s.get("iso", "")}
            for s in raw_states if isinstance(s, dict)
        ]
    return []


def _normalize(raw: list) -> list:
    seen = {}
    for item in raw:
        date_obj = item.get("date", {})
        iso_date = date_obj.get("iso", "")
        datetime_info = date_obj.get("datetime", {})

        country_raw = item.get("country", {})
        if isinstance(country_raw, dict):
            country_name = country_raw.get("name", "")
            country_id = country_raw.get("id", "")
        else:
            country_name = str(country_raw)
            country_id = ""

        raw_states = item.get("states", "All")
        states_str = _parse_states(raw_states)
        states_list = _parse_states_full(raw_states)
        is_national = (states_str == "All" or states_str.lower() == "all")

        types = item.get("type", [])
        primary_type = item.get("primary_type", "")

        key = (item.get("name", ""), iso_date)
        if key not in seen:
            seen[key] = {
                "name": item.get("name", ""),
                "description": item.get("description", ""),
                "date": iso_date,
                "date_year": datetime_info.get("year"),
                "date_month": datetime_info.get("month"),
                "date_day": datetime_info.get("day"),
                "type": types,
                "primary_type": primary_type,
                "canonical_url": item.get("canonical_url", ""),
                "urlid": item.get("urlid", ""),
                "locations": item.get("locations", "All"),
                "states": states_str,
                "states_list": states_list,
                "country_name": country_name,
                "country_id": country_id,
                "is_national": is_national,
            }
        else:
            existing = seen[key]
            if is_national and not existing["is_national"]:
                existing["states"] = "All"
                existing["states_list"] = []
                existing["is_national"] = True
                existing["primary_type"] = primary_type
                existing["type"] = types
            elif not is_national and not existing["is_national"]:
                if existing["states"] and existing["states"] != states_str:
                    combined = existing["states"] + ", " + states_str
                    existing["states"] = combined if len(combined) <= 120 else combined[:117] + "..."

    return list(seen.values())


def fetch_countries() -> list:
    api_key = config_manager.get_api_key()
    if not api_key:
        return _builtin_countries()

    base_url = config_manager.get_base_url()
    params = {"api_key": api_key}
    url = f"{base_url}/countries?{urllib.parse.urlencode(params)}"
    logger.api("Fetching countries list")

    try:
        raw = _make_request(url)
        data = json.loads(raw)
        countries = data.get("response", {}).get("countries", [])
        if countries:
            result = [
                {"code": c.get("iso-3166", ""), "name": c.get("country_name", "")}
                for c in countries
                if c.get("iso-3166")
            ]
            result.sort(key=lambda x: x["name"])
            logger.success(f"Loaded {len(result)} countries from API")
            return result
        return _builtin_countries()
    except Exception as e:
        logger.warning(f"Countries API failed ({e}), using built-in list")
        return _builtin_countries()


def _builtin_countries() -> list:
    countries = [
        {"code": "AD", "name": "Andorra"},
        {"code": "AE", "name": "United Arab Emirates"},
        {"code": "AF", "name": "Afghanistan"},
        {"code": "AG", "name": "Antigua and Barbuda"},
        {"code": "AI", "name": "Anguilla"},
        {"code": "AL", "name": "Albania"},
        {"code": "AM", "name": "Armenia"},
        {"code": "AO", "name": "Angola"},
        {"code": "AR", "name": "Argentina"},
        {"code": "AS", "name": "American Samoa"},
        {"code": "AT", "name": "Austria"},
        {"code": "AU", "name": "Australia"},
        {"code": "AW", "name": "Aruba"},
        {"code": "AX", "name": "Aland Islands"},
        {"code": "AZ", "name": "Azerbaijan"},
        {"code": "BA", "name": "Bosnia and Herzegovina"},
        {"code": "BB", "name": "Barbados"},
        {"code": "BD", "name": "Bangladesh"},
        {"code": "BE", "name": "Belgium"},
        {"code": "BF", "name": "Burkina Faso"},
        {"code": "BG", "name": "Bulgaria"},
        {"code": "BH", "name": "Bahrain"},
        {"code": "BI", "name": "Burundi"},
        {"code": "BJ", "name": "Benin"},
        {"code": "BL", "name": "Saint Barthelemy"},
        {"code": "BM", "name": "Bermuda"},
        {"code": "BN", "name": "Brunei"},
        {"code": "BO", "name": "Bolivia"},
        {"code": "BQ", "name": "Caribbean Netherlands"},
        {"code": "BR", "name": "Brazil"},
        {"code": "BS", "name": "Bahamas"},
        {"code": "BT", "name": "Bhutan"},
        {"code": "BW", "name": "Botswana"},
        {"code": "BY", "name": "Belarus"},
        {"code": "BZ", "name": "Belize"},
        {"code": "CA", "name": "Canada"},
        {"code": "CC", "name": "Cocos Islands"},
        {"code": "CD", "name": "DR Congo"},
        {"code": "CF", "name": "Central African Republic"},
        {"code": "CG", "name": "Republic of the Congo"},
        {"code": "CH", "name": "Switzerland"},
        {"code": "CI", "name": "Ivory Coast"},
        {"code": "CK", "name": "Cook Islands"},
        {"code": "CL", "name": "Chile"},
        {"code": "CM", "name": "Cameroon"},
        {"code": "CN", "name": "China"},
        {"code": "CO", "name": "Colombia"},
        {"code": "CR", "name": "Costa Rica"},
        {"code": "CU", "name": "Cuba"},
        {"code": "CV", "name": "Cape Verde"},
        {"code": "CW", "name": "Curacao"},
        {"code": "CX", "name": "Christmas Island"},
        {"code": "CY", "name": "Cyprus"},
        {"code": "CZ", "name": "Czech Republic"},
        {"code": "DE", "name": "Germany"},
        {"code": "DJ", "name": "Djibouti"},
        {"code": "DK", "name": "Denmark"},
        {"code": "DM", "name": "Dominica"},
        {"code": "DO", "name": "Dominican Republic"},
        {"code": "DZ", "name": "Algeria"},
        {"code": "EC", "name": "Ecuador"},
        {"code": "EE", "name": "Estonia"},
        {"code": "EG", "name": "Egypt"},
        {"code": "EH", "name": "Western Sahara"},
        {"code": "ER", "name": "Eritrea"},
        {"code": "ES", "name": "Spain"},
        {"code": "ET", "name": "Ethiopia"},
        {"code": "FI", "name": "Finland"},
        {"code": "FJ", "name": "Fiji"},
        {"code": "FK", "name": "Falkland Islands"},
        {"code": "FM", "name": "Micronesia"},
        {"code": "FO", "name": "Faroe Islands"},
        {"code": "FR", "name": "France"},
        {"code": "GA", "name": "Gabon"},
        {"code": "GB", "name": "United Kingdom"},
        {"code": "GD", "name": "Grenada"},
        {"code": "GE", "name": "Georgia"},
        {"code": "GF", "name": "French Guiana"},
        {"code": "GG", "name": "Guernsey"},
        {"code": "GH", "name": "Ghana"},
        {"code": "GI", "name": "Gibraltar"},
        {"code": "GL", "name": "Greenland"},
        {"code": "GM", "name": "Gambia"},
        {"code": "GN", "name": "Guinea"},
        {"code": "GP", "name": "Guadeloupe"},
        {"code": "GQ", "name": "Equatorial Guinea"},
        {"code": "GR", "name": "Greece"},
        {"code": "GT", "name": "Guatemala"},
        {"code": "GU", "name": "Guam"},
        {"code": "GW", "name": "Guinea-Bissau"},
        {"code": "GY", "name": "Guyana"},
        {"code": "HK", "name": "Hong Kong"},
        {"code": "HN", "name": "Honduras"},
        {"code": "HR", "name": "Croatia"},
        {"code": "HT", "name": "Haiti"},
        {"code": "HU", "name": "Hungary"},
        {"code": "ID", "name": "Indonesia"},
        {"code": "IE", "name": "Ireland"},
        {"code": "IL", "name": "Israel"},
        {"code": "IM", "name": "Isle of Man"},
        {"code": "IN", "name": "India"},
        {"code": "IO", "name": "British Indian Ocean Territory"},
        {"code": "IQ", "name": "Iraq"},
        {"code": "IR", "name": "Iran"},
        {"code": "IS", "name": "Iceland"},
        {"code": "IT", "name": "Italy"},
        {"code": "JE", "name": "Jersey"},
        {"code": "JM", "name": "Jamaica"},
        {"code": "JO", "name": "Jordan"},
        {"code": "JP", "name": "Japan"},
        {"code": "KE", "name": "Kenya"},
        {"code": "KG", "name": "Kyrgyzstan"},
        {"code": "KH", "name": "Cambodia"},
        {"code": "KI", "name": "Kiribati"},
        {"code": "KM", "name": "Comoros"},
        {"code": "KN", "name": "Saint Kitts and Nevis"},
        {"code": "KP", "name": "North Korea"},
        {"code": "KR", "name": "South Korea"},
        {"code": "KW", "name": "Kuwait"},
        {"code": "KY", "name": "Cayman Islands"},
        {"code": "KZ", "name": "Kazakhstan"},
        {"code": "LA", "name": "Laos"},
        {"code": "LB", "name": "Lebanon"},
        {"code": "LC", "name": "Saint Lucia"},
        {"code": "LI", "name": "Liechtenstein"},
        {"code": "LK", "name": "Sri Lanka"},
        {"code": "LR", "name": "Liberia"},
        {"code": "LS", "name": "Lesotho"},
        {"code": "LT", "name": "Lithuania"},
        {"code": "LU", "name": "Luxembourg"},
        {"code": "LV", "name": "Latvia"},
        {"code": "LY", "name": "Libya"},
        {"code": "MA", "name": "Morocco"},
        {"code": "MC", "name": "Monaco"},
        {"code": "MD", "name": "Moldova"},
        {"code": "ME", "name": "Montenegro"},
        {"code": "MF", "name": "Saint Martin"},
        {"code": "MG", "name": "Madagascar"},
        {"code": "MH", "name": "Marshall Islands"},
        {"code": "MK", "name": "North Macedonia"},
        {"code": "ML", "name": "Mali"},
        {"code": "MM", "name": "Myanmar"},
        {"code": "MN", "name": "Mongolia"},
        {"code": "MO", "name": "Macau"},
        {"code": "MP", "name": "Northern Mariana Islands"},
        {"code": "MQ", "name": "Martinique"},
        {"code": "MR", "name": "Mauritania"},
        {"code": "MS", "name": "Montserrat"},
        {"code": "MT", "name": "Malta"},
        {"code": "MU", "name": "Mauritius"},
        {"code": "MV", "name": "Maldives"},
        {"code": "MW", "name": "Malawi"},
        {"code": "MX", "name": "Mexico"},
        {"code": "MY", "name": "Malaysia"},
        {"code": "MZ", "name": "Mozambique"},
        {"code": "NA", "name": "Namibia"},
        {"code": "NC", "name": "New Caledonia"},
        {"code": "NE", "name": "Niger"},
        {"code": "NF", "name": "Norfolk Island"},
        {"code": "NG", "name": "Nigeria"},
        {"code": "NI", "name": "Nicaragua"},
        {"code": "NL", "name": "Netherlands"},
        {"code": "NO", "name": "Norway"},
        {"code": "NP", "name": "Nepal"},
        {"code": "NR", "name": "Nauru"},
        {"code": "NU", "name": "Niue"},
        {"code": "NZ", "name": "New Zealand"},
        {"code": "OM", "name": "Oman"},
        {"code": "PA", "name": "Panama"},
        {"code": "PE", "name": "Peru"},
        {"code": "PF", "name": "French Polynesia"},
        {"code": "PG", "name": "Papua New Guinea"},
        {"code": "PH", "name": "Philippines"},
        {"code": "PK", "name": "Pakistan"},
        {"code": "PL", "name": "Poland"},
        {"code": "PM", "name": "Saint Pierre and Miquelon"},
        {"code": "PN", "name": "Pitcairn"},
        {"code": "PR", "name": "Puerto Rico"},
        {"code": "PS", "name": "Palestine"},
        {"code": "PT", "name": "Portugal"},
        {"code": "PW", "name": "Palau"},
        {"code": "PY", "name": "Paraguay"},
        {"code": "QA", "name": "Qatar"},
        {"code": "RE", "name": "Reunion"},
        {"code": "RO", "name": "Romania"},
        {"code": "RS", "name": "Serbia"},
        {"code": "RU", "name": "Russia"},
        {"code": "RW", "name": "Rwanda"},
        {"code": "SA", "name": "Saudi Arabia"},
        {"code": "SB", "name": "Solomon Islands"},
        {"code": "SC", "name": "Seychelles"},
        {"code": "SD", "name": "Sudan"},
        {"code": "SE", "name": "Sweden"},
        {"code": "SG", "name": "Singapore"},
        {"code": "SH", "name": "Saint Helena"},
        {"code": "SI", "name": "Slovenia"},
        {"code": "SJ", "name": "Svalbard and Jan Mayen"},
        {"code": "SK", "name": "Slovakia"},
        {"code": "SL", "name": "Sierra Leone"},
        {"code": "SM", "name": "San Marino"},
        {"code": "SN", "name": "Senegal"},
        {"code": "SO", "name": "Somalia"},
        {"code": "SR", "name": "Suriname"},
        {"code": "SS", "name": "South Sudan"},
        {"code": "ST", "name": "Sao Tome and Principe"},
        {"code": "SV", "name": "El Salvador"},
        {"code": "SX", "name": "Sint Maarten"},
        {"code": "SY", "name": "Syria"},
        {"code": "SZ", "name": "Eswatini"},
        {"code": "TC", "name": "Turks and Caicos Islands"},
        {"code": "TD", "name": "Chad"},
        {"code": "TG", "name": "Togo"},
        {"code": "TH", "name": "Thailand"},
        {"code": "TJ", "name": "Tajikistan"},
        {"code": "TK", "name": "Tokelau"},
        {"code": "TL", "name": "Timor-Leste"},
        {"code": "TM", "name": "Turkmenistan"},
        {"code": "TN", "name": "Tunisia"},
        {"code": "TO", "name": "Tonga"},
        {"code": "TR", "name": "Turkey"},
        {"code": "TT", "name": "Trinidad and Tobago"},
        {"code": "TV", "name": "Tuvalu"},
        {"code": "TW", "name": "Taiwan"},
        {"code": "TZ", "name": "Tanzania"},
        {"code": "UA", "name": "Ukraine"},
        {"code": "UG", "name": "Uganda"},
        {"code": "US", "name": "United States"},
        {"code": "UY", "name": "Uruguay"},
        {"code": "UZ", "name": "Uzbekistan"},
        {"code": "VA", "name": "Vatican City"},
        {"code": "VC", "name": "Saint Vincent and the Grenadines"},
        {"code": "VE", "name": "Venezuela"},
        {"code": "VG", "name": "British Virgin Islands"},
        {"code": "VI", "name": "US Virgin Islands"},
        {"code": "VN", "name": "Vietnam"},
        {"code": "VU", "name": "Vanuatu"},
        {"code": "WF", "name": "Wallis and Futuna"},
        {"code": "WS", "name": "Samoa"},
        {"code": "XK", "name": "Kosovo"},
        {"code": "YE", "name": "Yemen"},
        {"code": "YT", "name": "Mayotte"},
        {"code": "ZA", "name": "South Africa"},
        {"code": "ZM", "name": "Zambia"},
        {"code": "ZW", "name": "Zimbabwe"},
    ]
    countries.sort(key=lambda x: x["name"])
    return countries
