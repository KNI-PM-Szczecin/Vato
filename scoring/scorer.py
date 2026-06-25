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
    
    disabled_apis = getattr(data, 'disabled_apis', [])
    disabled_text = t("basic.disabled") if hasattr(t, '__call__') else "Wyłączono"
    
    has_bailiff = False
    age_score = 0
    reg_score = 0
    cap_score = 0
    credibility_score = 0
    sanctions_score = 20
    bailiff_score = 0
    bailiff_status = t("scorer.status_pos")
    
    country_code = (getattr(data, 'country_code', 'PL') or 'PL').upper()    
    
    status_vat = str(getattr(data, 'status_vat', 'NIEZNANY') or 'NIEZNANY').upper()
    legal_status = (getattr(data, 'status_prawny', 'NIEZNANY') or 'NIEZNANY').upper()
    on_whitelist = getattr(data, 'rachunek_na_bialej_liscie', False)
    is_vies_confirmed = getattr(data, 'is_vat_payer', False)
    
    missing_registry_data = (not data_rozpoczecia) and (legal_status in ("NIEZNANY", "", None))
    registry_skipped = missing_registry_data and (("KRS" in disabled_apis) or ("CEIDG" in disabled_apis))

    # 1. Experience
    if registry_skipped:
        age_max = 0
        age_score = 0
        age_status = disabled_text
    else:
        age_max = 10
        if data_rozpoczecia and isinstance(data.data_rozpoczecia, date):
            years_in_business = date.today().year - data.data_rozpoczecia.year
            age_score = 10 if years_in_business >=5 else (5 if years_in_business >= 2 else 0)
            justifications.append(t("scorer.age_years", years=years_in_business))
        else:
            if country_code != "PL":
                age_score = 5
                justifications.append(t("scorer.age_eu", country=country_code))
            else:
                age_score = 5
                justifications.append(t("scorer.age_unknown"))
        age_status = t("scorer.status_pos") if age_score == 10 else t("scorer.status_warn")
            
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_age"), score=age_score, max_score=age_max,
        status=age_status
    ))
    
    # 2. Registry Status & 3. Credibility
    reg_max = 15 if not registry_skipped else 0
    cred_max = 15 if ("VAT" not in disabled_apis and country_code == "PL") or ("VIES" not in disabled_apis and country_code != "PL") else 0

    if country_code == "PL":
        if "VAT" in disabled_apis:
            credibility_score = 0
            cred_status = disabled_text
        else:
            if "CZYNNY" in status_vat:
                credibility_score = 15
                justifications.append(t("scorer.cred_pl_good"))
            else:
                credibility_score = 0
                justifications.append(t("scorer.cred_pl_bad", status=status_vat))
            cred_status = t("scorer.status_pos") if credibility_score == 15 else t("scorer.status_warn")

        if registry_skipped:
            reg_score = 0
            reg_status = disabled_text
        else:
            if legal_status == "AKTYWNA":
                reg_score += 5
            elif legal_status in ("NIEZNANY", "", None):
                reg_score += 2
            if "CZYNNY" in status_vat:
                reg_score += 5
            if on_whitelist:
                reg_score += 5

            ceidg_likely = legal_status in ("NIEZNANY", "", None) and "CZYNNY" in status_vat
            fully_ok = legal_status == "AKTYWNA" and "CZYNNY" in status_vat
            if ceidg_likely:
                justifications.append(t("scorer.reg_ceidg_neutral"))
            elif fully_ok or reg_score >= 15:
                justifications.append(t("scorer.reg_pl_good"))
            else:
                whitelist_str = "TAK" if on_whitelist else "NIE"
                justifications.append(t("scorer.reg_pl_bad", legal=legal_status, vat=status_vat, whitelist=whitelist_str))
            reg_status = t("scorer.status_pos") if reg_score == 15 else t("scorer.status_warn")

    else:
        if "VIES" in disabled_apis:
            credibility_score = 0
            reg_score = 0
            cred_status = disabled_text
            reg_status = disabled_text
        else:
            vies_confirmed = "CZYNNY" in status_vat or legal_status == "AKTYWNA" or is_vies_confirmed
            if vies_confirmed:
                credibility_score = 15
                reg_score = 15
                justifications.append(t("scorer.reg_eu_good"))
            else:
                credibility_score = 5
                reg_score = 2
                justifications.append(t("scorer.reg_eu_bad", legal=legal_status, vat=status_vat))
            cred_status = t("scorer.status_pos") if credibility_score == 15 else t("scorer.status_warn")
            reg_status = t("scorer.status_pos") if reg_score == 15 else t("scorer.status_warn")
    
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_reg"), score=reg_score, max_score=reg_max,
        status=reg_status
    ))

    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_cred"), score=credibility_score, max_score=cred_max,
        status=cred_status
    ))
    
    # 4. Company capital
    cap_max = 10 if not registry_skipped else 0
    bailiff_max = 25 if not registry_skipped else 0
    if registry_skipped:
        cap_score = 0
        bailiff_score = 0
        cap_status = disabled_text
        bailiff_status = disabled_text
    else:
        if country_code != "PL":
            vies_confirmed = "CZYNNY" in status_vat or legal_status == "AKTYWNA" or is_vies_confirmed
            cap_score = 7 if not vies_confirmed else 10
            bailiff_score = 15 if not vies_confirmed else 20
            justifications.append(t("scorer.cap_eu", country=country_code))
        else:
            share_capital = getattr(data, 'share_capital', None)
            if share_capital is None:
                cap_score = 7
            else:
                cap_score = 10 if share_capital >= 50000 else 5

            has_bailiff = getattr(data, 'has_bailiff_proceedings', None)
            if has_bailiff is True:
                bailiff_score = 0
                bailiff_status = t("scorer.status_neg")
                justifications.append(t("scorer.bailiff_yes"))
            elif has_bailiff is False:
                bailiff_score = 25
                bailiff_status = t("scorer.status_pos")
                justifications.append(t("scorer.bailiff_no"))
            else:
                bailiff_score = 15
                bailiff_status = t("scorer.status_unk")
                justifications.append(t("scorer.bailiff_unknown"))
        cap_status = t("scorer.status_pos") if cap_score == 10 else t("scorer.status_warn")
    
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_cap"), score=cap_score, max_score=cap_max,
        status=cap_status
    ))
    
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_bailiff"), score=bailiff_score, max_score=bailiff_max,
        status=bailiff_status
    ))
    
    # Sanctions (derived from lists, assume part of KRS/VAT check, we leave as is, max 15)
    has_sanctions = getattr(data, 'on_sanctions_list', None)
    if has_sanctions is True:
        sanctions_score = 0
        justifications.append(t("scorer.sanctions_yes"))
    else:
        sanctions_score = 15
        justifications.append(t("scorer.sanctions_no"))
        
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_sanc"), score=sanctions_score, max_score=15,
        status=t("scorer.status_pos") if sanctions_score == 15 else t("scorer.status_warn")
    ))
    
    # 5. Digital credibility (Web)
    web_score = 0
    web_max = 10 if "WEB" not in disabled_apis else 0
    if "WEB" in disabled_apis:
        web_score = 0
        web_status = disabled_text
    else:
        website_url = getattr(data, 'website_url', None)
        if website_url:
            justifications.append(t("scorer.web_found", url=website_url))
            ssl_valid = getattr(data, 'ssl_valid', False)
            if ssl_valid:
                web_score += 2
                justifications.append(t("scorer.web_ssl_yes"))
            else:
                justifications.append(t("scorer.web_ssl_no"))
                
            domain_age = getattr(data, 'domain_age_days', None)
            if domain_age is not None:
                if domain_age > 730:
                    web_score += 2
                    justifications.append(t("scorer.web_age_2y", days=domain_age))
                elif domain_age > 180:
                    web_score += 1
                    justifications.append(t("scorer.web_age_6m", days=domain_age))
                elif domain_age < 90:
                    justifications.append(t("scorer.web_age_short", days=domain_age))
                else:
                    justifications.append(t("scorer.web_age_exact", days=domain_age))
            else:
                justifications.append(t("scorer.web_age_no"))
                
            days_since_post = getattr(data, 'days_since_last_post', None)
            if days_since_post is not None:
                if days_since_post <= 90:
                    web_score += 2
                    justifications.append(t("scorer.web_act_90", days=days_since_post))
                elif days_since_post <= 180:
                    web_score += 1
                    justifications.append(t("scorer.web_act_180", days=days_since_post))
                else:
                    justifications.append(t("scorer.web_act_old", days=days_since_post))
            else:
                justifications.append(t("scorer.web_act_no"))
                
            nip_matched = getattr(data, 'website_nip_matched', False)
            if nip_matched:
                web_score += 2
                justifications.append(t("scorer.web_nip_yes"))
            else:
                justifications.append(t("scorer.web_nip_no"))
        else:
            justifications.append(t("scorer.web_no"))
            
        news_found = getattr(data, 'news_found', False)
        if news_found:
            web_score += 2
            justifications.append(t("scorer.web_news_yes"))
        else:
            justifications.append(t("scorer.web_news_no"))
        web_status = t("scorer.status_pos") if web_score >= 5 else (t("scorer.status_warn") if web_score >= 0 else t("scorer.status_neg"))
            
    categories_results.append(CategoryScore(
        category_name=t("scorer.cat_web"), 
        score=web_score, 
        max_score=web_max,
        status=web_status
    ))
    
    # 6. Reputation & Domain Anomalies Penalties
    domain_penalty = 0
    if "WEB" not in disabled_apis:
        suspicious_domain = getattr(data, 'suspicious_domain', False)
        if suspicious_domain:
            domain_penalty = -10
            justifications.append(t("scorer.web_domain_warn"))
            
    news_penalty = 0
    if "NEWS" not in disabled_apis:
        news_anomalies = getattr(data, 'news_anomalies', None) or []
        if news_anomalies:
            news_penalty = -15
            justifications.append(t("scorer.web_news_warn"))
            for article in news_anomalies[:3]:
                justifications.append(f"  * {article.get('title')}")
            
    total_score_raw = age_score + reg_score + cap_score + bailiff_score + credibility_score + sanctions_score + web_score + domain_penalty + news_penalty
    total_max = sum(cat.max_score for cat in categories_results)
    
    # Normalize to 100 points scale for the UI logic
    if total_max > 0:
        total_score = int((total_score_raw / total_max) * 100)
    else:
        total_score = 0
        
    total_score = max(0, min(100, total_score))
    
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