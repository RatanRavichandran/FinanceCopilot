from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd
import plotly.express as px
from scipy import stats


@dataclass(slots=True)
class ExpenseSummary:
    total_spending: float
    avg_monthly_spending: float
    avg_weekly_spending: float


def prepare_expense_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()

    drop_cols = [
        "Conversion rate from source/accounting currency to ils",
        "comments",
        "Labeling",
        "Discount_club",
        "Discount_key",
    ]
    df = df.drop(columns=[col for col in drop_cols if col in df.columns])

    if "Original_transaction_amount" in df.columns and "debit_amount" in df.columns:
        mismatched = df[df["debit_amount"] != df["Original_transaction_amount"]]
        if not mismatched.empty:
            df.loc[mismatched.index, "debit_amount"] = df.loc[mismatched.index, "Original_transaction_amount"]
        df = df.drop(columns=["Original_transaction_amount"], errors="ignore")

    df = df.drop(columns=["Original_transaction_currency"], errors="ignore")

    for col in ["transaction_date", "Billing_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "Name_of_the_business" in df.columns:
        df["Name_of_the_business"] = df["Name_of_the_business"].replace(
            {"Transfer in BIT BIP": "Transfer in BIT"}
        )

    if "debit_amount" in df.columns:
        df = df.dropna(subset=["debit_amount"])
        df["debit_amount"] = df["debit_amount"].astype(float)

        z_scores = stats.zscore(df["debit_amount"])
        if not isinstance(z_scores, pd.Series):
            z_scores = pd.Series(z_scores, index=df.index)
        df = df.loc[z_scores.abs() <= 3]

    df = df.sort_values(by="transaction_date")
    df = df.reset_index(drop=True)
    return df


def build_category_spend_chart(df: pd.DataFrame):
    grouped = df.groupby("category")["debit_amount"].sum().sort_values()
    fig = px.bar(
        grouped,
        x=grouped.index,
        y=grouped.values,
        labels={"x": "Category", "y": "Money Spent"},
    )
    fig.update_traces(hovertemplate="Category: %{x}<br>Money Spent: INR%{y:.2f}")
    return fig


def build_spend_trend_chart(df: pd.DataFrame, month_range: Optional[tuple[int, int]] = None):
    billing_month = df["Billing_date"].dt.month
    filtered = df
    if month_range is not None:
        filtered = df[(billing_month >= month_range[0]) & (billing_month <= month_range[1])]

    grouped = filtered.groupby(filtered["Billing_date"].dt.to_period("M"))["debit_amount"].sum()
    grouped.index = grouped.index.to_timestamp()

    fig = px.line(
        x=grouped.index,
        y=grouped.values,
        labels={"x": "Month", "y": "Total money spent"},
    )
    fig.update_xaxes(dtick="M1", tickformat="%b %Y")
    return fig


def build_payment_choice_chart(df: pd.DataFrame):
    counts = df["The_way_the_transaction_is_carried_out"].value_counts()
    return px.pie(counts, values=counts.values, names=counts.index)


def summarise_expenses(df: pd.DataFrame) -> ExpenseSummary:
    billing = df["Billing_date"].dt.to_period("M")
    weekly = df["Billing_date"].dt.to_period("W")

    total = df["debit_amount"].sum()
    avg_month = df.groupby(billing)["debit_amount"].sum().mean()
    avg_week = df.groupby(weekly)["debit_amount"].sum().mean()

    return ExpenseSummary(total, float(avg_month or 0), float(avg_week or 0))


def high_spending_categories(df: pd.DataFrame, threshold_ratio: float = 0.2) -> Dict[str, float]:
    total = df["debit_amount"].sum()
    grouped = df.groupby("category")["debit_amount"].sum()
    return grouped[grouped > threshold_ratio * total].to_dict()


__all__ = [
    "ExpenseSummary",
    "build_category_spend_chart",
    "build_payment_choice_chart",
    "build_spend_trend_chart",
    "high_spending_categories",
    "prepare_expense_dataframe",
    "summarise_expenses",
]
