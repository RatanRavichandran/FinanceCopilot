from __future__ import annotations

import math
from typing import Optional

import streamlit as st

from ..services.llm import ChatMessage, LLMUnavailable, chat
from ..services.youtube import YouTubeUnavailable, search_video
from ..utils.data import DataNotFound, load_loans_info, load_user_profile


def _calculate_emi(principal: float, annual_rate: float, tenure_years: int) -> float:
    if principal <= 0 or annual_rate <= 0 or tenure_years <= 0:
        raise ValueError("Principal, interest rate and tenure must be greater than zero.")

    monthly_rate = annual_rate / (12 * 100)
    tenure_months = tenure_years * 12
    numerator = principal * monthly_rate * (1 + monthly_rate) ** tenure_months
    denominator = (1 + monthly_rate) ** tenure_months - 1
    return numerator / denominator


def render() -> None:  # pragma: no cover - Streamlit entry point
    st.title("Hyper-personalised Loan Assistant")
    st.write(
        "Blend customer profiling, product intelligence, and conversational support to guide users to the right loan."
    )

    try:
        base_profile = load_user_profile()
    except DataNotFound:
        base_profile = ""

    try:
        base_loans_info = load_loans_info()
    except DataNotFound:
        base_loans_info = ""

    with st.expander("Reference data loaded from repo"):
        st.caption("These samples power the default experience; replace or edit them to suit your demo.")
        st.text_area("User profile sample", base_profile, height=200)
        st.text_area("Loan catalogue sample", base_loans_info, height=200)

    st.divider()

    profile = st.text_area("Paste the applicant profile", base_profile, height=200)
    loan_choice = st.text_input("Loan type of interest", "Two-wheeler loan")
    catalogue = st.text_area("Paste your loan product information", base_loans_info, height=200)

    if "loan_guidance" not in st.session_state:
        st.session_state.loan_guidance = None
    if "loan_video" not in st.session_state:
        st.session_state.loan_video = None

    col1, col2 = st.columns((1.5, 1))

    with col1:
        if st.button("Generate tailored guidance"):
            try:
                system_prompt = ChatMessage(
                    role="system",
                    content=(
                        "You are TVS Credit's digital loan specialist. Analyse the customer profile,"
                        " match it with product data, and respond with: 1) fit analysis for the requested"
                        f" {loan_choice}; 2) comparative alternatives; 3) risk flags; 4) next best actions."
                    ),
                )
                user_prompt = ChatMessage(
                    role="user",
                    content=(
                        f"Customer profile:\n{profile}\n\nLoan catalogue:\n{catalogue}\n\n"
                        f"Focus loan: {loan_choice}."
                    ),
                )
                st.session_state.loan_guidance = chat(
                    [system_prompt, user_prompt],
                    max_tokens=650,
                    temperature=0.4,
                )
            except LLMUnavailable:
                st.session_state.loan_guidance = "Set OPENAI_API_KEY to enable guidance generation."
            except Exception as exc:  # noqa: BLE001
                st.session_state.loan_guidance = f"Could not generate guidance: {exc}"

        if st.session_state.loan_guidance:
            st.subheader("Guidance")
            st.markdown(st.session_state.loan_guidance)

    with col2:
        st.subheader("Loan explainer video")

        if st.button("Find a YouTube explainer"):
            try:
                result = search_video(f"TVS Credit {loan_choice} loan")
            except YouTubeUnavailable:
                result = None
                st.warning("Set YOUTUBE_API_KEY to enable YouTube search.")
            except Exception as exc:  # noqa: BLE001
                result = None
                st.error(f"Failed to fetch video: {exc}")

            st.session_state.loan_video = result

        if st.session_state.loan_video:
            title, url = st.session_state.loan_video
            st.caption(title)
            st.video(url)

        st.divider()
        st.subheader("EMI calculator")
        principal = st.number_input("Loan amount", value=500_000.0, min_value=1_000.0, step=10_000.0)
        rate = st.number_input("Interest rate (% per annum)", value=8.5, min_value=0.1, step=0.1)
        tenure = st.slider("Tenure (years)", min_value=1, max_value=30, value=5)

        if st.button("Calculate EMI"):
            try:
                emi = _calculate_emi(principal, rate, tenure)
                st.success(f"Estimated monthly EMI: INR{emi:,.2f}")
            except ValueError as exc:
                st.error(str(exc))

    st.divider()

    st.header("Loan support chat")
    st.caption("The assistant uses the profile and catalogue context provided above.")

    if "loan_chat" not in st.session_state:
        st.session_state.loan_chat = []

    for message in st.session_state.loan_chat:
        role = "You" if message["role"] == "user" else "Assistant"
        st.markdown(f"**{role}:** {message['content']}")

    user_message = st.chat_input("Ask anything about the loan journey")

    if user_message:
        st.session_state.loan_chat.append({"role": "user", "content": user_message})
        try:
            context_messages = [
                ChatMessage(
                    role="system",
                    content="You are a hyper-personalised loan advisor for TVS Credit.",
                ),
                ChatMessage(role="system", content=f"Customer profile: {profile}"),
                ChatMessage(role="system", content=f"Loan catalogue: {catalogue}"),
            ] + [ChatMessage(**msg) for msg in st.session_state.loan_chat]
            assistant_reply = chat(context_messages, max_tokens=500)
        except LLMUnavailable:
            assistant_reply = "Set OPENAI_API_KEY to enable conversational guidance."
        except Exception as exc:  # noqa: BLE001
            assistant_reply = f"We ran into an issue answering this: {exc}"

        st.session_state.loan_chat.append({"role": "assistant", "content": assistant_reply})
        st.experimental_rerun()


__all__ = ["render"]
