import pandas as pd
from models.contractor import ScoreResult
def export_results(results: list[ScoreResult], path: str) -> None:
    """Export results to Excel — one sheet per NIP, plus a summary sheet."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        # Summary sheet
        summary_data = [
            {
                "NIP": r.nip,
                "Wynik": r.total,
                "Maks": 40,
                "Status prawny": r.legal_status,
                "Doświadczenie": r.experience,
                "Podatki VAT": r.vat_taxes,
                "Stabilność": r.stability,
                "Rekomendacja": r.risk_level.value,
            }
            for r in results
        ]
        pd.DataFrame(summary_data).to_excel(writer, sheet_name="Podsumowanie", index=False)
        # Individual sheet per NIP
        for r in results:
            sheet_name = r.nip[:31]  # Excel sheet name limit
            detail_data = [{"Kategoria": line} for line in r.details]
            detail_data.append({"Kategoria": f"WYNIK: {r.total}/40 — {r.risk_level.value}"})
            pd.DataFrame(detail_data).to_excel(writer, sheet_name=sheet_name, index=False)
