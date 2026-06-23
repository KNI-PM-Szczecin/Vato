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

        data_rej_str = firma.get("dataRozpoczecia", "")
        data_rej = None
        if data_rej_str:
            try:
                data_rej = date.fromisoformat(data_rej_str[:10])
            except ValueError:
                pass

        return {"status_prawny": status, "data_rozpoczecia": data_rej}

    except Exception:
        return {}


async def enrich(data: ContractorData) -> ContractorData:
    result = await fetch_ceidg_data(data.nip)
    return data.model_copy(update=result) if result else data
