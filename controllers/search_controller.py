"""
Orchestrates the full verification flow for one or more NIPs.
Runs async data fetching in a background thread so the GUI never freezes.
"""
import asyncio
import threading
from typing import Callable

from models.contractor import ContractorData, ScoreResult
from services import entity_detector, krs_client, ceidg_client, vat_client
from scoring.evaluator import evaluate_contractor


async def _fetch_and_score(nip: str, bank_account: str | None) -> ScoreResult:
    data = ContractorData(nip=nip, bank_account=bank_account)

    # Identify entity type (KRS public API, no key needed) → fetch legal status
    entity_type = await entity_detector.detect(nip)
    if entity_type == "KRS":
        data = await krs_client.enrich(data)
    else:
        data = await ceidg_client.enrich(data)

    # Always check VAT whitelist (public, no key needed)
    data = await vat_client.enrich(data)

    return evaluate_contractor(data)


async def _run_all(nips: list[tuple[str, str | None]]) -> list[ScoreResult]:
    tasks = [_fetch_and_score(nip, account) for nip, account in nips]
    return await asyncio.gather(*tasks, return_exceptions=False)


def verify_nips(
    nips: list[tuple[str, str | None]],
    on_done: Callable[[list[ScoreResult]], None],
    on_error: Callable[[Exception], None],
    app_after: Callable,
) -> None:
    """
    Start async verification in a background thread.
    Calls on_done(results) on the main thread when finished.
    app_after is ctk root.after — used to schedule callback on main thread.
    """
    def _run():
        try:
            results = asyncio.run(_run_all(nips))
            app_after(0, lambda: on_done(results))
        except Exception as exc:
            app_after(0, lambda: on_error(exc))

    threading.Thread(target=_run, daemon=True).start()
