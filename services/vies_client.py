import httpx
from models.contractor import ContractorData

BASE_URL = "https://ec.europa.eu/taxation_customs/vies/rest-api/ms"

async def fech_vies_data(country_code: str, vat_number: str) -> dict:
    url = f"{BASE_URL}/{country_code}/vies/vat/{vat_number}"
    
    default_response = {
        "is_vat_payer": False,
        "legal_name": "---",
        "raw_status": "INVALID",
        "country_code": country_code,
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return default_response
            
            res_data = resp.json()
            
            is_valid = res_data.get("isValid", False)
            name = res_data.get("name", "---").strip()
            
            return{
                "is_vat_payer": is_valid,
                "legal_name": name if name else "---",
                "raw_status": "VALID" if is_valid else "INVALID",
                "country_code": country_code,
            }
            
    except Exception as e:
        print(f"Error fetching VIES data: {e}")
        return default_response

async def enrich(data: ContractorData) -> ContractorData:
    country = getattr(data, 'country_code', 'PL') or 'PL'
    vies_data = await fech_vies_data(country, data.nip)

    update = {
        "is_vat_payer": vies_data["is_vat_payer"],
        "status_vat": "CZYNNY" if vies_data["is_vat_payer"] else "NIEZNANY",
        "status_prawny": "AKTYWNA" if vies_data["is_vat_payer"] else "NIEZNANY",
    }
    # Only overwrite legal_name if VIES returned a real name
    vies_name = vies_data.get("legal_name", "---")
    if vies_name and vies_name != "---":
        update["legal_name"] = vies_name

    return data.model_copy(update=update)