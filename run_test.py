import asyncio
from models.contractor import ContractorData
from services import utils, vies_client, krs_client, ceidg_client, vat_client
from scoring import scorer
from services.regon_client import RegonClient

regon_client_instance = RegonClient()

async def verify_contractor(raw_nip: str, default_country: str = "PL") -> ContractorData:
    # 1. Parsowanie wejścia (odcina DE od numeru)
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
        contractor = await vies_client.enrich(contractor)

    # 4. Scoring
    print("Uruchamianie algorytmu scoringowego ...")
    contractor = await scorer.enrich(contractor)
    return contractor

async def main():
    # Odpalamy test dla Niemiec - teraz przejdzie poprawnie przez ścieżkę UE!
    firma_de = await verify_contractor("DE129273398")
    
    print("\n" + "="*40)
    print(f"Wynik DE: {firma_de.legal_name} -> {firma_de.scoring['risk_level']} ({firma_de.scoring['total_score']} pkt)")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(main())