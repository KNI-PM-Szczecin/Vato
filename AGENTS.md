# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Desktop app for logistics analysts to verify contractor credibility. Hackathon Morski challenge: "Automatyzacja procesu oceny wiarygodności kontrahentów". Aggregates data from Polish/EU registries and uses an LLM to generate an auditable risk assessment.

## Tech Stack

- **Language**: Python 3.12.0
- **GUI**: CustomTkinter
- **Async**: `asyncio` + `threading` — background threads run async coroutines so the GUI never freezes
- **LLM**: Anthropic Claude API (primary), OpenAI optional
- **PDF export**: ReportLab (or FPDF2)
- **Architecture**: MVC/MVVM — strict separation between GUI, business logic, and network layer

## Architecture

```
views/         # CustomTkinter widgets/windows only — no business logic here
controllers/   # (or viewmodels/) state management, wires views to services
services/      # one file per external API; all calls are async
models/        # Pydantic data models shared across layers
ai/            # LLM client and prompt templates
utils/         # PDF generation, phishing validation, helpers
```

## External APIs

All calls must be async (`httpx.AsyncClient`). Each service returns a Pydantic model, never raw dicts. Handle partial failures gracefully — show what's available, flag what failed.

| API | Purpose |
|-----|---------|
| KRS | Company registry (spółki) |
| CEIDG | Sole trader registry (JDG) |
| Biała Lista VAT (`wl-api.mf.gov.pl`) | VAT whitelist |
| VIES | EU VAT cross-border verification |
| GITD/ITD | Transport license registry |

## LLM Risk Analysis

Pass aggregated structured data to the LLM and request back (via structured output / tool use):
- `risk_level`: `"Niskie"` | `"Średnie"` | `"Wysokie"`
- `reasoning_chain`: list of reasoning steps in Polish (must be human-readable and auditable)
- `risk_flags`: list of specific issues detected

## Key Libraries

```
customtkinter
httpx
anthropic
openai          # optional
reportlab
python-dotenv
pydantic
```

## Security

- All secrets in `.env`, loaded via `python-dotenv` — never hardcoded or committed
- Validate contact data (email, phone, URLs) against phishing patterns before display
- Sanitize any data passed into PDF templates

## PDF Report Sections

Detail view and exported PDF must include: **Dane prawne · Finanse · Licencje · Flagi Ryzyka** plus the full LLM reasoning chain.

## Skills

- `/architecture` — propose project structure, directory layout, and `requirements.txt`
- `/api-check` — reference for async API integration patterns used in this project
- `/risk-report` — workflow for LLM risk assessment and PDF export
