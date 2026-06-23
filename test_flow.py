"""
Szybki test flow weryfikacji bez GUI.
Uruchom: python test_flow.py [NIP]
Domyślnie testuje kilka znanych NIPs.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from services.entity_detector import detect
from services.krs_client import fetch_krs_data
from services.ceidg_client import fetch_ceidg_data
from services.vat_client import fetch_vat_data
from models.contractor import ContractorData
from scoring.evaluator import evaluate_contractor
from datetime import date


TEST_NIPS = [
    # (NIP, opis, typ)
    ("7740001454", "PKN Orlen S.A. — duża spółka", "KRS"),
    ("5213003700", "Allegro.pl sp. z o.o.", "KRS"),
]


async def test_nip(nip: str, opis: str = ""):
    print(f"\n{'='*55}")
    print(f"NIP: {nip}  {opis}")
    print(f"{'='*55}")

    # 1. Detekcja typu
    entity_type = await detect(nip)
    print(f"[1] Typ podmiotu:  {entity_type}")

    # 2. Dane rejestrowe
    if entity_type == "KRS":
        reg_data = await fetch_krs_data(nip)
    else:
        reg_data = await fetch_ceidg_data(nip)
    print(f"[2] Dane rej.:     {reg_data}")

    # 3. VAT / Biała Lista
    vat_data = await fetch_vat_data(nip)
    print(f"[3] VAT:           {vat_data}")

    # 4. Scoring
    data = ContractorData(nip=nip, **reg_data, **vat_data)
    result = evaluate_contractor(data)
    print(f"[4] Wynik:         {result.total}/40  →  {result.risk_level.value}")
    for d in result.szczegoly:
        print(f"       • {d}")


async def main():
    nips_to_test = sys.argv[1:] if len(sys.argv) > 1 else None

    if nips_to_test:
        for nip in nips_to_test:
            await test_nip(nip.replace("-", "").replace(" ", ""))
    else:
        for nip, opis, _ in TEST_NIPS:
            await test_nip(nip, opis)


if __name__ == "__main__":
    asyncio.run(main())
