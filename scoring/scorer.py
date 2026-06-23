from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from models.contractor import ContractorData
from services.i18n import t

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
    credibility_score: int
    sanctions_score: int
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
    credibility_score = 0
    sanctions_score = 20
    bailiff_score = 0
    bailiff_status = t("scorer.status_pos")
    
    country_code = (getattr(data, 'country_code', 'PL') or 'PL').upper()    
    
    # Doswiadczenie w biznesie (Experience in business)
    data_rozpoczecia = getattr(data, 'data_rozpoczecia', None)
    if data_rozpoczecia and isinstance(data.data_rozpoczecia, date):
        years_in_business = date.today().year - data.data_rozpoczecia.year
        age_score = 10 if years_in_business >=5 else (5 if years_in_business >= 2 else 0)
        justifications.append(t("scorer.age_years", years=years_in_business))
    else:
        if country_code != "PL":
            age_score = 5
            justifications.append(t("scorer.age_eu", country=country_code))
        else:
            age_score = 0 
            justifications.append(t("scorer.age_unknown"))
            
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_age"), score=age_score, max_score=10,
        status=t("scorer.status_pos") if age_score == 10 else t("scorer.status_warn")
    ))
    
    # Status Rejestrowy & Wiarygodnosc
    status_vat = str(getattr(data, 'status_vat', 'NIEZNANY') or 'NIEZNANY').upper()
    if country_code == "PL":
        if "CZYNNY" in status_vat:
            credibility_score = 15
            justifications.append(t("scorer.cred_pl_good"))
        else:
            credibility_score = 0
            justifications.append(t("scorer.cred_pl_bad", status=status_vat))
    else:
        credibility_score = 15
        justifications.append(t("scorer.cred_eu_unknown", country=country_code))

    legal_status = (getattr(data, 'status_prawny', 'NIEZNANY') or 'NIEZNANY' ).upper()
    on_whitelist = getattr(data, 'rachunek_na_bialej_liscie', False)
    
    if country_code == "PL":
        if legal_status == "AKTYWNA": reg_score += 5
        if "CZYNNY" in status_vat: reg_score += 5
        if on_whitelist: reg_score += 5
        
        if reg_score < 15:
            justifications.append(t("scorer.reg_pl_bad", legal=legal_status, vat=status_vat, whitelist=on_whitelist))
        else:
            justifications.append(t("scorer.reg_pl_good"))
            
    else:
        if "CZYNNY" in status_vat or legal_status == "AKTYWNA":
            reg_score = 15
            justifications.append(t("scorer.reg_eu_good"))
        else:
            reg_score = 5
            justifications.append(t("scorer.reg_eu_bad", legal=legal_status, vat=status_vat))
    
    
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_reg"), score=reg_score, max_score=15,
        status=t("scorer.status_pos") if reg_score == 15 else t("scorer.status_warn")
    ))

    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_cred"), score=credibility_score, max_score=15,
        status=t("scorer.status_pos") if credibility_score == 15 else t("scorer.status_warn")
    ))
    
    # Kapital firmy
    if country_code != "PL":
        cap_score = 10
        bailiff_score = 25
        justifications.append(t("scorer.cap_eu", country=country_code))
    else:
        share_capital = getattr(data, 'share_capital', None)
        cap_score = 10 if (share_capital and share_capital >= 50000) else 5
        
        has_bailiff = getattr(data, 'has_bailiff_proceedings', None)
        if has_bailiff is True:
            bailiff_score = 0
            bailiff_status = t("scorer.status_neg")
            justifications.append(t("scorer.bailiff_yes"))
        elif has_bailiff is False:
            bailiff_score = 25
            bailiff_status = t("scorer.status_pos")
            justifications.append(t("scorer.bailiff_no"))
    
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_cap"), score=cap_score, max_score=10,
        status=t("scorer.status_pos") if cap_score == 10 else t("scorer.status_warn")
    ))
    
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_bailiff"), score=bailiff_score, max_score=25,
        status=bailiff_status if country_code == "PL" else t("scorer.status_unk")
    ))
    
    has_sanctions = getattr(data, 'on_sanctions_list', None)
    if has_sanctions is True:
        sanctions_score = 0
        justifications.append("Podmiot figuruje na oficjalnej liscie sankcji.")
    else:
        sanctions_score = 15
        justifications.append("Brak wpisow o sankcjach na oficjalnych listach.")
        
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_sanc"), score=sanctions_score, max_score=15,
        status=t("scorer.status_pos") if sanctions_score == 15 else t("scorer.status_warn")
    ))
    
    # Wiarygodność cyfrowa (Website scraping, SSL, Age, RSS)
    web_score = 0
    website_url = getattr(data, 'website_url', None)
    
    if website_url:
        justifications.append(f"Zidentyfikowano oficjalną stronę WWW: {website_url}")
        
        # 1. SSL Check
        ssl_valid = getattr(data, 'ssl_valid', False)
        if ssl_valid:
            web_score += 2
            justifications.append("Witryna zabezpieczona poprawnym certyfikatem SSL/TLS (+2 pkt).")
        else:
            justifications.append("Witryna nie posiada aktywnego/poprawnego certyfikatu SSL/TLS (0 pkt).")
            
        # 2. Domain Age Check
        domain_age = getattr(data, 'domain_age_days', None)
        if domain_age is not None:
            if domain_age > 730:
                web_score += 3
                justifications.append(f"Domena zarejestrowana ponad 2 lata temu ({domain_age} dni temu) (+3 pkt).")
            elif domain_age > 180:
                web_score += 1
                justifications.append(f"Domena zarejestrowana ponad 6 miesięcy temu ({domain_age} dni temu) (+1 pkt).")
            elif domain_age < 90:
                justifications.append(f"Domena zarejestrowana niedawno ({domain_age} dni temu) (0 pkt).")
            else:
                justifications.append(f"Domena zarejestrowana {domain_age} dni temu (0 pkt).")
        else:
            justifications.append("Brak danych o wieku domeny w RDAP (0 pkt).")
            
        # 3. Activity Check
        days_since_post = getattr(data, 'days_since_last_post', None)
        if days_since_post is not None:
            if days_since_post <= 90:
                web_score += 3
                justifications.append(f"Witryna aktywnie prowadzona, ostatnia aktywność {days_since_post} dni temu (+3 pkt).")
            elif days_since_post <= 180:
                web_score += 1
                justifications.append(f"Umiarkowana aktywność witryny, ostatnia aktualizacja {days_since_post} dni temu (+1 pkt).")
            else:
                justifications.append(f"Witryna nie była aktualizowana od {days_since_post} dni (0 pkt).")
        else:
            justifications.append("Brak aktywnego kanału RSS lub nowych artykułów (0 pkt).")
            
        # 4. NIP Match Check
        nip_matched = getattr(data, 'website_nip_matched', False)
        if nip_matched:
            web_score += 2
            justifications.append("Zgodność tożsamości: NIP firmy odnaleziony na jej stronie WWW (+2 pkt).")
        else:
            justifications.append("NIP firmy nie został odnaleziony bezpośrednio na stronie głównej (0 pkt).")
    else:
        justifications.append("Nie odnaleziono oficjalnej witryny kontrahenta (0 pkt).")
        
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_web"), 
        score=web_score, 
        max_score=10,
        status="POZYTYWNY" if web_score >= 5 else ("OSTRZEŻENIE" if web_score >= 0 else "NEGATYWNY")
    ))
    
    total_score = age_score + reg_score + cap_score + bailiff_score + credibility_score + sanctions_score + web_score
    
    if has_bailiff is True:
        bailiff_score = -20
        risk_level = t("scorer.risk_critical")
        color_code = "red"
    elif total_score >= 66:
        risk_level = t("scorer.risk_low")
        color_code = "green"
    elif total_score < 66 and total_score >= 30:
        risk_level = t("scorer.risk_med")
        color_code = "yellow"
    else:
        risk_level = t("scorer.risk_high")
        color_code = "red"
        
    scoring_result = ScoringResult(
        total_score=total_score,
        risk_level=risk_level,
        age_score=age_score,
        reg_score=reg_score,
        cap_score=cap_score,
        bailiff_score=bailiff_score,
        credibility_score=credibility_score,
        sanctions_score=sanctions_score,
        color_code=color_code,
        categories=categories_results,
        justifications=justifications
    )
    
    return data.model_copy(update={"scoring": scoring_result.model_dump()})