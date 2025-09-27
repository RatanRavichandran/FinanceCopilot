from __future__ import annotations

import json
from typing import Dict

import streamlit as st

from ..services.llm import ChatMessage, LLMUnavailable, chat
from ..utils import analytics
from ..utils.data import (
    DataNotFound,
    load_bank_statement,
    load_personal_expenses,
)


def _format_currency(value: float) -> str:
    return f"INR{value:,.2f}"


def render() -> None:  # pragma: no cover - Streamlit entry point
    st.title("Financial Insights Dashboard")

    try:
        raw_df = load_personal_expenses()
        expenses = analytics.prepare_expense_dataframe(raw_df)
    except DataNotFound as exc:
        st.error(str(exc))
        return

    summary = analytics.summarise_expenses(expenses)
    categories = analytics.high_spending_categories(expenses)

    st.write(
        "This view helps you explore spending trends, spot anomalies, and chat with an AI for bespoke insights."
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Total spend", _format_currency(summary.total_spending))
    col2.metric("Average monthly spend", _format_currency(summary.avg_monthly_spending))
    col3.metric("Average weekly spend", _format_currency(summary.avg_weekly_spending))

    min_month = int(expenses["Billing_date"].dt.month.min())
    max_month = int(expenses["Billing_date"].dt.month.max())
    month_range = st.slider(
        "Select month range",
        min_value=min_month,
        max_value=max_month,
        value=(min_month, max_month),
    )

    chart_col, insight_col = st.columns((2, 1))
    with chart_col:
        st.subheader("Category spend")
        st.plotly_chart(analytics.build_category_spend_chart(expenses), use_container_width=True)

        st.subheader("Spending trend")
        st.plotly_chart(
            analytics.build_spend_trend_chart(expenses, month_range=month_range),
            use_container_width=True,
        )

        st.subheader("Payment options breakdown")
        st.plotly_chart(analytics.build_payment_choice_chart(expenses), use_container_width=True)

    with insight_col:
        st.subheader("High spend categories")
        if categories:
            for name, value in categories.items():
                st.write(f"- {name}: {_format_currency(value)}")
        else:
            st.write("No high-spend categories above the configured threshold.")

        st.divider()
        st.subheader("Recent transactions")
        try:
            bank_df = load_bank_statement().head(5)
            st.dataframe(bank_df[["Date", "Description", "Amount"]], hide_index=True)
        except (DataNotFound, KeyError):  # fallback if optional columns differ
            try:
                st.dataframe(load_bank_statement().head(5), hide_index=True)
            except DataNotFound:
                st.info("Bank statement sample not available.")

    st.divider()

    st.header("Chat with your financial assistant")
    st.caption("Summaries are generated from the dataset above; no transaction data leaves your machine unless OpenAI is enabled.")

    if "financial_chat" not in st.session_state:
        st.session_state.financial_chat = []

    for message in st.session_state.financial_chat:
        role = "You" if message["role"] == "user" else "Assistant"
        st.markdown(f"**{role}:** {message['content']}")

    user_prompt = st.text_input("Ask a question about your spending")

    if user_prompt:
        st.session_state.financial_chat.append({"role": "user", "content": user_prompt})
        try:
            context = ChatMessage(
                role="system",
                content=json.dumps(
                    {
                        "total_spending": summary.total_spending,
                        "average_monthly_spending": summary.avg_monthly_spending,
                        "average_weekly_spending": summary.avg_weekly_spending,
                        "high_spend_categories": categories,
                    },
                    default=float,
                ),
            )
            messages = [
                ChatMessage(
                    role="system",
                    content=(
                        "You are a helpful financial coach. Provide actionable insights without disclosing exact"
                        " rupee values unless explicitly requested."
                    ),
                ),
                context,
                *[ChatMessage(**msg) for msg in st.session_state.financial_chat],
            ]
            assistant_reply = chat(messages, max_tokens=400)
        except LLMUnavailable as exc:
            assistant_reply = (
                "LLM configuration missing. Set OPENAI_API_KEY to enable AI responses."
            )
        except Exception as exc:  # noqa: BLE001
            assistant_reply = f"Something went wrong while generating the response: {exc}"

        st.session_state.financial_chat.append({"role": "assistant", "content": assistant_reply})
        st.experimental_rerun()


__all__ = ["render"]
