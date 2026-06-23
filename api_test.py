import os
import json
import datetime
import re

try:
    import httpx as _httpx
except ImportError:
    _httpx = None

try:
    from dotenv import load_dotenv
    load_dotenv("api/.env")
except ImportError:
    pass

CEIDG_API_KEY = os.getenv("CEIDG_API_KEY")
REGON_API_KEY = os.getenv("REGON_API_KEY")


def fetch_company_name(nip: str) -> str:
    """
    Fetch company name from:
    - Biała Lista MF (wl-api.mf.gov.pl) for PL companies
    - VIES REST API (POST check-vat-number) for EU companies
      Note: some EU countries (e.g. DE) do not expose names via VIES.
    Returns '---' on any failure or unavailable data.
    """
    if _httpx is None:
        return "---"

    nip_clean = nip.strip().upper()
    if nip_clean.startswith("PL"):
        nip_clean = nip_clean[2:]

    eu_match = re.match(r'^([A-Z]{2})(.+)$', nip_clean)

    try:
        if eu_match:
            country, vat_num = eu_match.group(1), eu_match.group(2)
            url = "https://ec.europa.eu/taxation_customs/vies/rest-api/check-vat-number"
            resp = _httpx.post(url, json={"countryCode": country, "vatNumber": vat_num}, timeout=8)
            if resp.status_code == 200:
                name = resp.json().get("name", "").strip()
                return name if name and name != "---" else "---"
        else:
            check_date = datetime.date.today().isoformat()
            url = f"https://wl-api.mf.gov.pl/api/search/nip/{nip_clean}?date={check_date}"
            resp = _httpx.get(url, timeout=8)
            if resp.status_code == 200:
                subject = resp.json().get("result", {}).get("subject", {})
                name = subject.get("name", "").strip()
                return name if name else "---"
    except Exception:
        pass

    return "---"


def fetch_company_data(nip: str, bank_account: str = None) -> dict:
    original_nip = nip.strip().upper()
    working_nip = original_nip
    
    if working_nip.startswith("PL"):
        working_nip = working_nip[2:]
        
    print(f"Pobieranie danych dla NIP: {original_nip} (właściwy: {working_nip})...")
    
    import re
    is_foreign = bool(re.match(r"^[A-Z]{2}", working_nip)) and not working_nip.isdigit()
    
    # Mockowane dane (system opcjonalnie przechodzi na np. VIES dla NIP-ów zagranicznych)
    mocked_data = {
        "nip": original_nip,
        "bank_account": bank_account,
        "legal_status": "AKTYWNA",
        "start_date": (datetime.date.today() - datetime.timedelta(days=3*365 if not is_foreign else 2*365)).isoformat(),
        "vat_status": "CZYNNY",
        "account_on_whitelist": not is_foreign, # Zagraniczne nie są na polskiej białej liście
        "address_changes_last_year": 0,
        "board_changes_last_3_months": False,
        "frequent_legal_form_changes": False
    }
    
    return mocked_data


def evaluate_contractor(data: dict) -> dict:
    score = {
        "1_legal_status": 0,
        "2_experience": 0,
        "3_vat_taxes": 0,
        "4_stability": 0,
        "total": 0,
        "details": []
    }
    
    today = datetime.date.today()

    status = data.get("legal_status", "")
    start_date_str = data.get("start_date", today.isoformat())
    start_date = datetime.date.fromisoformat(start_date_str)
    months_na_rynku = (today.year - start_date.year) * 12 + today.month - start_date.month
    
    if status == "AKTYWNA":
        if months_na_rynku <= 3:
            score["1_legal_status"] = 0
            score["details"].append("Status (0 pkt): Działalność aktywna, ale założona niedawno (podwyższone ryzyko).")
        else:
            score["1_legal_status"] = 10
            score["details"].append("Status (+10 pkt): Działalność aktywna.")
    elif status == "ZAWIESZONA":
        score["1_legal_status"] = -5
        score["details"].append("Status (-5 pkt): Działalność zawieszona.")
    elif status in ["ZAMKNIETA", "UPADLOSC", "LIKWIDACJA"]:
        score["1_legal_status"] = -10
        score["details"].append(f"Status (-10 pkt): Działalność w stanie {status}.")
    else:
        score["details"].append("Status (0 pkt): Brak danych o statusie.")

    czeste_zmiany = data.get("frequent_legal_form_changes", False)
    
    if czeste_zmiany:
        score["2_experience"] = -5
        score["details"].append("Doświadczenie (-5 pkt): Częste zmiany formy prawnej / zamykanie i otwieranie.")
    else:
        years_na_rynku = months_na_rynku / 12.0
        if years_na_rynku > 5:
            score["2_experience"] = 10
            score["details"].append("Doświadczenie (+10 pkt): Firma istnieje powyżej 5 lat.")
        elif years_na_rynku >= 2:
            score["2_experience"] = 5
            score["details"].append("Doświadczenie (+5 pkt): Firma istnieje od 2 do 5 lat.")
        elif years_na_rynku >= 0.5:
            score["2_experience"] = 0
            score["details"].append("Doświadczenie (0 pkt): Firma istnieje od 6 miesięcy do 2 lat.")
        else:
            score["2_experience"] = 0
            score["details"].append("Doświadczenie (0 pkt): Firma istnieje bardzo krótko (poniżej 6 miesięcy).")

    vat_status = data.get("vat_status", "NIEZNANY")
    na_bialej_liscie = data.get("account_on_whitelist", False)
    
    if vat_status == "CZYNNY" and na_bialej_liscie:
        score["3_vat_taxes"] = 10
        score["details"].append("Podatki (+10 pkt): Czynny podatnik VAT, rachunek na Białej Liście.")
    elif vat_status == "ZWOLNIONY":
        score["3_vat_taxes"] = 0
        score["details"].append("Podatki (0 pkt): Podmiot zwolniony z VAT.")
    elif vat_status == "WYKRESLONY" or (vat_status == "CZYNNY" and not na_bialej_liscie and data.get("bank_account")):
        score["3_vat_taxes"] = -10
        score["details"].append("Podatki (-10 pkt): Wykreślony z VAT lub numer konta niezgodny z Białą Listą!")
    else:
        score["details"].append("Podatki (0 pkt): Brak weryfikacji konta / nieokreślony status VAT.")

    zmiany_adresu = data.get("address_changes_last_year", 0)
    wymiana_zarzadu = data.get("board_changes_last_3_months", False)
    
    if wymiana_zarzadu:
        score["4_stability"] = -10
        score["details"].append("Stabilność (-10 pkt): Całkowita wymiana zarządu i adresu w ostatnich 3 msc (WYSOKIE RYZYKO).")
    elif zmiany_adresu > 2:
        score["4_stability"] = -5
        score["details"].append("Stabilność (-5 pkt): Więcej niż 2 zmiany adresu siedziby w ostatnim roku.")
    elif zmiany_adresu == 0 and not wymiana_zarzadu:
        score["4_stability"] = 10
        score["details"].append("Stabilność (+10 pkt): Brak zmian zarządu i adresu w ostatnich yearsch.")
    else:
        score["details"].append("Stabilność (0 pkt): Niewielkie, standardowe zmiany korporacyjne.")

    score["total"] = (
        score["1_legal_status"] + 
        score["2_experience"] + 
        score["3_vat_taxes"] + 
        score["4_stability"]
    )
    
    return score


if __name__ == "__main__":
    TEST_NIP = "5252674798"
    TEST_ACCOUNT = "12 1234 5678 0000 0000 0000 0000"
    
    company_data = fetch_company_data(TEST_NIP, TEST_ACCOUNT)
    
    result = evaluate_contractor(company_data)
    
    print("\n" + "="*50)
    print(f" WYNIK OCENY KONTRAHENTA: {TEST_NIP}")
    print("="*50)
    print(f"Całkowita liczba punktów: {result['total']} / 40")
    print("-" * 50)
    for detail in result["details"]:
        print(" ->", detail)
    
    print("-" * 50)
    if result["total"] >= 20:
        print("REKOMENDACJA: Akceptacja - niska szansa na ryzyko.")
    elif result["total"] >= 0:
        print("REKOMENDACJA: Wymagana dodatkowa weryfikacja.")
    else:
        print("REKOMENDACJA: Odrzucenie - zbyt wysokie ryzyko współpracy!")
    print("="*50)
