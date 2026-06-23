"""
KRS — public REST API, no key required.
Step 1: search by NIP to get KRS number.
Step 2: fetch full record by KRS number.
"""
import httpx
from datetime import date
from models.contractor import ContractorData

BASE = "https://api-krs.ms.gov.pl/api/krs"

STATUS_MAP = {
    "AKTYWNA": "ACTIVE",
    "W LIKWIDACJI": "LIQUIDATION",
    "W UPADŁOŚCI": "BANKRUPTCY",
    "WYKREŚLONA": "CLOSED",
}


async def fetch_krs_data(nip: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            # Step 1: find KRS number by NIP
            search = await client.get(
                f"{BASE}/podmiot/search",
                params={"nip": nip, "format": "json"},
            )
            search.raise_for_status()
            items = search.json()

            krs_numer = None
            if isinstance(items, list) and items:
                krs_numer = items[0].get("nrKrs") or items[0].get("krs")
            elif isinstance(items, dict):
                # some API versions wrap in {"odpis": [...]} or {"results": [...]}
                lista = items.get("odpis") or items.get("results") or []
                if lista:
                    krs_numer = lista[0].get("nrKrs") or lista[0].get("krs")

            if not krs_numer:
                return {}

            # Step 2: fetch full record
            resp = await client.get(
                f"{BASE}/OdpisAktualny/{krs_numer}",
                params={"rejestr": "P", "format": "json"},
            )
            if resp.status_code != 200:
                return {}
            body = resp.json()

        dzial1 = (
            body.get("odpis", {})
                .get("dane", {})
                .get("dzial1", {})
        )
        info = dzial1.get("danePodmiotu", {})

        data_rej = None
        data_rej_str = info.get("dataRejestracjiWKRS", "")
        if data_rej_str:
            try:
                data_rej = date.fromisoformat(data_rej_str[:10])
            except ValueError:
                pass

        status_raw = info.get("statusPodmiotu", "").upper()
        status = STATUS_MAP.get(status_raw, "AKTYWNA")

        return {"legal_status": status, "start_date": data_rej}

    except Exception:
        return {}


async def enrich(data: ContractorData) -> ContractorData:
    result = await fetch_krs_data(data.nip)
    return data.model_copy(update=result) if result else data
