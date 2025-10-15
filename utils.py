# utils.py
from pathlib import Path
import pandas as pd
from datetime import datetime
import numpy as np

DATA_PATH = Path("data/swiss_hr_dataset.csv")

def load_data():
    """Load HR dataset from CSV (returns DataFrame)."""
    df = pd.read_csv(DATA_PATH, parse_dates=["Hire Date"], dayfirst=False)
    return df

def save_data(df):
    """Save DataFrame to CSV (overwrite)."""
    df.to_csv(DATA_PATH, index=False)

def append_row(row_dict):
    """Append a single row (dict) to the CSV safely."""
    df = load_data()
    new_df = pd.DataFrame([row_dict])
    # Ensure Hire Date column is ISO formatted in CSV
    if "Hire Date" in new_df.columns:
        new_df["Hire Date"] = pd.to_datetime(new_df["Hire Date"]).dt.date
    df = pd.concat([df, new_df], ignore_index=True)
    save_data(df)

def compute_vacation_total(workload_pct):
    """
    Compute vacation days total scaling linearly with workload:
    max 25 days at 100%. workload_pct like '60%' or 0.6 or int 60.
    Returns integer number of days.
    """
    # normalize to fraction
    if isinstance(workload_pct, str) and workload_pct.endswith("%"):
        frac = float(workload_pct.strip("%")) / 100.0
    elif isinstance(workload_pct, (int, float)) and workload_pct > 1:
        frac = float(workload_pct) / 100.0
    else:
        frac = float(workload_pct)
    total = round(25 * frac)
    return int(total)

def infer_seniority(age, hire_date=None):
    """
    Suggest a seniority level based on age and optionally hire_date.
    (Simple heuristic — editable.)
    """
    if hire_date is not None:
        # ensure datetime.date / datetime
        try:
            years_at_company = (pd.to_datetime("today") - pd.to_datetime(hire_date)).days / 365.25
        except Exception:
            years_at_company = 0
    else:
        years_at_company = 0

    if age < 28 and years_at_company < 3:
        return "Junior"
    if age < 35 and years_at_company < 6:
        return "Mid"
    if age < 45 and years_at_company < 12:
        return "Senior"
    if age < 60 and years_at_company >= 8:
        return "Manager"
    return "Director"