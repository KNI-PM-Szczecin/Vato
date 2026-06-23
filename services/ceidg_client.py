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
        reg_date = _parse_date(firma.get("dataRozpoczecia", ""))
        name = firma.get("nazwa") or firma.get("firma") or ""
        
        res = {"status_prawny": status, "data_rozpoczecia": reg_date}
        if name:
            res["legal_name"] = name.strip()
        return res
    except Exception:
        return {}


# ── Portal scraper ────────────────────────────────────────────────────────────

def _hidden(html: str, name: str) -> str:
    m = re.search(rf'id="{re.escape(name)}"[^>]*value="([^"]*)"', html)
    return m.group(1) if m else ""


async def _fetch_via_scraper(nip: str) -> dict:
    try:
        async with httpx.AsyncClient(
            headers=_HEADERS, follow_redirects=True, timeout=20
        ) as client:
            # Step 1 — load the form to get ASP.NET hidden fields
            r = await client.get(PORTAL_URL)
            r.raise_for_status()
            html = r.text

            form_data = {
                "__VIEWSTATE": _hidden(html, "__VIEWSTATE"),
                "__VIEWSTATEGENERATOR": _hidden(html, "__VIEWSTATEGENERATOR"),
                "__EVENTVALIDATION": _hidden(html, "__EVENTVALIDATION"),
                "__EVENTTARGET": "",
                "__EVENTARGUMENT": "",
                "ctl00$ContentPlaceHolder1$txtNIP": nip,
                "ctl00$ContentPlaceHolder1$btnSzukaj": "Szukaj",
            }

            # Step 2 — submit search
            r = await client.post(PORTAL_URL, data=form_data)
            r.raise_for_status()
            return _parse_portal_html(r.text)
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
        result["status_prawny"] = STATUS_MAP.get(raw, "AKTYWNA")

    # Founding date — look for "Data rozpoczęcia" or "Data wpisu"
    date_match = re.search(
        r"(?:Data\s+(?:rozpocz[ęe]cia|wpisu))[^<]*</[^>]+>\s*<[^>]+>\s*(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})",
        html, re.IGNORECASE
    )
    if date_match:
        result["data_rozpoczecia"] = _parse_date(date_match.group(1))

    # Name extraction
    name_match = re.search(r'href="Details\.aspx\?Id=[^"]*"[^>]*>\s*([^<]+)', html, re.IGNORECASE)
    if name_match:
        result["legal_name"] = name_match.group(1).strip()

    # Fallback: if we got any results page (no "Brak wyników"), assume active
    if "Brak wynik" not in html and not result.get("status_prawny"):
        result["status_prawny"] = "ACTIVE"

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
