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
    return _build_pl(contractor) if lang == "pl" else _build_en(contractor)


def _years_ago(d: date) -> int:
    return date.today().year - d.year


def _build_pl(c) -> str:
    parts: list[str] = []

    name = getattr(c, "legal_name", None) or "nieznana firma"
    nip  = getattr(c, "nip", "")
    scoring = getattr(c, "scoring", {}) or {}
    total   = scoring.get("total_score")
    risk    = scoring.get("risk_level", "")
    color   = scoring.get("color_code", "yellow")

    # ── intro ──────────────────────────────────────────────────────────────────
    parts.append(f"Weryfikacja zakończona.")
    parts.append(f"Podmiot: {name}.")
    if nip:
        parts.append(f"Numer NIP: {nip}.")

    # ── scoring result ─────────────────────────────────────────────────────────
    if total is not None:
        parts.append(f"Wynik oceny ryzyka: {total} punktów na sto możliwych.")
        if risk:
            parts.append(f"Rekomendacja: {risk}.")

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
    elif status_prawny not in ("", "NIEZNANY"):
        parts.append(f"Status w rejestrze: {status_prawny.lower()}.")

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
    parts.append(f"Entity: {name}.")
    if nip:
        parts.append(f"Tax ID: {nip}.")

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

    vat = (getattr(c, "status_vat", "") or "").upper()
    if "CZYNNY" in vat:
        parts.append("The company is an active VAT payer.")
    elif "WYKREŚLONY" in vat or "WYKRESLONY" in vat:
        parts.append("Warning: the company has been removed from the VAT register.")

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
    if website:
        parts.append("Official website identified.")
        if ssl:
            parts.append("The site has a valid security certificate.")
    else:
        parts.append("No official website found.")

    if color == "green":
        parts.append("Summary: contractor assessed as reliable and low-risk.")
    elif color == "red":
        parts.append("Summary: contractor assessed as high-risk. Detailed review recommended.")
    else:
        parts.append("Summary: proceed with caution when working with this contractor.")

    return " ".join(parts)
