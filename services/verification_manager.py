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
        print(f"\nIdentyfikacja typu dzialanosci w REGON ...")
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
            
        print(f"Sprawdzanie bialej listy KRS ...")
        vat_data = await vat_client.fetch_vat_data(clean_nip, bank_account)
        contractor = contractor.model_copy(update=vat_data)
        
    else:
        print(f"\nPobieranie danych z VIES ...")
        contractor = await vies_client.enrich(contractor)
    
    print(f"\nUruchamianie algorytmu scoringowego ...")
    contractor = await scorer.enrich(contractor)

    return contractor