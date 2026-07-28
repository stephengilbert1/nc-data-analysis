# src/aggregate.py
import pandas as pd

def format_quarter(period_str):
    """
    Reformats a period string from 'YYYYQ#' to 'Q# YYYY' for display.
    e.g. '2023Q1' -> 'Q1 2023'
    """
    year, quarter = period_str.split("Q")
    return f"Q{quarter} {year}"

def get_counts_with_labels(df, column):
    """
    Returns value counts for `column` in `df`, with Count, Percent,
    and a combined 'Count (Percent%)' Label column for chart text.
    """
    counts = df[column].value_counts().reset_index()
    counts.columns = [column, "Count"]
    counts["Percent"] = (counts["Count"] / counts["Count"].sum() * 100).round(1)
    counts["Label"] = counts["Count"].astype(str) + " (" + counts["Percent"].astype(str) + "%)"
    return counts

def build_quarterly_counts(df, group_col, date_col="Date/Time Opened"):
    """
    Groups `df` by Quarter and `group_col`, zero-filling any quarter/category
    combination that had no cases - keeps line/bar charts continuous.
    """
    df = df.copy()
    df["Quarter"] = df[date_col].dt.to_period("Q").astype(str)

    quarters = sorted(df["Quarter"].unique())
    quarters = [format_quarter(q) for q in quarters]
    df["Quarter"] = df["Quarter"].map(format_quarter)

    categories = df[group_col].unique()
    full_index = pd.MultiIndex.from_product([quarters, categories], names=["Quarter", group_col])
    return (
        df.groupby(["Quarter", group_col]).size()
        .reindex(full_index, fill_value=0)
        .reset_index(name="Count")
    )

def share_of(counts, label_col, category, pct_col="Percent"):
    """Percent of total for one category in a get_counts_with_labels frame."""
    match = counts.loc[counts[label_col] == category, pct_col]
    if match.empty:
        raise KeyError(f"{category!r} not found in {label_col}")
    return match.iloc[0]


def leader(counts, label_col, value_col="Count"):
    """Name of the highest-count category."""
    return counts.loc[counts[value_col].idxmax(), label_col]