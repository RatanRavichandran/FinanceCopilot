# dY | TVS Credit Financial Copilot

Reimagined version of the hackathon-winning prototype that blends financial analytics, hyper-personalised loan guidance, and contract intelligence into a single Streamlit experience.

## Highlights
- **Financial Insights** - interactive dashboard powered by personal expense data with a GPT coach on tap.
- **Loan Assistant** - combines persona context, product catalogue, EMI calculator, and explainer videos.
- **Contract Intelligence** - anonymise uploaded agreements and interrogate them safely with AI.
- **Persona Builder** - lightweight intake wizard that exports profiles for reuse across modules.
- **Clean repo layout** - notebooks, data samples, scripts, and legacy snapshots organised for GitHub.

## Repo layout
```
assets/                        # Brand and visual assets
data/
  raw/                        # XLSX samples used by dashboards
  reference/                  # Text snippets / generated artefacts
docs/
  presentations/              # Pitch decks for context
  resources/                  # Supporting legal artefacts
legacy/                       # Original hackathon scripts and dumps (read-only)
notebooks/                    # Exploratory analyses (Jupyter)
scripts/                      # Utility tooling (scrapers etc.)
src/
  streamlit_app.py            # Entry point for the multi-module app
  dy_finassist/               # Reusable modules, pages, and services
.env.example                  # Template for runtime secrets
requirements.txt
README.md
```

> The compressed archives from the original submission remain in the root for provenance. Feel free to drop them before pushing to GitHub.

## Getting started
1. **Create an environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # PowerShell
   pip install -r requirements.txt
   ```
2. **Configure secrets**
   ```bash
   copy .env.example .env
   # Add your OPENAI_API_KEY (and optionally YOUTUBE_API_KEY)
   ```
3. **Launch the UI**
   ```bash
   streamlit run src/streamlit_app.py
   ```

## Module guide
- **Financial Insights** (`financial_dashboard.py`)
  - Cleans `data/raw/personal_finance_transactions.xlsx`, builds Plotly visualisations, and pipes curated context to GPT.
  - Recent transaction table sourced from `data/raw/bank_statement_sample.xlsx`.
- **Loan Assistant** (`loan_assistant.py`)
  - Works with sample persona and catalogue text in `data/reference`. Replace these with live exports for demos.
  - Optional YouTube explainer lookup through `YOUTUBE_API_KEY`.
  - Built-in EMI calculator with validation.
- **Contract Intelligence** (`contract_assistant.py`)
  - Accepts PDF/TXT, anonymises with Presidio when available, and generates business-friendly summaries.
  - Follow-up Q&A runs against the anonymised context.
- **Persona Builder** (`persona_builder.py`)
  - Simple intake form that saves the generated persona to `data/reference/generated_user_profile.txt`.

## Data and assets
- `data/raw/` hosts anonymised Excel samples. Swap these with your own before showcasing.
- `docs/resources/` preserves the legal artefacts referenced during the hackathon (sample agreements, templates).
- `legacy/` holds untouched scripts and directories from the winning submission for comparison or rollback.

## Automation and tooling
- `scripts/scrape_loans.py` fetches loan product webpages and runs them through the LLM summariser.
  ```bash
  python scripts/scrape_loans.py https://www.tvscredit.com/loans/two-wheeler-loans/
  ```
  This requires `OPENAI_API_KEY` and internet access.

## Optional extensions
- Voice and text-to-speech capabilities from the original build are available in `legacy/scripts/preloan.py`. They can be ported back by installing `SpeechRecognition`, `gTTS`, `deep-translator`, and `pycountry`, then wiring them into the new layout.

## Next steps
- Replace the sample data with sanitised analytics from production-like sources.
- Add regression tests for the analytics layer (`src/dy_finassist/utils/analytics.py`).
- Spin up a GitHub Action to lint and deploy the Streamlit app automatically.

Happy shipping! :rocket:
