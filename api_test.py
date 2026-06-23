import os
import json
import datetime

try:
    from dotenv import load_dotenv
    load_dotenv("api/.env")
except ImportError:
    pass

CEIDG_API_KEY = os.getenv("CEIDG_API_KEY")
REGON_API_KEY = os.getenv("REGON_API_KEY")


def fetch_company_data(nip: str, bank_account: str = None) -> dict:
    print(f"Pobieranie danych dla NIP: {nip}...")
    
    mocked_data = {
        "nip": nip,
        "bank_account": bank_account,
        "legal_status": "AKTYWNA",
        "start_date": (datetime.date.today() - datetime.timedelta(days=3*365)).isoformat(),
        "vat_status": "CZYNNY",
        "account_on_whitelist": True,
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
