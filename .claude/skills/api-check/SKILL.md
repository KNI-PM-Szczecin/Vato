---
name: api-check
description: Reference for async API integration patterns in this project — KRS, CEIDG, Biała Lista VAT, VIES, transport licenses (GITD/ITD).
---

Patterns to follow when implementing or reviewing API service files in `services/`:

- Each API gets its own file: `services/krs_client.py`, `services/ceidg_client.py`, etc.
- All HTTP calls via `httpx.AsyncClient` inside `async` methods
- GUI triggers these via a background thread: `loop.run_coroutine_threadsafe(coro, loop)` or a `threading.Thread` wrapping `asyncio.run()`
- Each service method returns a Pydantic model from `models/` — never raw dicts or JSON
- Handle rate limits, timeouts, and 404s gracefully — partial results are valid; flag missing data explicitly
- API keys and base URLs loaded from `.env` via `python-dotenv`

| Service file | API endpoint |
|---|---|
| `krs_client.py` | KRS API (`api.rejestr.io` or official KRS REST) |
| `ceidg_client.py` | CEIDG public REST API |
| `vat_client.py` | `https://wl-api.mf.gov.pl/` (Biała Lista) |
| `vies_client.py` | EU VIES REST (`ec.europa.eu/taxation_customs/vies/`) |
| `transport_client.py` | GITD/ITD public registry |

When implementing a new service: write the Pydantic model first, then the client, then wire it into the controller.
