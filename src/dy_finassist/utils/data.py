from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from ..config import RAW_DATA_DIR, REFERENCE_DATA_DIR


class DataNotFound(FileNotFoundError):
    """Raised when an expected data asset is missing."""


@lru_cache(maxsize=1)
def load_personal_expenses() -> pd.DataFrame:
    path = RAW_DATA_DIR / "personal_finance_transactions.xlsx"
    if not path.exists():
        raise DataNotFound(f"Expected file not found: {path}")
    return pd.read_excel(path)


@lru_cache(maxsize=1)
def load_bank_statement() -> pd.DataFrame:
    path = RAW_DATA_DIR / "bank_statement_sample.xlsx"
    if not path.exists():
        raise DataNotFound(f"Expected file not found: {path}")

    data = pd.read_excel(path)
    if "Date" in data.columns:
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data.sort_values("Date", ascending=False)

    withdrawal = data.get("Withdrawal Amount")
    deposit = data.get("Deposit Amount")
    if withdrawal is not None or deposit is not None:
        withdrawal = withdrawal.fillna(0) if withdrawal is not None else 0
        deposit = deposit.fillna(0) if deposit is not None else 0
        data["Amount"] = deposit - withdrawal

    if "Narration" in data.columns:
        data = data.rename(columns={"Narration": "Description"})

    return data


def _load_text(filename: str) -> str:
    path = REFERENCE_DATA_DIR / filename
    if not path.exists():
        raise DataNotFound(f"Expected file not found: {path}")
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_loans_info() -> str:
    return _load_text("loans_info_sample.txt")


@lru_cache(maxsize=1)
def load_user_profile() -> str:
    return _load_text("user_profile_sample.txt")


__all__ = [
    "DataNotFound",
    "load_bank_statement",
    "load_loans_info",
    "load_personal_expenses",
    "load_user_profile",
]
