"""
CEIDG client — two strategies:
  1. Official API  (requires CEIDG_API_KEY in .env)
  2. Portal scraper (fallback when no key — works for hackathon)

To switch to the API in the future, just set CEIDG_API_KEY in .env.
"""
import os
import re
import httpx
from datetime import date
from models.contractor import ContractorData

API_BASE = "https://dane.biznes.gov.pl/api/ceidg/v2"
PORTAL_URL = "https://aplikacja.ceidg.gov.pl/CEIDG/CEIDG.Public.UI/Search.aspx"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9",
}

STATUS_MAP = {
    "AKTYWNA": "ACTIVE",
    "AKTYWNY": "ACTIVE",
    "ZAWIESZONA": "SUSPENDED",
    "ZAWIESZONY": "SUSPENDED",
    "WYKREŚLONA": "CLOSED",
    "WYKREŚLONY": "CLOSED",
    "WYKREŚLONA Z REJESTRU": "CLOSED",
}


# ── Official API ──────────────────────────────────────────────────────────────

async def _fetch_via_api(nip: str, api_key: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.get(
                f"{API_BASE}/firma",
                params={"nip": nip},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            body = resp.json()

        firma = (body.get("firma") or [{}])[0]
        if not firma:
            return {}

        status = STATUS_MAP.get(firma.get("status", "").upper(), "NIEZNANY")
        data_rej = _parse_date(firma.get("dataRozpoczecia", ""))
        return {"legal_status": status, "start_date": data_rej}
    except Exception:
        return {}


        return {"status_prawny": status, "data_rozpoczecia": data_rej, "share_capital": 0.0, "has_bailiff_proceedings": None}

    except Exception:
        return {}


def _parse_portal_html(html: str) -> dict:
    """Extract status and founding date from CEIDG search results page."""
    result: dict = {}

    # Status — look for common labels in the results table
    status_match = re.search(
        r"Status[^<]*</[^>]+>\s*<[^>]+>\s*([A-ZŁĆĘÓŚŹŻĄ ]+)",
        html, re.IGNORECASE
    )
    if status_match:
        raw = status_match.group(1).strip().upper()
        result["legal_status"] = STATUS_MAP.get(raw, "AKTYWNA")

    # Founding date — look for "Data rozpoczęcia" or "Data wpisu"
    date_match = re.search(
        r"(?:Data\s+(?:rozpocz[ęe]cia|wpisu))[^<]*</[^>]+>\s*<[^>]+>\s*(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})",
        html, re.IGNORECASE
    )
    if date_match:
        result["start_date"] = _parse_date(date_match.group(1))

    # Fallback: if we got any results page (no "Brak wyników"), assume active
    if "Brak wynik" not in html and not result.get("legal_status"):
        result["legal_status"] = "ACTIVE"

    return result


# ── Shared helpers ────────────────────────────────────────────────────────────

def _parse_date(s: str) -> date | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return date.fromisoformat(s[:10]) if "-" in s else date.strptime(s, fmt)
        except ValueError:
            continue
    return None


# ── Public interface ──────────────────────────────────────────────────────────

async def fetch_ceidg_data(nip: str) -> dict:
    api_key = os.getenv("CEIDG_API_KEY", "")
    if api_key:
        result = await _fetch_via_api(nip, api_key)
        if result:
            return result
    # Fallback to scraper (no key needed)
    return await _fetch_via_scraper(nip)


async def enrich(data: ContractorData) -> ContractorData:
    result = await fetch_ceidg_data(data.nip)
    return data.model_copy(update=result) if result else data
