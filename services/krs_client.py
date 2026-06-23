"""
KRS — public REST API, no key required.
https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{krs}?rejestr=P&format=json
We search by NIP via: https://api-krs.ms.gov.pl/api/krs/podmiot/search?nip={nip}
"""
import httpx
from datetime import date
from models.contractor import ContractorData


BASE = "https://api-krs.ms.gov.pl/api/krs"


async def fetch_krs_data(nip: str) -> dict:
    """Returns partial ContractorData fields for a spółka."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Step 1: find KRS number by NIP
            search = await client.get(f"{BASE}/podmiot/search", params={"nip": nip})
            search.raise_for_status()
            items = search.json().get("copy_doc", {}).get("dane", {}).get("sections", {})
            # Try direct NIP search endpoint
            resp = await client.get(
                f"{BASE}/OdpisAktualny/{nip}",
                params={"rejestr": "P", "format": "json"},
            )
            if resp.status_code != 200:
                return {}
            body = resp.json()

        section1 = body.get("copy_doc", {}).get("dane", {}).get("section1", {})
        info = section1.get("subject_data", {})

        reg_date_str = info.get("dataRejestracjiWKRS", "")
        reg_date = None
        if reg_date_str:
            try:
                reg_date = date.fromisoformat(reg_date_str[:10])
            except ValueError:
                pass

        status_raw = info.get("subject_status", "")
        status_map = {
            "": "NIEZNANY",
            "AKTYWNA": "AKTYWNA",
            "W LIKWIDACJI": "LIKWIDACJA",
            "W UPADŁOŚCI": "UPADLOSC",
            "WYKREŚLONA": "ZAMKNIETA",
        }
        status = status_map.get(status_raw.upper(), "AKTYWNA")

        return {"legal_status": status, "start_date": reg_date}

    except Exception:
        return {}


async def enrich(data: ContractorData) -> ContractorData:
    result = await fetch_krs_data(data.nip)
    return data.model_copy(update=result) if result else data
