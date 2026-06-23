---
name: risk-report
description: Workflow for LLM risk assessment and PDF export for a contractor. Run with /risk-report <NIP or KRS number>.
disable-model-invocation: true
---

Steps to generate a contractor risk report for $ARGUMENTS (NIP or KRS number):

1. **Aggregate data** — call all services in parallel (`asyncio.gather`): KRS, CEIDG, Biała Lista VAT, VIES, transport licenses. Merge results into a single Pydantic model.

2. **Build LLM prompt** — include: company name, NIP/KRS, VAT status, financial flags, license validity, any anomalies or missing data. Instruct the LLM to respond in Polish.

3. **Call LLM with structured output** (tool use / response schema):
   ```json
   {
     "risk_level": "Niskie" | "Średnie" | "Wysokie",
     "reasoning_chain": ["step 1...", "step 2...", ...],
     "risk_flags": ["flag 1", "flag 2"]
   }
   ```

4. **Render in UI** — populate the detail view sections: Dane prawne · Finanse · Licencje · Flagi Ryzyka · Uzasadnienie AI.

5. **Export PDF** (ReportLab) — one section per page, include full reasoning chain at the end for auditability.

Use the Anthropic API (`ai/llm_client.py`) as primary. Fall back to OpenAI if configured. Never display raw API errors to the user — map them to a user-friendly Polish message.
