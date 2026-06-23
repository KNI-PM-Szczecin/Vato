import os
import glob

replacements = {
    "status_prawny": "legal_status",
    "data_rozpoczecia": "start_date",
    "status_vat": "vat_status",
    "rachunek_na_bialej_liscie": "account_on_whitelist",
    "zmiany_adresu_ostatni_rok": "address_changes_last_year",
    "wymiana_zarzadu_ostatnie_3msc": "board_changes_last_3_months",
    "czeste_zmiany_formy": "frequent_legal_form_changes",
    "doswiadczenie": "experience",
    "podatki_vat": "vat_taxes",
    "stabilnosc": "stability",
    "szczegoly": "details",
    "miesiace": "months",
    "lata": "years",
    "data_rej_str": "reg_date_str",
    "data_rej": "reg_date",
    "dzial1": "section1",
    "status_kolor": "status_color",
    "rekomendacja": "recommendation",
    "raport_szybki": "quick_report",
    "pelny_raport": "full_report",
    "dzialy": "sections",
    "odpis": "copy_doc",
    "danePodmiotu": "subject_data",
    "statusPodmiotu": "subject_status",
    "dataRozpoczecia": "start_date_json",
    "pParametryWyszukiwania": "search_params",
    "DaneSzukajPodmioty": "SearchSubjects",
    "KluczUzytkownika": "UserKey",
    "Zaloguj": "Login",
    "pKluczUzytkownika": "pUserKey",
    "ZalogujResult": "LoginResult",
    "UslugaBIRzewnPubl": "BIRServiceExternalPubl",
    "wyszukiwarkaregon": "regon_search",
    "Nip": "Nip",
    "Typ": "Type"
}

files = glob.glob("**/*.py", recursive=True)
for f in files:
    if "venv" in f or "__pycache__" in f or "rename.py" in f:
        continue
    with open(f, "r", encoding="utf-8") as file:
        content = file.read()
    
    new_content = content
    for k, v in replacements.items():
        new_content = new_content.replace(k, v)
        
    if new_content != content:
        with open(f, "w", encoding="utf-8") as file:
            file.write(new_content)
        print(f"Updated {f}")

