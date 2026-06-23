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
            items = search.json().get("odpis", {}).get("dane", {}).get("dzialy", {})
            # Try direct NIP search endpoint
            resp = await client.get(
                f"{BASE}/OdpisAktualny/{nip}",
                params={"rejestr": "P", "format": "json"},
            )
            if resp.status_code != 200:
                return {}
            body = resp.json()

        dzial1 = body.get("odpis", {}).get("dane", {}).get("dzial1", {})
        info = dzial1.get("danePodmiotu", {})

        data_rej_str = info.get("dataRejestracjiWKRS", "")
        data_rej = None
        if data_rej_str:
            try:
                data_rej = date.fromisoformat(data_rej_str[:10])
            except ValueError:
                pass

        status_raw = info.get("statusPodmiotu", "")
        status_map = {
            "": "NIEZNANY",
            "AKTYWNA": "AKTYWNA",
            "W LIKWIDACJI": "LIKWIDACJA",
            "W UPADŁOŚCI": "UPADLOSC",
            "WYKREŚLONA": "ZAMKNIETA",
        }
        status = status_map.get(status_raw.upper(), "AKTYWNA")

        return {"status_prawny": status, "data_rozpoczecia": data_rej}

    except Exception:
        return {}


async def enrich(data: ContractorData) -> ContractorData:
    result = await fetch_krs_data(data.nip)
    return data.model_copy(update=result) if result else data
