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
        legal_name = subject.get("name", "").strip()
        krs_number = subject.get("krs", "")
        regon_number = subject.get("regon", "")

        on_whitelist = False
        if bank_account:
            accounts = subject.get("accountNumbers", [])
            normalized = bank_account.replace(" ", "")
            on_whitelist = any(acc.replace(" ", "") == normalized for acc in accounts)

        res = {
            "status_vat": vat_status,
            "rachunek_na_bialej_liscie": on_whitelist,
            "krs_number": krs_number.strip() if krs_number else None,
            "regon_number": regon_number.strip() if regon_number else None
        }
        if legal_name:
            res["legal_name"] = legal_name
        return res

    except Exception:
        return {"vat_status": "UNKNOWN", "account_on_whitelist": False}


async def enrich(data: ContractorData) -> ContractorData:
    result = await fetch_vat_data(data.nip, data.bank_account)
    return data.model_copy(update=result)

