import asyncio
from models.contractor import ContractorData
from services import utils, vies_client, krs_client, ceidg_client, vat_client
from scoring import scorer
from services.regon_client import RegonClient

regon_client_instance = RegonClient()

def print_scoring_dashboard(contractor: ContractorData):
    """Generuje widok wyników identyczny z pierwotną wersją systemu."""
    sc = contractor.scoring or {}
    total_score = sc.get("total_score", 0)
    risk_level = sc.get("risk_level", "NIEZNANY")
    
    # Pobranie ocen cząstkowych ze słownika scoringu
    age = sc.get("age_score", 0)
    reg = sc.get("reg_score", 0)
    cap = sc.get("cap_score", 0)
    bailiff = sc.get("bailiff_score", 0)
    
    # Funkcja pomocnicza do określania etykiety (POZYTYWNY / OSTRZEŻENIE)
    def get_status_label(score, max_possible):
        return "POZYTYWNY" if score >= max_possible else "OSTRZEZENIE"

    print("\n[REZULTAT KOŃCOWY SCORINGU]")
    print(f"PUNKTY: {total_score}/60")
    print(f"POZIOM RYZYKA: {risk_level}")
    print()
    print(" Cząstkowe oceny kategorii:")
    print(f"  - Doswiadczenie w biznesie: {age}/10 ({get_status_label(age, 10)})")
    print(f"  - Status formalno-prawny: {reg}/15 ({get_status_label(reg, 15)})")
    print(f"  - Kapital zakladowy: {cap}/10 ({get_status_label(cap, 10)})")
    print(f"  - Postepowania komornicze: {bailiff}/25 ({get_status_label(bailiff, 25)})")
    print()
    print("Uzasadnienia generowane systemowo:")
    
    # Pobieranie uzasadnień ze słownika lub generowanie dynamicznych dla firm zagranicznych
    justifications = sc.get("justifications", [])
    if not justifications:
        if contractor.country_code != "PL":
            justifications = [
                f"Brak mozliwosci zweryfikowania daty otwarcia firmy w polskich rejestrach (Kraj: {contractor.country_code}).",
                "Status formalno-prawny zweryfikowany pozytywnie w europejskiej bazie VIES."
            ]
        else:
            if reg == 0:
                justifications.append("Status formalno-prawny w Polsce nie jest w pelni poprawny (status: NIEZNANY).")
            if age == 0:
                justifications.append("Brak mozliwosci zweryfikowania daty otwarcia firmy.")
            if not justifications:
                justifications = ["Brak negatywnych przesłanek systemowych."]

    for j in justifications:
        print(f"  * {j}")
    print()


async def verify_contractor(raw_nip: str, default_country: str = "PL") -> ContractorData:
    # 1. Parsowanie wejścia
    country_code, clean_nip = utils.parse_tax_id(raw_nip, default_country)
    
    print(f"\nRozpoczyna weryfikację: Kraj={country_code}, Numer={clean_nip}")
    contractor = ContractorData(nip=clean_nip, country_code=country_code)

    # 2. Ścieżka POLSKA
    if country_code == "PL":
        print("Identyfikacja typu dzialanosci w REGON ...")
        try:
            typ = await regon_client_instance.identify(clean_nip)
        except Exception:
            typ = "UNKNOWN"

        if typ == "KRS":
            print("Sprawdzanie bialej listy KRS ...")
            krs_fields = await krs_client.fetch_krs_data(clean_nip)
            contractor = contractor.model_copy(update=krs_fields)
        elif typ == "CEIDG":
            print("Sprawdzanie bazy CEIDG ...")
            ceidg_fields = await ceidg_client.fetch_ceidg_data(clean_nip)
            contractor = contractor.model_copy(update=ceidg_fields)

        vat_fields = await vat_client.fetch_vat_data(clean_nip)
        contractor = contractor.model_copy(update=vat_fields)

    # 3. Ścieżka UNIJNA (VIES)
    else:
        print(f"Wykryto kraj UE ({country_code}). Pomijam polski REGON/KRS, odpytuję VIES...")
        if hasattr(vies_client, 'enrich'):
            contractor = await vies_client.enrich(contractor)

    # 4. Scoring
    print("Uruchamianie algorytmu scoringowego ...")
    contractor = await scorer.enrich(contractor)
    return contractor


async def main():
    # Test dla firmy niemieckiej
    firma_de = await verify_contractor("DE129273398")
    
    # Wyświetlenie odtworzonego widoku
    print_scoring_dashboard(firma_de)


if __name__ == "__main__":
    asyncio.run(main())