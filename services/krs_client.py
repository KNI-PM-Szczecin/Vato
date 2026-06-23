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


async def fetch_krs_data(nip: str, krs_numer: str | None = None) -> dict:
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            if not krs_numer:
                # Step 1: find KRS number by NIP
                search = await client.get(
                    f"{BASE}/podmiot/search",
                    params={"nip": nip, "format": "json"},
                )
                search.raise_for_status()
                items = search.json()

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

        odpis_dane = body.get("odpis", {}).get("dane", {})
        dzial1 = odpis_dane.get("dzial1", {})
        info = dzial1.get("danePodmiotu", {})

        kapital_info = dzial1.get("kapital", {}).get("wysokoscKapitaluZakladowego", {})
        share_capital = kapital_info.get("wartosc")
        if share_capital is not None:
            # KRS zwraca liczby z przecinkiem jako separatorem dziesiętnym (np. "125000,00")
            share_capital = float(str(share_capital).replace(",", "."))

        dzial4 = odpis_dane.get("dzial4", {})
        has_bailiff = False

        if dzial4:
            klucze_egzekucji = ["wpisyOPostepowaniuEgzekucyjnym", "ogloszeniaOPostepowaniuEgzekucyjnym"]
            if any(klucz in dzial4 for klucz in klucze_egzekucji) or any("egzekuc" in str(k).lower() for k in dzial4.keys()):
                has_bailiff = True

        header = body.get("odpis", {}).get("naglowekA", {})
        reg_date = None
        reg_date_str = header.get("dataRejestracjiWKRS", "")
        if reg_date_str:
            try:
                # Format is usually DD.MM.YYYY, but handle ISO format YYYY-MM-DD too just in case
                if "-" in reg_date_str:
                    reg_date = date.fromisoformat(reg_date_str[:10])
                else:
                    from datetime import datetime
                    reg_date = datetime.strptime(reg_date_str, "%d.%m.%Y").date()
            except ValueError:
                pass

        status_raw = info.get("statusPodmiotu", "").upper()
        status = STATUS_MAP.get(status_raw, "AKTYWNA")
        legal_name = info.get("nazwa", "").strip()

        res = {
            "status_prawny": status,
            "data_rozpoczecia": reg_date,
            "share_capital": share_capital,
            "has_bailiff_proceedings": has_bailiff
        }
        if legal_name:
            res["legal_name"] = legal_name
        return res

    except Exception:
        return {}


async def enrich(data: ContractorData) -> ContractorData:
    result = await fetch_krs_data(data.nip)
    return data.model_copy(update=result) if result else data
