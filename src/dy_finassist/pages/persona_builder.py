from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import streamlit as st

from ..config import REFERENCE_DATA_DIR
from ..services.llm import ChatMessage, LLMUnavailable, chat

PROFILE_OUTPUT = REFERENCE_DATA_DIR / "generated_user_profile.txt"


def _save_profile(snapshot: str) -> Path:
    PROFILE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_OUTPUT.write_text(snapshot, encoding="utf-8")
    return PROFILE_OUTPUT


def render() -> None:  # pragma: no cover - Streamlit entry point
    st.title("Persona Intake Wizard")
    st.write(
        "Capture prospect details in minutes and generate a reusable persona file for other journeys."
    )

    with st.form("persona_form"):
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=18, max_value=80, value=30)
            employment_status = st.selectbox(
                "Employment status",
                ["Salaried", "Self-employed", "Business owner", "Student", "Retired"],
            )
            monthly_income = st.selectbox(
                "Monthly income range",
                ["Below INR 25,000", "INR 25,000 - 75,000", "INR 75,000 - 150,000", "Above INR 150,000"],
            )
        with col2:
            city = st.text_input("City", value="Chennai")
            credit_history = st.selectbox("Credit history awareness", ["Limited", "Average", "Strong"])
            primary_goal = st.text_input("Primary loan goal", value="Upgrade to a new scooter")

        existing_loans = st.text_area("Existing loans or debts", value="Two-wheeler loan outstanding ~INR 40,000")
        collateral = st.selectbox("Collateral available", ["None", "Vehicle", "Property", "Investments"])
        urgency = st.selectbox(
            "Urgency",
            ["Immediate", "Within a month", "2-3 months", "Exploratory"],
        )
        submit = st.form_submit_button("Generate persona")

    if submit:
        answers: Dict[str, str | int] = {
            "age": age,
            "employment_status": employment_status,
            "monthly_income": monthly_income,
            "city": city,
            "credit_history": credit_history,
            "primary_goal": primary_goal,
            "existing_loans": existing_loans,
            "collateral": collateral,
            "urgency": urgency,
        }
        try:
            persona = chat(
                [
                    ChatMessage(
                        role="system",
                        content=(
                            "You are a TVS Credit relationship manager. Turn the intake answers into a detailed persona"
                            " covering demographics, financial posture, risk outlook, and tone of voice to use in"
                            " customer conversations."
                        ),
                    ),
                    ChatMessage(role="user", content=json.dumps(answers, default=str)),
                ],
                max_tokens=450,
                temperature=0.5,
            )
        except LLMUnavailable:
            persona = "Set OPENAI_API_KEY to enable persona generation."
        except Exception as exc:  # noqa: BLE001
            persona = f"Persona generation failed: {exc}"

        st.subheader("Generated persona")
        st.markdown(persona)

        saved_path = _save_profile(persona)
        st.success(f"Persona snapshot saved to {saved_path.relative_to(Path.cwd())}")


__all__ = ["render"]
