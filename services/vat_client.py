"""
Biała Lista Podatników VAT (KAS) — public API, no key required.
https://wl-api.mf.gov.pl/
"""
import httpx
from datetime import date
from models.contractor import ContractorData


BASE = "https://wl-api.mf.gov.pl/api"


async def fetch_vat_data(nip: str, bank_account: str | None = None) -> dict:
    """
    Returns dict with keys: vat_status, account_on_whitelist.
    On any error returns safe defaults (NIEZNANY / False).
    """
    check_date = date.today().isoformat()
    url = f"{BASE}/search/nip/{nip}?date={check_date}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        subject = data.get("result", {}).get("subject", {})
        vat_status = subject.get("statusVat", "NIEZNANY")

        on_whitelist = False
        if bank_account:
            accounts = subject.get("accountNumbers", [])
            normalized = bank_account.replace(" ", "")
            on_whitelist = any(acc.replace(" ", "") == normalized for acc in accounts)

        return {"vat_status": vat_status, "account_on_whitelist": on_whitelist}

    except Exception:
        return {"vat_status": "NIEZNANY", "account_on_whitelist": False}


async def enrich(data: ContractorData) -> ContractorData:
    result = await fetch_vat_data(data.nip, data.bank_account)
    return data.model_copy(update=result)
