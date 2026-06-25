"""
Detects whether a NIP belongs to a company (→ KRS) or JDG (→ CEIDG).
Uses the free public KRS search API — no key required.
If the NIP is found in KRS → "KRS". Otherwise → "CEIDG".
"""
import httpx

KRS_SEARCH = "https://api-krs.ms.gov.pl/api/krs/podmiot/search"


async def detect(nip: str) -> str:
    """Return 'KRS' or 'CEIDG'."""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(KRS_SEARCH, params={"nip": nip, "format": "json"})
            if resp.status_code == 200:
                data = resp.json()
                # API returns a list; any hit means it's a company
                if data and (isinstance(data, list) and len(data) > 0):
                    return "KRS"
                # Some KRS API versions return {"odpis": ...} or {"results": ...}
                if isinstance(data, dict) and (data.get("odpis") or data.get("results")):
                    return "KRS"
    except Exception:
        pass
    return "CEIDG"
