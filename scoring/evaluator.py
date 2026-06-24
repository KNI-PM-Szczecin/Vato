from datetime import date
from models.contractor import ContractorData, RiskLevel, ScoreResult


def evaluate_contractor(data: ContractorData) -> ScoreResult:
    """
    Evaluates a contractor's risk level based on aggregated data.
    The total score is calculated across four key categories:
    1. Legal status
    2. Experience
    3. VAT / Whitelist credibility
    4. Corporate stability
    
    Returns a ScoreResult containing points and detailed justifications.
    """
    result = ScoreResult(nip=data.nip)
    today = date.today()

    # 1. Legal status
    if data.start_date:
        months = (today.year - data.start_date.year) * 12 + today.month - data.start_date.month
    else:
        months = 0

    status = data.legal_status
    if status == "ACTIVE":
        if months <= 3:
            result.details.append("Legal status (0 pts): Active but registered recently — elevated risk.")
        else:
            result.legal_status = 10
            result.details.append("Legal status (+10 pts): Active business.")
    elif status == "SUSPENDED":
        result.legal_status = -5
        result.details.append("Legal status (-5 pts): Business suspended.")
    elif status in ("CLOSED", "BANKRUPTCY", "LIQUIDATION"):
        result.legal_status = -10
        result.details.append(f"Legal status (-10 pts): Business in state: {status.lower()}.")
    else:
        result.details.append("Legal status (0 pts): No status data available.")

    # 2. Experience
    if data.frequent_legal_form_changes:
        result.experience = -5
        result.details.append("Experience (-5 pts): Frequent changes of legal form.")
    else:
        years = months / 12.0
        if years > 5:
            result.experience = 10
            result.details.append("Experience (+10 pts): Company has been operating for over 5 years.")
        elif years >= 2:
            result.experience = 5
            result.details.append("Experience (+5 pts): Company has been operating for 2–5 years.")
        else:
            result.details.append("Experience (0 pts): Company has been operating for less than 2 years.")

    # 3. VAT / Whitelist
    if data.vat_status == "CZYNNY" and data.account_on_whitelist:
        result.vat_taxes = 10
        result.details.append("VAT (+10 pts): Active VAT payer, bank account on the MF Whitelist.")
    elif data.vat_status == "ZWOLNIONY":
        result.details.append("VAT (0 pts): Entity VAT-exempt.")
    elif data.vat_status == "WYKRESLONY" or (
        data.vat_status == "CZYNNY" and not data.account_on_whitelist and data.bank_account
    ):
        result.vat_taxes = -10
        result.details.append("VAT (-10 pts): Removed from VAT register or bank account not on the Whitelist!")
    else:
        result.details.append("VAT (0 pts): No VAT data available.")

    # 4. Stability
    if data.board_changes_last_3_months:
        result.stability = -10
        result.details.append("Stability (-10 pts): Full board and address change in last 3 months — HIGH RISK.")
    elif data.address_changes_last_year > 2:
        result.stability = -5
        result.details.append("Stability (-5 pts): More than 2 address changes in the last year.")
    elif data.address_changes_last_year == 0 and not data.board_changes_last_3_months:
        result.stability = 10
        result.details.append("Stability (+10 pts): No board or address changes.")
    else:
        result.details.append("Stability (0 pts): Minor standard corporate changes.")

    # Final Score Calculation
    result.total = result.legal_status + result.experience + result.vat_taxes + result.stability

    # Determine Risk Level Recommendation
    if result.total >= 20:
        result.risk_level = RiskLevel.ACCEPT
    elif result.total >= 0:
        result.risk_level = RiskLevel.VERIFY
    else:
        result.risk_level = RiskLevel.REJECT

    return result
