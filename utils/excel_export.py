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
