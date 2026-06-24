"""
Builds a natural-language spoken summary of a ContractorData object for ElevenLabs TTS.
Avoids all formatting characters, technical abbreviations, and log-style punctuation
that cause a TTS model to stutter or read nonsense.
"""

from __future__ import annotations
from datetime import date
from services.i18n import get_language as get_current_language


def build_tts_report(contractor) -> str:
    lang = get_current_language()
    if lang == "pl":
        return _build_pl(contractor)
    elif lang == "de":
        return _build_de(contractor)
    return _build_en(contractor)


def _years_ago(d: date) -> int:
    return date.today().year - d.year

def _spaced_nip(nip: str) -> str:
    return " ".join(list(nip)) if nip else ""


def _build_pl(c) -> str:
    parts: list[str] = []

    name = getattr(c, "legal_name", None) or "nieznana firma"
    nip  = getattr(c, "nip", "")
    scoring = getattr(c, "scoring", {}) or {}
    total   = scoring.get("total_score")
    risk    = scoring.get("risk_level", "")
    color   = scoring.get("color_code", "yellow")

    risk_map = {
        "Accepted": "akceptacja",
        "Verification Required": "wymagana weryfikacja",
        "Rejected": "odrzucenie"
    }
    risk_pl = risk_map.get(risk, risk) if risk else ""

    # ── scoring result ─────────────────────────────────────────────────────────
    parts.append(f"Weryfikacja zakończona.")
    if nip:
        parts.append(f"Numer NIP: {_spaced_nip(nip)}.")

    if total is not None:
        parts.append(f"Wynik oceny ryzyka: {total} punktów na sto możliwych.")
        if risk_pl:
            parts.append(f"Rekomendacja: {risk_pl}.")

    # ── legal status ───────────────────────────────────────────────────────────
    status_prawny = (getattr(c, "status_prawny", "") or "").upper()
    data_rozp = getattr(c, "data_rozpoczecia", None)

    if data_rozp:
        lata = _years_ago(data_rozp)
        parts.append(f"Firma działa od {lata} {'roku' if lata == 1 else 'lat'}.")
    else:
        parts.append("Nie udało się ustalić daty rejestracji firmy.")

    if status_prawny == "AKTYWNA":
        parts.append("Status w rejestrze KRS: aktywna.")
    elif status_prawny == "ZAWIESZONA":
        parts.append("Status w rejestrze KRS: zawieszona.")
    elif status_prawny == "WYKREŚLONA" or status_prawny == "WYKREŚLONY":
        parts.append("Status w rejestrze KRS: wykreślona.")
    elif status_prawny not in ("", "NIEZNANY"):
        parts.append("Status w rejestrze: nieznany.")

    # ── VAT ───────────────────────────────────────────────────────────────────
    vat = (getattr(c, "status_vat", "") or "").upper()
    if "CZYNNY" in vat:
        parts.append("Firma jest czynnym płatnikiem podatku VAT.")
    elif "WYKREŚLONY" in vat or "WYKRESLONY" in vat:
        parts.append("Uwaga: firma została wykreślona z rejestru VAT.")
    elif "ZWOLNIONY" in vat:
        parts.append("Firma jest zwolniona z podatku VAT.")

    whitelist = getattr(c, "rachunek_na_bialej_liscie", False)
    if whitelist:
        parts.append("Konto bankowe firmy widnieje na Białej Liście Ministerstwa Finansów.")

    # ── share capital ─────────────────────────────────────────────────────────
    cap = getattr(c, "share_capital", None)
    if cap is not None:
        parts.append(f"Kapitał zakładowy wynosi {int(cap):,} złotych.".replace(",", " "))

    # ── bailiff ───────────────────────────────────────────────────────────────
    bailiff = getattr(c, "has_bailiff_proceedings", None)
    if bailiff is True:
        parts.append("Ostrzeżenie: wykryto aktywne postępowania komornicze.")
    elif bailiff is False:
        parts.append("Brak postępowań komorniczych.")

    # ── sanctions ─────────────────────────────────────────────────────────────
    sanctions = getattr(c, "on_sanctions_list", None)
    if sanctions is True:
        parts.append("Uwaga: podmiot figuruje na oficjalnej liście sankcji.")
    else:
        parts.append("Brak wpisów na listach sankcji.")

    # ── website ───────────────────────────────────────────────────────────────
    website = getattr(c, "website_url", None)
    ssl     = getattr(c, "ssl_valid", None)
    domain_age = getattr(c, "domain_age_days", None)
    activity   = getattr(c, "days_since_last_post", None)

    if website:
        parts.append("Zidentyfikowano oficjalną stronę internetową firmy.")
        if ssl:
            parts.append("Strona posiada ważny certyfikat bezpieczeństwa.")
        if domain_age and domain_age > 730:
            parts.append(f"Domena działa od ponad {domain_age // 365} lat.")
        if activity is not None and activity <= 90:
            parts.append(f"Strona była aktualizowana {activity} dni temu.")
    else:
        parts.append("Nie odnaleziono oficjalnej strony internetowej firmy.")

    # ── summary ───────────────────────────────────────────────────────────────
    if color == "green":
        parts.append("Podsumowanie: kontrahent oceniony jako wiarygodny i bezpieczny.")
    elif color == "red":
        parts.append("Podsumowanie: kontrahent oceniony jako wysokiego ryzyka. Zalecana szczegółowa weryfikacja.")
    else:
        parts.append("Podsumowanie: zalecana ostrożność przy współpracy z tym kontrahentem.")

    parts.append(f"Raport wygenerowano dla podmiotu: {name}.")

    return " ".join(parts)


def _build_en(c) -> str:
    parts: list[str] = []

    name = getattr(c, "legal_name", None) or "unknown company"
    nip  = getattr(c, "nip", "")
    scoring = getattr(c, "scoring", {}) or {}
    total   = scoring.get("total_score")
    risk    = scoring.get("risk_level", "")
    color   = scoring.get("color_code", "yellow")

    parts.append("Verification complete.")
    if nip:
        parts.append(f"Tax ID: {_spaced_nip(nip)}.")

    if total is not None:
        parts.append(f"Risk score: {total} out of 100 points.")
        if risk:
            parts.append(f"Recommendation: {risk}.")

    status_prawny = (getattr(c, "status_prawny", "") or "").upper()
    data_rozp = getattr(c, "data_rozpoczecia", None)

    if data_rozp:
        lata = _years_ago(data_rozp)
        parts.append(f"The company has been operating for {lata} {'year' if lata == 1 else 'years'}.")
    else:
        parts.append("Unable to determine the company registration date.")

    if status_prawny == "AKTYWNA":
        parts.append("Registry status: active.")
    elif status_prawny == "ZAWIESZONA":
        parts.append("Registry status: suspended.")
    elif status_prawny == "WYKREŚLONA" or status_prawny == "WYKREŚLONY":
        parts.append("Registry status: removed.")
    elif status_prawny not in ("", "NIEZNANY"):
        parts.append("Registry status: unknown.")

    vat = (getattr(c, "status_vat", "") or "").upper()
    if "CZYNNY" in vat:
        parts.append("The company is an active VAT payer.")
    elif "WYKREŚLONY" in vat or "WYKRESLONY" in vat:
        parts.append("Warning: the company has been removed from the VAT register.")
    elif "ZWOLNIONY" in vat:
        parts.append("The company is VAT exempt.")

    whitelist = getattr(c, "rachunek_na_bialej_liscie", False)
    if whitelist:
        parts.append("The bank account of the company is on the white list.")

    cap = getattr(c, "share_capital", None)
    if cap is not None:
        parts.append(f"Share capital: {int(cap):,} Polish zloty.")

    bailiff = getattr(c, "has_bailiff_proceedings", None)
    if bailiff is True:
        parts.append("Warning: active enforcement proceedings detected.")
    elif bailiff is False:
        parts.append("No enforcement proceedings found.")

    sanctions = getattr(c, "on_sanctions_list", None)
    if sanctions is True:
        parts.append("Warning: entity appears on an official sanctions list.")
    else:
        parts.append("No sanctions list entries found.")

    website = getattr(c, "website_url", None)
    ssl     = getattr(c, "ssl_valid", None)
    domain_age = getattr(c, "domain_age_days", None)
    activity   = getattr(c, "days_since_last_post", None)

    if website:
        parts.append("Official website identified.")
        if ssl:
            parts.append("The site has a valid security certificate.")
        if domain_age and domain_age > 730:
            parts.append(f"The domain has been active for over {domain_age // 365} years.")
        if activity is not None and activity <= 90:
            parts.append(f"The website was updated {activity} days ago.")
    else:
        parts.append("No official website found.")

    if color == "green":
        parts.append("Summary: contractor assessed as reliable and low-risk.")
    elif color == "red":
        parts.append("Summary: contractor assessed as high-risk. Detailed review recommended.")
    else:
        parts.append("Summary: proceed with caution when working with this contractor.")

    parts.append(f"This report was generated for the entity: {name}.")

    return " ".join(parts)


def _build_de(c) -> str:
    parts: list[str] = []

    name = getattr(c, "legal_name", None) or "unbekanntes Unternehmen"
    nip  = getattr(c, "nip", "")
    scoring = getattr(c, "scoring", {}) or {}
    total   = scoring.get("total_score")
    risk    = scoring.get("risk_level", "")
    color   = scoring.get("color_code", "yellow")

    risk_map = {
        "Accepted": "Akzeptiert",
        "Verification Required": "Überprüfung erforderlich",
        "Rejected": "Abgelehnt"
    }
    risk_de = risk_map.get(risk, risk) if risk else ""

    parts.append("Überprüfung abgeschlossen.")
    if nip:
        parts.append(f"Steuernummer: {_spaced_nip(nip)}.")

    if total is not None:
        parts.append(f"Risikobewertung: {total} von 100 Punkten.")
        if risk_de:
            parts.append(f"Empfehlung: {risk_de}.")

    status_prawny = (getattr(c, "status_prawny", "") or "").upper()
    data_rozp = getattr(c, "data_rozpoczecia", None)

    if data_rozp:
        lata = _years_ago(data_rozp)
        parts.append(f"Das Unternehmen ist seit {lata} {'Jahr' if lata == 1 else 'Jahren'} tätig.")
    else:
        parts.append("Das Registrierungsdatum konnte nicht ermittelt werden.")

    if status_prawny == "AKTYWNA":
        parts.append("Registerstatus: aktiv.")
    elif status_prawny == "ZAWIESZONA":
        parts.append("Registerstatus: ruhend.")
    elif status_prawny == "WYKREŚLONA" or status_prawny == "WYKREŚLONY":
        parts.append("Registerstatus: gelöscht.")
    elif status_prawny not in ("", "NIEZNANY"):
        parts.append("Registerstatus: unbekannt.")

    vat = (getattr(c, "status_vat", "") or "").upper()
    if "CZYNNY" in vat:
        parts.append("Das Unternehmen ist ein aktiver Umsatzsteuerzahler.")
    elif "WYKREŚLONY" in vat or "WYKRESLONY" in vat:
        parts.append("Warnung: Das Unternehmen wurde aus dem Umsatzsteuerregister gelöscht.")
    elif "ZWOLNIONY" in vat:
        parts.append("Das Unternehmen ist von der Umsatzsteuer befreit.")

    whitelist = getattr(c, "rachunek_na_bialej_liscie", False)
    if whitelist:
        parts.append("Das Bankkonto des Unternehmens steht auf der weißen Liste.")

    cap = getattr(c, "share_capital", None)
    if cap is not None:
        parts.append(f"Stammkapital: {int(cap):,} Złoty.".replace(",", "."))

    bailiff = getattr(c, "has_bailiff_proceedings", None)
    if bailiff is True:
        parts.append("Warnung: Aktive Vollstreckungsverfahren erkannt.")
    elif bailiff is False:
        parts.append("Keine Vollstreckungsverfahren gefunden.")

    sanctions = getattr(c, "on_sanctions_list", None)
    if sanctions is True:
        parts.append("Warnung: Das Unternehmen steht auf einer offiziellen Sanktionsliste.")
    else:
        parts.append("Keine Einträge in Sanktionslisten gefunden.")

    website = getattr(c, "website_url", None)
    ssl     = getattr(c, "ssl_valid", None)
    domain_age = getattr(c, "domain_age_days", None)
    activity   = getattr(c, "days_since_last_post", None)

    if website:
        parts.append("Offizielle Website identifiziert.")
        if ssl:
            parts.append("Die Website verfügt über ein gültiges Sicherheitszertifikat.")
        if domain_age and domain_age > 730:
            parts.append(f"Die Domain ist seit über {domain_age // 365} Jahren aktiv.")
        if activity is not None and activity <= 90:
            parts.append(f"Die Website wurde vor {activity} Tagen aktualisiert.")
    else:
        parts.append("Keine offizielle Website gefunden.")

    if color == "green":
        parts.append("Zusammenfassung: Vertragspartner wird als zuverlässig und risikoarm eingestuft.")
    elif color == "red":
        parts.append("Zusammenfassung: Vertragspartner wird als hochriskant eingestuft. Detaillierte Prüfung empfohlen.")
    else:
        parts.append("Zusammenfassung: Bei der Zusammenarbeit mit diesem Vertragspartner ist Vorsicht geboten.")

    parts.append(f"Dieser Bericht wurde für folgendes Unternehmen erstellt: {name}.")

    return " ".join(parts)
