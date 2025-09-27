# Architecture Overview

## Application layers
- **Streamlit shell (`src/streamlit_app.py`)** - handles navigation and theming for the four experience modules.
- **Pages (`src/dy_finassist/pages/`)** - feature-specific views composed of widgets, charts, and AI workflows.
- **Services (`src/dy_finassist/services/`)** - adapters around third-party APIs (OpenAI, YouTube).
- **Utilities (`src/dy_finassist/utils/`)** - data loaders, analytics helpers, and PDF/text processing glue.

## Data flow
1. Sample Excel/TXT artefacts live under `data/`. They are loaded via utilities with caching so repeated reads are cheap.
2. The analytics module standardises spending data (type casting, outlier removal) before the dashboard renders charts.
3. AI-dependent flows share a single entry point (`services.llm.chat`) that enforces environment variables and raises meaningful errors when keys are missing.
4. Summaries and generated personas are written back to `data/reference/` so they can be versioned with the repo.

## External integrations
- **OpenAI** (`OPENAI_API_KEY`, `OPENAI_MODEL`) for contract summaries, financial advice, and persona generation.
- **YouTube Data API v3** (`YOUTUBE_API_KEY`) for contextual explainer videos.
- **Presidio** (optional) for anonymising uploaded contracts.

## Extensibility hooks
- Add more Streamlit modules by dropping new files under `src/dy_finassist/pages` and wiring them into `PAGES` in `streamlit_app.py`.
- Additional datasets can plug into `utils/data.py`; downstream modules will automatically benefit from caching.
- Voice/TTS integration can live in a new service module that toggles on via `ENABLE_VOICE_FEATURES`.
