import json
from pathlib import Path
from configs import config_manager
from database import db_manager
from helper.logger import logger


def _json_path() -> Path:
    rel = config_manager.get_cache("json_fallback_path", "cache_fallback.json")
    return Path(__file__).parent.parent / rel


def _load_json_store() -> dict:
    p = _json_path()
    if p.exists():
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read JSON fallback cache: {e}")
            return {}
    return {}


def _save_json_store(store: dict):
    p = _json_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def _json_key(country: str, year: int, month: int) -> str:
    return f"{country.upper()}_{year}_{month}"


def _holiday_month(h: dict) -> int:
    """Extract month number from a holiday dict."""
    m = h.get("date_month")
    if m:
        try:
            return int(m)
        except (ValueError, TypeError):
            pass
    try:
        return int(h.get("date", "").split("-")[1])
    except Exception:
        return 0


def _fetch_sqlite(country: str, year: int, month: int) -> list | None:
    """Direct SQLite lookup, None if miss or expired."""
    try:
        return db_manager.fetch(country, year, month)
    except Exception:
        return None


def _fetch_json(country: str, year: int, month: int) -> list | None:
    """JSON fallback lookup."""
    store = _load_json_store()
    return store.get(_json_key(country, year, month))


def get_holidays(country: str, year: int, month: int) -> list | None:
    """
    Cache lookup with smart derivation.

    Priority:
      1. Exact (country, year, month) in SQLite
      2. Exact (country, year, month) in JSON fallback
      3. Derive from all-year (month=0) data by filtering — stores the derived
         result so subsequent lookups are direct hits.
    Returns None only when no cached data exists at all.
    """
    use_sqlite = config_manager.get_cache("use_sqlite", True)

    # --- 1. Direct SQLite hit ---
    if use_sqlite:
        result = _fetch_sqlite(country, year, month)
        if result is not None:
            logger.cache(f"SQLite cache hit: {country} {year}/{month}")
            return result

    # --- 2. Direct JSON fallback hit ---
    result = _fetch_json(country, year, month)
    if result is not None:
        logger.cache(f"JSON cache hit: {country} {year}/{month}")
        return result

    # --- 3. Smart derivation from all-year (month=0) ---
    if month != 0:
        all_year = None
        if use_sqlite:
            all_year = _fetch_sqlite(country, year, 0)
        if all_year is None:
            all_year = _fetch_json(country, year, 0)

        if all_year is not None:
            filtered = [h for h in all_year if _holiday_month(h) == month]
            logger.cache(
                f"Derived from all-year: {country} {year}/{month} "
                f"({len(filtered)} holidays)"
            )
            if filtered:
                _store_internal(country, year, month, filtered)
            return filtered

    return None


def store_holidays(country: str, year: int, month: int, holidays: list):
    """
    Persist holidays to cache. Skips empty results — an empty list almost
    always indicates a failed/rate-limited API call, not a genuinely empty
    month. Genuine empty months are populated via smart derivation.
    """
    if not holidays:
        logger.cache(f"Skipped caching empty result: {country} {year}/{month}")
        return
    _store_internal(country, year, month, holidays)


def _store_internal(country: str, year: int, month: int, holidays: list):
    """Write to both SQLite and JSON (no empty-skip guard — used internally)."""
    use_sqlite = config_manager.get_cache("use_sqlite", True)
    if use_sqlite:
        try:
            db_manager.store(country, year, month, holidays)
            logger.cache(
                f"Stored in SQLite: {country} {year}/{month} "
                f"({len(holidays)} holidays)"
            )
        except Exception as e:
            logger.error(f"SQLite store failed: {e}")

    store = _load_json_store()
    store[_json_key(country, year, month)] = holidays
    _save_json_store(store)


def clear_all():
    db_manager.clear_all()
    p = _json_path()
    if p.exists():
        p.unlink()
    logger.info("All caches cleared.")
