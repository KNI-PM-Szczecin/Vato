import pandas as pd
from models.contractor import ScoreResult

def strip_polish_chars(text: str) -> str:
    """Replaces Polish characters with their ASCII equivalents to keep export file content standardized."""
    if not isinstance(text, str):
        return text
    mapping = {
        'ą': 'a', 'Ą': 'A',
        'ć': 'c', 'Ć': 'C',
        'ę': 'e', 'Ę': 'E',
        'ł': 'l', 'Ł': 'L',
        'ń': 'n', 'Ń': 'N',
        'ó': 'o', 'Ó': 'O',
        'ś': 's', 'Ś': 'S',
        'ź': 'z', 'Ź': 'Z',
        'ż': 'z', 'Ż': 'Z'
    }
    for pol, eng in mapping.items():
        text = text.replace(pol, eng)
    return text

def export_results(results: list, path: str) -> None:
    """Export results to Excel — summary sheet + one sheet per NIP, free of Polish characters."""
    summary_data = []
    for r in results:
        is_contractor = hasattr(r, 'scoring') and isinstance(r.scoring, dict)
        nip = getattr(r, 'nip', '---')
        
        if is_contractor:
            score = r.scoring.get('total_score', 0)
            max_score = 100
            rec = r.scoring.get('risk_level', 'NIEZNANY')
            justifications = r.scoring.get('justifications', [])
        else:
            score = getattr(r, 'total', 0)
            max_score = 40
            rec = getattr(r, 'risk_level', None)
            rec = rec.value if rec else 'NIEZNANY'
            justifications = getattr(r, 'details', [])
            
        website = getattr(r, 'website_url', None) or "NIE ODNALEZIONO"
        ssl = "TAK" if getattr(r, 'ssl_valid', False) else "NIE"
        age = getattr(r, 'domain_age_days', None)
        domain_age = f"{age} dni" if age is not None else "BRAK DANYCH"
        posts = getattr(r, 'days_since_last_post', None)
        activity = f"Ostatni wpis {posts} dni temu" if posts is not None else "BRAK DANYCH"
        nip_match = "TAK" if getattr(r, 'website_nip_matched', False) else "NIE"

        row = {
            "NIP": nip,
            "Nazwa firmy": strip_polish_chars(getattr(r, 'legal_name', '---') if is_contractor else '---'),
            "Wynik": score,
            "Wynik Max": max_score,
            "Rekomendacja": strip_polish_chars(rec),
            "Strona WWW": strip_polish_chars(website),
            "Szyfrowanie SSL": strip_polish_chars(ssl),
            "Wiek domeny": strip_polish_chars(domain_age),
            "Ostatnia aktywnosc (RSS)": strip_polish_chars(activity),
            "Zgodnosc NIP na stronie": strip_polish_chars(nip_match)
        }
        summary_data.append(row)
        
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

        for r in results:
            nip = getattr(r, 'nip', '---')
            sheet_name = nip[:31]
            is_contractor = hasattr(r, 'scoring') and isinstance(r.scoring, dict)
            
            if is_contractor:
                score = r.scoring.get('total_score', 0)
                max_score = 100
                rec = r.scoring.get('risk_level', 'NIEZNANY')
                justifications = r.scoring.get('justifications', [])
            else:
                score = getattr(r, 'total', 0)
                max_score = 40
                rec = getattr(r, 'risk_level', None)
                rec = rec.value if rec else 'NIEZNANY'
                justifications = getattr(r, 'details', [])
                
            detail_data = []
            
            def add_row(field_name, value):
                detail_data.append({
                    "Nazwa pola": strip_polish_chars(field_name), 
                    "Wartosc": strip_polish_chars(str(value)) if value is not None else ""
                })
                
            add_row("NIP", nip)
            if is_contractor:
                add_row("Nazwa firmy", getattr(r, 'legal_name', '---'))
                add_row("Status prawny", getattr(r, 'status_prawny', 'NIEZNANY'))
                add_row("Status VAT", getattr(r, 'status_vat', 'NIEZNANY'))
                add_row("Biala lista", "TAK" if getattr(r, 'rachunek_na_bialej_liscie', False) else "NIE")
            
            add_row("Strona WWW", getattr(r, 'website_url', None) or "NIE ODNALEZIONO")
            add_row("Szyfrowanie SSL/TLS", "TAK" if getattr(r, 'ssl_valid', False) else "NIE")
            
            age = getattr(r, 'domain_age_days', None)
            add_row("Wiek domeny", f"{age} dni" if age is not None else "BRAK DANYCH")
            
            posts = getattr(r, 'days_since_last_post', None)
            add_row("Ostatnia aktywnosc (RSS)", f"Ostatni wpis {posts} dni temu" if posts is not None else "BRAK DANYCH")
            
            add_row("Zgodnosc NIP na stronie", "TAK" if getattr(r, 'website_nip_matched', False) else "NIE")
            add_row("WYNIK KONCOWY", f"{score}/{max_score}")
            add_row("REKOMENDACJA RYZYKA", rec)
            
            add_row("", "")
            add_row("Uzasadnienie szczegolowe:", "")
            
            for j in justifications:
                add_row("•", j)
                
            pd.DataFrame(detail_data).to_excel(writer, sheet_name=sheet_name, index=False)

def read_nips_from_excel(path: str) -> list[str]:
    """Read a list of NIPs from an Excel file (.xlsx). Looks for a column named 'NIP' or takes the first column."""
    try:
        df = pd.read_excel(path, engine="openpyxl")
        nip_col = next((col for col in df.columns if str(col).strip().upper() == "NIP"), None)
        
        if nip_col:
            nips = df[nip_col].dropna().astype(str).tolist()
        else:
            nips = df.iloc[:, 0].dropna().astype(str).tolist()
            
        cleaned_nips = []
        import re
        for nip in nips:
            clean = str(nip).replace(" ", "").replace("-", "").upper()
            if clean.endswith(".0"):
                clean = clean[:-2]
            
            if re.match(r"^[A-Z]{2}[A-Z0-9]{2,14}$", clean) or (clean.isdigit() and len(clean) == 10):
                cleaned_nips.append(clean)
        return cleaned_nips
    except Exception as e:
        print(f"Błąd podczas czytania pliku Excel: {e}")
        return []
