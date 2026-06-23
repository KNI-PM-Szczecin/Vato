from datetime import date
from models.contractor import ContractorData, RiskLevel, ScoreResult


def evaluate_contractor(data: ContractorData) -> ScoreResult:
    result = ScoreResult(nip=data.nip)
    today = date.today()

    # 1. Status prawny
    if data.data_rozpoczecia:
        miesiace = (today.year - data.data_rozpoczecia.year) * 12 + today.month - data.data_rozpoczecia.month
    else:
        miesiace = 0

    status = data.status_prawny
    if status == "AKTYWNA":
        if miesiace <= 3:
            result.szczegoly.append("Status (0 pkt): Aktywna, założona niedawno — podwyższone ryzyko.")
        else:
            result.status_prawny = 10
            result.szczegoly.append("Status (+10 pkt): Działalność aktywna.")
    elif status == "ZAWIESZONA":
        result.status_prawny = -5
        result.szczegoly.append("Status (-5 pkt): Działalność zawieszona.")
    elif status in ("ZAMKNIETA", "UPADLOSC", "LIKWIDACJA"):
        result.status_prawny = -10
        result.szczegoly.append(f"Status (-10 pkt): Działalność w stanie {status}.")
    else:
        result.szczegoly.append("Status (0 pkt): Brak danych o statusie.")

    # 2. Doświadczenie
    if data.czeste_zmiany_formy:
        result.doswiadczenie = -5
        result.szczegoly.append("Doświadczenie (-5 pkt): Częste zmiany formy prawnej.")
    else:
        lata = miesiace / 12.0
        if lata > 5:
            result.doswiadczenie = 10
            result.szczegoly.append("Doświadczenie (+10 pkt): Firma istnieje powyżej 5 lat.")
        elif lata >= 2:
            result.doswiadczenie = 5
            result.szczegoly.append("Doświadczenie (+5 pkt): Firma istnieje od 2 do 5 lat.")
        else:
            result.szczegoly.append("Doświadczenie (0 pkt): Firma istnieje krócej niż 2 lata.")

    # 3. Podatki VAT / Biała Lista
    if data.status_vat == "CZYNNY" and data.rachunek_na_bialej_liscie:
        result.podatki_vat = 10
        result.szczegoly.append("Podatki (+10 pkt): Czynny podatnik VAT, rachunek na Białej Liście.")
    elif data.status_vat == "ZWOLNIONY":
        result.szczegoly.append("Podatki (0 pkt): Podmiot zwolniony z VAT.")
    elif data.status_vat == "WYKRESLONY" or (
        data.status_vat == "CZYNNY" and not data.rachunek_na_bialej_liscie and data.bank_account
    ):
        result.podatki_vat = -10
        result.szczegoly.append("Podatki (-10 pkt): Wykreślony z VAT lub konto niezgodne z Białą Listą!")
    else:
        result.szczegoly.append("Podatki (0 pkt): Brak danych VAT.")

    # 4. Stabilność
    if data.wymiana_zarzadu_ostatnie_3msc:
        result.stabilnosc = -10
        result.szczegoly.append("Stabilność (-10 pkt): Pełna wymiana zarządu i adresu w ostatnich 3 msc — WYSOKIE RYZYKO.")
    elif data.zmiany_adresu_ostatni_rok > 2:
        result.stabilnosc = -5
        result.szczegoly.append("Stabilność (-5 pkt): Więcej niż 2 zmiany adresu w ostatnim roku.")
    elif data.zmiany_adresu_ostatni_rok == 0 and not data.wymiana_zarzadu_ostatnie_3msc:
        result.stabilnosc = 10
        result.szczegoly.append("Stabilność (+10 pkt): Brak zmian zarządu i adresu.")
    else:
        result.szczegoly.append("Stabilność (0 pkt): Standardowe zmiany korporacyjne.")

    result.total = result.status_prawny + result.doswiadczenie + result.podatki_vat + result.stabilnosc

    if result.total >= 20:
        result.risk_level = RiskLevel.ACCEPT
    elif result.total >= 0:
        result.risk_level = RiskLevel.VERIFY
    else:
        result.risk_level = RiskLevel.REJECT

    return result
