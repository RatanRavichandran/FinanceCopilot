from __future__ import annotations

import streamlit as st

from dy_finassist.pages import (
    contract_assistant,
    financial_dashboard,
    loan_assistant,
    persona_builder,
)

PAGES = {
    "Financial Insights": financial_dashboard.render,
    "Loan Assistant": loan_assistant.render,
    "Contract Intelligence": contract_assistant.render,
    "Persona Builder": persona_builder.render,
}


def main() -> None:  # pragma: no cover - Streamlit entry point
    st.set_page_config(page_title="dY | Financial Copilot", layout="wide")
    st.sidebar.title("Navigation")
    page_name = st.sidebar.radio("Choose a module", list(PAGES.keys()))
    st.sidebar.markdown("---")
    st.sidebar.caption("Set OPENAI_API_KEY (and optionally YOUTUBE_API_KEY) before running.")

    render = PAGES[page_name]
    render()


if __name__ == "__main__":
    main()
