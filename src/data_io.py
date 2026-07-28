#data_io.py# src/data_io.py
import pandas as pd


def parse_dates(df, column):
    """
    Cleans 'a.m./p.m.' formatting and parses `column` to datetime in place.
    """
    cleaned = df[column].str.replace("a.m.", "AM", regex=False).str.replace("p.m.", "PM", regex=False)
    df[column] = pd.to_datetime(cleaned, format="%Y-%m-%d, %I:%M %p")
    return df


def load_nc_data(path):
    """Load and clean the raw NC export: fix Type encoding, parse dates, derive quarter."""
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["Type"] = df["Type"].str.encode("cp1252").str.decode("utf-8")
    df = parse_dates(df, "Date/Time Opened")
    df["quarter"] = df["Date/Time Opened"].dt.to_period("Q").astype(str)
    return df


def load_sales_data(path):
    """Load monthly sales and derive the quarter key for merging against NC data."""
    df_sales = pd.read_csv(path, encoding="utf-8-sig")
    df_sales['month_year'] = pd.to_datetime(df_sales['month_year'])
    df_sales['quarter'] = df_sales['month_year'].dt.to_period('Q')
    df_sales['quarter'] = df_sales['quarter'].astype(str)
    return df_sales
