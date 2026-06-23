import re

EU_COUNTRY_CODES = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "EL", "ES", "FI", "FR",
    "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT", "NL", "PL", "PT", "RO",
    "SE", "SI", "SK"
}

def parse_tax_id(raw_nip: str, selected_country: str = "PL") -> tuple[str, str]:
    clean = re.sub(r'[^A-Z0-9]', '', raw_nip.upper())
        
    if len(clean) > 2 and clean[:2].isalpha():
        prefix = clean[:2]
        if prefix in EU_COUNTRY_CODES:
            return prefix, clean[2:]
    
    return selected_country.upper(), clean