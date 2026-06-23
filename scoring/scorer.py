from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from models.contractor import ContractorData

class CategoryScore(BaseModel):
    category_name: str
    score: int
    max_score: int
    status: str
    
class ScoringResult(BaseModel):
    total_score: int
    risk_level: str
    age_score: int
    reg_score: int
    cap_score: int
    bailiff_score: int
    color_code: str
    categories: List[CategoryScore]
    justifications: List[str]
    
async def enrich(data: ContractorData) -> ContractorData:
    justifications =[]
    categories_results = []
    
    has_bailiff = False
    age_score = 0
    reg_score = 0
    cap_score = 0
    bailiff_score = 0
    bailiff_status = "POZYTYWNY"
    
    country_code = (getattr(data, 'country_code', 'PL') or 'PL').upper()    
    
    # Doswiadczenie w biznesie (Experience in business)
    data_rozpoczecia = getattr(data, 'data_rozpoczecia', None)
    if data_rozpoczecia and isinstance(data.data_rozpoczecia, date):
        years_in_business = date.today().year - data.data_rozpoczecia.year
        age_score = 10 if years_in_business >=5 else (5 if years_in_business >= 2 else 0)
        justifications.append(f"Firma istnieje od {years_in_business} lat na rynku.")
    else:
        if country_code != "PL":
            age_score = 5
            justifications.append("Ogolne API UE nie udostepnia daty zalozenia dla kraju {country_code}.")
        else:
            age_score = 0 
            justifications.append("Brak mozliwosci zweryfikowania daty otwarcia firmy.")
            
    categories_results.append(CategoryScore(
        category_name="Doswiadczenie w biznesie", score = age_score, max_score = 10,
        status = "POZYTYWNY" if age_score == 10 else "OSTRZEZENIE" 
    ))
    
    # Status Rejestorwy
    
    legal_status = (getattr(data, 'status_prawny', 'NIEZNANY') or 'NIEZNANY' ).upper()
    status_vat = str(getattr(data, 'status_vat', 'NIEZNANY') or 'NIEZNANY').upper()
    on_whitelist = getattr(data, 'rachunek_na_bialej_liscie', False)
    
    if country_code == "PL":
        if legal_status == "AKTYWNA": reg_score += 5
        if "CZYNNY" in status_vat: reg_score += 5
        if on_whitelist: reg_score += 5
        
        if reg_score < 15:
            justifications.append(f"Status formalno-prawny w Polsce nie jest w pelni poprawny (status: {legal_status}, VAT: {status_vat}, Biala lista: {on_whitelist})")
        else:
            justifications.append(f"Firma w pelni aktywna, zarejestrowana jako platnik VAT , czynny na bialej liscie bankow.")
            
    else:
        if "CZYNNY" in status_vat or legal_status == "AKTYWNA":
            reg_score = 15
            justifications.append(f"Podmiot pomyslnie zweryfikowany w europejskiej bazie VIES ")
        else:
            reg_score = 5
            justifications.append(f"Podmiot nie jest zarejestrowany jako platnik VAT w europejskiej bazie VIES (status: {legal_status}, VAT: {status_vat})")
    
    
    categories_results.append(CategoryScore(
        category_name="Status formalno-prawny", score = reg_score, max_score = 15,
        status = "POZYTYWNY" if reg_score == 15 else "OSTRZEŻENIE"
    ))
    
    # Kapital firmy
    
    if country_code != "PL":
        cap_score = 10
        bailiff_score = 25
        justifications.append(f"Szczegolowa struktura kapitalowa oraz egzekucyjna dla kraju {country_code} wymaga komercyjnych raportow miedzynarodowych.")
    else:
        share_capital = getattr(data, 'share_capital', None)
        cap_score = 10 if (share_capital and share_capital >= 50000) else 5
        
        has_bailiff = getattr(data, 'has_bailiff_proceedings', None)
        if has_bailiff is True:
            bailiff_score = 0
            bailiff_status = "NEGATYWNY"
            justifications.append("Wykryto oficjalne wpisy o egzekucjach komorniczych.")
        elif has_bailiff is False:
            bailiff_score = 25
            bailiff_status = "POZYTYWNY"
            justifications.append("Brak wpisow o egzekucjach komorniczych.")
    
    
    categories_results.append(CategoryScore(
        category_name="Kapital zakladowy", score = cap_score, max_score = 10,
        status = "POZYTYWNY" if cap_score == 10 else "OSTRZEŻENIE"
    ))
    
    categories_results.append(CategoryScore(
        category_name="Postepowania komornicze", score = bailiff_score, max_score = 25,
        status = bailiff_status if country_code == "PL" else "NIEZNANY"
    ))
    
    total_score = age_score + reg_score + cap_score + bailiff_score 
    
    if has_bailiff is True:
        bailiff_score = -20
        risk_level = "KRYTYCZNE (Egzekucja komornicza)"
        color_code = "red"
    elif total_score >=41:
        risk_level = "Zagrozenie niskie (Zaufany kontrahent)"
        color_code = "green"
    elif total_score < 40 and total_score >= 20:
        risk_level = "Zagrozenie srednie (Zalecana ostroznosc)"
        color_code = "yellow"
    else:
        risk_level = "Zagrozenie wysokie"
        color_code = "red"
        
    scoring_result = ScoringResult(
        total_score=total_score,
        risk_level=risk_level,
        age_score=age_score,
        reg_score=reg_score,
        cap_score=cap_score,
        bailiff_score=bailiff_score,
        color_code=color_code,
        categories=categories_results,
        justifications=justifications
    )
    
    return data.model_copy(update={"scoring": scoring_result.model_dump()})