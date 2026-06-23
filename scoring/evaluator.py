from datetime import date
from models.contractor import ContractorData, RiskLevel, ScoreResult


def evaluate_contractor(data: ContractorData) -> ScoreResult:
    result = ScoreResult(nip=data.nip)
    today = date.today()

    # 1. Legal status
    if data.start_date:
        months = (today.year - data.start_date.year) * 12 + today.month - data.start_date.month
    else:
        months = 0

    status = data.legal_status
    if status == "AKTYWNA":
        if months <= 3:
            result.details.append("Status (0 pkt): Aktywna, założona niedawno — podwyższone ryzyko.")
        else:
            result.legal_status = 10
            result.details.append("Status (+10 pkt): Działalność aktywna.")
    elif status == "ZAWIESZONA":
        result.legal_status = -5
        result.details.append("Status (-5 pkt): Działalność zawieszona.")
    elif status in ("ZAMKNIETA", "UPADLOSC", "LIKWIDACJA"):
        result.legal_status = -10
        result.details.append(f"Status (-10 pkt): Działalność w stanie {status}.")
    else:
        result.details.append("Status (0 pkt): Brak danych o statusie.")

    # 2. Experience
    if data.frequent_legal_form_changes:
        result.experience = -5
        result.details.append("Doświadczenie (-5 pkt): Częste zmiany formy prawnej.")
    else:
        years = months / 12.0
        if years > 5:
            result.experience = 10
            result.details.append("Doświadczenie (+10 pkt): Firma istnieje powyżej 5 lat.")
        elif years >= 2:
            result.experience = 5
            result.details.append("Doświadczenie (+5 pkt): Firma istnieje od 2 do 5 lat.")
        else:
            result.details.append("Doświadczenie (0 pkt): Firma istnieje krócej niż 2 years.")

    # 3. VAT Taxes / Whitelist
    if data.vat_status == "CZYNNY" and data.account_on_whitelist:
        result.vat_taxes = 10
        result.details.append("Podatki (+10 pkt): Czynny podatnik VAT, rachunek na Białej Liście.")
    elif data.vat_status == "ZWOLNIONY":
        result.details.append("Podatki (0 pkt): Podmiot zwolniony z VAT.")
    elif data.vat_status == "WYKRESLONY" or (
        data.vat_status == "CZYNNY" and not data.account_on_whitelist and data.bank_account
    ):
        result.vat_taxes = -10
        result.details.append("Podatki (-10 pkt): Wykreślony z VAT lub konto niezgodne z Białą Listą!")
    else:
        result.details.append("Podatki (0 pkt): Brak danych VAT.")

    # 4. Stability
    if data.board_changes_last_3_months:
        result.stability = -10
        result.details.append("Stabilność (-10 pkt): Pełna wymiana zarządu i adresu w ostatnich 3 msc — WYSOKIE RYZYKO.")
    elif data.address_changes_last_year > 2:
        result.stability = -5
        result.details.append("Stabilność (-5 pkt): Więcej niż 2 zmiany adresu w ostatnim roku.")
    elif data.address_changes_last_year == 0 and not data.board_changes_last_3_months:
        result.stability = 10
        result.details.append("Stabilność (+10 pkt): Brak zmian zarządu i adresu.")
    else:
        result.details.append("Stabilność (0 pkt): Standardowe zmiany korporacyjne.")

    result.total = result.legal_status + result.experience + result.vat_taxes + result.stability

    if result.total >= 20:
        result.risk_level = RiskLevel.ACCEPT
    elif result.total >= 0:
        result.risk_level = RiskLevel.VERIFY
    else:
        result.risk_level = RiskLevel.REJECT

    return result
