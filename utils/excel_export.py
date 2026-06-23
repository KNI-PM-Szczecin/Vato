import pandas as pd
from models.contractor import ScoreResult


def export_results(results: list[ScoreResult], path: str) -> None:
    """Export results to Excel — summary sheet + one sheet per NIP."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary_data = [
            {
                "NIP": r.nip,
                "Score": r.total,
                "Max": 40,
                "Legal Status": r.legal_status,
                "Experience": r.experience,
                "VAT Taxes": r.vat_taxes,
                "Stability": r.stability,
                "Recommendation": r.risk_level.value,
            }
            for r in results
        ]
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Summary", index=False)

        for r in results:
            sheet_name = r.nip[:31]
            detail_data = [{"Details": line} for line in r.details]
            detail_data.append({"Details": f"RESULT: {r.total}/40 — {r.risk_level.value}"})
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
            
            # Akceptuj NIPy polskie (10 cyfr) oraz europejskie (2 litery + cyfry/litery)
            if re.match(r"^[A-Z]{2}[A-Z0-9]{2,14}$", clean) or (clean.isdigit() and len(clean) == 10):
                cleaned_nips.append(clean)
        return cleaned_nips
    except Exception as e:
        print(f"Błąd podczas czytania pliku Excel: {e}")
        return []
