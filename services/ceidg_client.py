"""
CEIDG — requires CEIDG_API_KEY in .env.
https://dane.biznes.gov.pl/api/ceidg/v2/firma?nip={nip}
"""
import os
import httpx
from datetime import date
from models.contractor import ContractorData


BASE = "https://dane.biznes.gov.pl/api/ceidg/v2"


async def fetch_ceidg_data(nip: str) -> dict:
    api_key = os.getenv("CEIDG_API_KEY", "")
    if not api_key:
        return {}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{BASE}/firma",
                params={"nip": nip},
                headers={"Authorization": f"Bearer {api_key}"},
            )
            resp.raise_for_status()
            body = resp.json()

        firma = body.get("firma", [{}])[0] if body.get("firma") else {}
        if not firma:
            return {}

        status_raw = firma.get("status", "")
        status_map = {
            "AKTYWNA": "AKTYWNA",
            "ZAWIESZONA": "ZAWIESZONA",
            "WYKREŚLONA": "ZAMKNIETA",
        }
        status = status_map.get(status_raw.upper(), "NIEZNANY")

        reg_date_str = firma.get("start_date_json", "")
        reg_date = None
        if reg_date_str:
            try:
                reg_date = date.fromisoformat(reg_date_str[:10])
            except ValueError:
                pass

        return {"legal_status": status, "start_date": reg_date}

    except Exception:
        return {}


async def enrich(data: ContractorData) -> ContractorData:
    result = await fetch_ceidg_data(data.nip)
    return data.model_copy(update=result) if result else data
