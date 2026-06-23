# AGENTS.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Vato** — desktop app for logistics analysts to verify contractor credibility. Hackathon Morski: "Automatyzacja procesu oceny wiarygodności kontrahentów". Aggregates data from Polish/EU registries, scores contractors (40-point algorithm), and exports reports.

## Tech Stack

- **Language**: Python 3.12
- **GUI**: CustomTkinter
- **Async**: `asyncio` + `threading` — background threads run async coroutines so the GUI never freezes
- **PDF export**: ReportLab
- **Excel export**: pandas + openpyxl (one sheet per NIP, merge multiple into one file)
- **Email**: smtplib (send reports as attachments)
- **TTS**: ElevenLabs API (accessibility — reads report aloud)
- **Architecture**: MVC — strict separation between GUI, business logic, and network layer

## Architecture

```
views/         # CustomTkinter widgets/windows only — no business logic
controllers/   # state management, wires views to services + scoring
services/      # one file per external API; all calls are async httpx
models/        # Pydantic data models shared across layers
scoring/       # 4-category 40-point contractor evaluation algorithm
utils/         # PDF, Excel, email, TTS helpers
```

## Key Workflow

1. User enters one or more NIPs (10–15 at once supported)
2. REGON identifies each NIP as spółka (→ KRS) or JDG (→ CEIDG)
3. Services fetch data async in parallel per NIP
4. `scoring/evaluator.py` scores each contractor (max 40 pts)
5. Results shown in GUI + exported to Excel (one sheet/NIP, optional merge) and/or PDF
6. Optional: email report as attachment; TTS reads summary aloud

## Scoring Categories (from `api_test.py`)

| # | Category | Max pts |
|---|----------|---------|
| 1 | Status prawny | 10 |
| 2 | Doświadczenie | 10 |
| 3 | Podatki VAT / Biała Lista | 10 |
| 4 | Stabilność | 10 |

Threshold: ≥20 → akceptacja, ≥0 → dodatkowa weryfikacja, <0 → odrzucenie.

## External APIs

All HTTP calls via `httpx.AsyncClient`. Each service returns a Pydantic model. Handle partial failures gracefully — show available data, flag what failed.

| API | Key needed | Purpose |
|-----|-----------|---------|
| REGON/BIR1 | `REGON_API_KEY` | Identify NIP type (spółka vs JDG) |
| KRS | none | Legal status of spółki |
| CEIDG | `CEIDG_API_KEY` | Legal status of JDG |
| Biała Lista VAT | none | VAT status + bank account check |
| VIES | none | EU VAT verification (optional) |
| ElevenLabs | `ELEVENLABS_API_KEY` | TTS for accessibility |

## Key Libraries

```
customtkinter>=5.2.0
httpx>=0.27.0
pydantic>=2.7.0
python-dotenv>=1.0.0
reportlab>=4.2.0
pandas>=2.2.0
openpyxl>=3.1.0
elevenlabs>=1.0.0
requests>=2.32.0
```

## Security

- All secrets in `.env`, loaded via `python-dotenv` — never hardcoded or committed
- `.env` is gitignored

## Export Formats

- **Excel**: one `.xlsx` sheet per NIP; if multiple NIPs, offer merged workbook
- **PDF**: sections — Dane prawne · Finanse · Status VAT · Stabilność · Wynik
- **Email**: send Excel/PDF as attachment via smtplib

## Skills

- `/architecture` — project structure and `requirements.txt`
- `/api-check` — async API integration patterns for this project
