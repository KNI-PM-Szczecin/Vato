from models.contractor import ContractorData
from services import krs_client, ceidg_client, vies_client, utils, vat_client
from scoring import scorer
from services.regon_client import RegonClient

regon_client = RegonClient()

async def verify_contractor(raw_nip: str, selected_country: str = "PL", bank_account: str = None) -> ContractorData:
    country_code, clean_nip = utils.parse_tax_id(raw_nip, selected_country)
    
    print(f"\nRozpoczyna weryfikacje: Kraj={country_code}, Numer={clean_nip} ")
    
    contractor = ContractorData(
        nip=clean_nip,
        country_code=country_code,
        bank_account=bank_account
    )
    
    if country_code == "PL":
        print(f"\nSprawdzanie bialej listy VAT (Ministerstwo Finansow) ...")
        vat_data = await vat_client.fetch_vat_data(clean_nip, bank_account)
        contractor = contractor.model_copy(update=vat_data)
        
        krs_number = vat_data.get("krs_number")
        
        if krs_number:
            print(f"\nPobieranie danych z KRS (Numer KRS: {krs_number}) ...")
            krs_data = await krs_client.fetch_krs_data(clean_nip, krs_numer=krs_number)
            contractor = contractor.model_copy(update=krs_data)
        else:
            print(f"\nBrak numeru KRS na bialej liscie. Identyfikacja typu dzialanosci...")
            try:
                typ = await regon_client.identify(clean_nip)
            except Exception as e:
                print(f"Blad Regon: {e}")
                typ = "UNKNOWN"
                
            if typ == "KRS":
                print(f"\nPobieranie danych z KRS ...")
                krs_data = await krs_client.fetch_krs_data(clean_nip)
                contractor = contractor.model_copy(update=krs_data)
            elif typ == "CEIDG":
                print(f"\nPobieranie danych z CEIDG ...")
                ceidg_data = await ceidg_client.fetch_ceidg_data(clean_nip)
                contractor = contractor.model_copy(update=ceidg_data)
            elif typ == "UNKNOWN":
                print(f"REGON niedostepny. Proba weryfikacji w KRS/CEIDG...")
                krs_data = await krs_client.fetch_krs_data(clean_nip)
                if krs_data:
                    print(f"Wykryto podmiot w KRS.")
                    contractor = contractor.model_copy(update=krs_data)
                else:
                    ceidg_data = await ceidg_client.fetch_ceidg_data(clean_nip)
                    if ceidg_data:
                        print(f"Wykryto podmiot w CEIDG.")
                        contractor = contractor.model_copy(update=ceidg_data)
        
    else:
        print(f"\nPobieranie danych z VIES ...")
        contractor = await vies_client.enrich(contractor)
        
    print(f"\nWeryfikacja cyfrowa (strona WWW, SSL, wiek domeny) ...")
    try:
        from services import web_verifier
        contractor = await web_verifier.enrich_with_web_data(contractor)
    except Exception as e:
        print(f"Błąd weryfikacji cyfrowej: {e}")
        
    print(f"\nWyszukiwanie wiadomosci prasowych (Google News) ...")
    try:
        from services import news_verifier
        news_data = await news_verifier.fetch_company_news(contractor.legal_name)
        contractor = contractor.model_copy(update={
            "news_found": news_data["news_found"],
            "news_anomalies": news_data["anomalies"]
        })
    except Exception as e:
        print(f"Błąd wyszukiwania wiadomości prasowych: {e}")
    
    print(f"\nUruchamianie algorytmu scoringowego ...")
    contractor = await scorer.enrich(contractor)

    return contractor