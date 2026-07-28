"""
Generate synthetic NC and sales data for the public / portfolio version of this
project.

The real Salesforce export and sales figures are commercially sensitive and are
never committed. This script produces stand-ins with the same schema, dtypes and
categorical vocabulary, so the notebook runs end to end and renders real charts
from invented numbers.

The synthetic series are shaped to reproduce the real dataset's findings, not to
invent new ones:
  - NC volume starts high at roll-out and decays to a low flat tail.
  - Venting-under-vacuum cases occur early and taper off after the fix, so their
    share of the total falls over time without changing the overall count.
  - Sales are roughly flat, so the NC-per-unit chart tracks the raw NC decline.

Account names are fictional. Any resemblance to real utilities or transformer
manufacturers is unintended.

Usage:
    python scripts/generate_synthetic_data.py
"""

import numpy as np
import pandas as pd

SEED = 26
OUT_DIR = "data"

# --------------------------------------------------------------------------
# Constants to verify against the real charts before publishing.
# These are reverse-engineered from rounded ranges, not read from real data.
# --------------------------------------------------------------------------

# Window. START must sit on or before the real first case so the roll-out peak
# lands in the right quarter (real peak is Q4 2021).
START = pd.Timestamp("2021-10-01")          # <-- confirm real first case date
END = pd.Timestamp("2026-06-30")

# Baseline NC arrival shape.
# PEAK_TO_TAIL is the tail rate as a fraction of the roll-out peak (~7.5 / 65).
# SETTLE_DAYS controls how fast it decays. Larger = slower settle.
PEAK_TO_TAIL = 0.12                         # <-- tune to match tail height
SETTLE_DAYS = 250                           # <-- tune to match how fast it falls

# Date the venting failure was addressed. Venting cases taper to ~zero by here.
VENTING_FIX = pd.Timestamp("2024-06-01")    # <-- read off the real venting chart

N_CASES = 367  # matches the real export's row count


# --------------------------------------------------------------------------
# Categorical vocabulary - mirrors the real data exactly
# --------------------------------------------------------------------------

DEPARTMENTS = {
    "Engineering - Customer": 0.91,
    "Engineering - Internal": 0.05,
    "Quality": 0.03,
    "Production": 0.01,
}

# Problem Flag distribution within Engineering - Customer
PROBLEM_FLAGS = {
    "Unintended Activation": 0.70,
    "Leaking": 0.13,
    "Other": 0.08,
    "Energized Activation": 0.05,
    "Did not Activate": 0.04,
}

# Root Cause conditional on Problem Flag
ROOT_CAUSES = {
    "Unintended Activation": {
        "Undetermined": 0.38,
        "SL removed before install": 0.20,
        "Venting under vaccuum": 0.12,
        "Incorrect SL Install": 0.10,
        "Activated on TM Line": 0.08,
        "1-ph pad lid closing": 0.06,
        "Shock during transit": 0.04,
        "Other": 0.02,
    },
    "Leaking": {
        "Rolling Seal": 0.73,
        "Housing crack": 0.10,
        "Undetermined": 0.09,
        "Weld porosity": 0.05,
        "Other": 0.03,
    },
    "Energized Activation": {
        "Undetermined": 0.45,
        "Field surge": 0.30,
        "Incorrect SL Install": 0.15,
        "Other": 0.10,
    },
    "Did not Activate": {
        "Undetermined": 0.50,
        "Contact fouling": 0.30,
        "Housing crack": 0.12,
        "Other": 0.08,
    },
    "Other": {
        "Undetermined": 0.60,
        "Other": 0.40,
    },
}

CASE_ORIGINS = {"Utility": 0.78, "Transformer Manufacturer": 0.22}

# The real export contains mojibake: an en dash (U+2013) whose UTF-8 bytes were
# decoded as cp1252, giving "a<euro><left-quote>". The notebook's load step
# reverses this. Reproducing the corruption here keeps that cleaning code
# meaningful in the public version rather than a no-op.
EN_DASH_MOJIBAKE = "\u00e2\u20ac\u201c"

CASE_TYPES = {
    f"Field Non{EN_DASH_MOJIBAKE}Conformance": 0.72,
    "Production Non-Conformance": 0.18,
    "Warranty Claim": 0.10,
}

STATUSES = {"Closed": 0.86, "In Progress": 0.10, "New": 0.04}
PRIORITIES = {"Medium": 0.55, "Low": 0.28, "High": 0.17}

VENTING_ROOT_CAUSE = "Venting under vaccuum"


# --------------------------------------------------------------------------
# Fictional account names
# --------------------------------------------------------------------------

# Australian-flavoured utility names, built combinatorially so the long tail is
# broad (~100 distinct accounts) as it is in the real data.
AU_PLACES = [
    "Murray Valley", "Kalgoorlie", "Yarra", "Barossa", "Nullarbor", "Pilbara",
    "Riverina", "Gippsland", "Cape York", "Bass Strait", "Wimmera", "Torrens",
    "Hunter Valley", "Darling Downs", "Great Dividing", "Eyre Peninsula",
    "Mallee", "Sunraysia", "Tanami", "Coral Coast", "Snowy River", "Bundaberg",
    "Illawarra", "Geraldton", "Katherine", "Warrnambool",
]
AU_SUFFIXES = [
    "Power", "Energy Networks", "Electricity", "Grid Services",
    "Power Corporation",
]

# Asian-flavoured transformer manufacturer names.
TM_ACCOUNTS = [
    "Hanshin Transformer Works",
    "Daeryuk Electric",
    "Jinhua Power Equipment",
    "Chonburi Transformer Co",
    "Selangor Electric Industries",
    "Sagara Denki",
    "Taipei Heavy Electric",
    "Bandung Transformindo",
    "Nam Viet Power Equipment",
    "Hyeonsan Electric",
]


def build_utility_accounts(rng, n=100):
    """Combinatorial fictional utility names, deduplicated."""
    names = set()
    while len(names) < n:
        place = rng.choice(AU_PLACES)
        suffix = rng.choice(AU_SUFFIXES)
        names.add(f"{place} {suffix}")
    return sorted(names)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def weighted_choice(rng, mapping, size):
    """Draw `size` values from a {value: probability} mapping."""
    keys = list(mapping)
    probs = np.array(list(mapping.values()), dtype=float)
    probs = probs / probs.sum()  # tolerate weights that don't sum to exactly 1
    return rng.choice(keys, size=size, p=probs)


def format_salesforce_datetime(ts):
    """
    Render a timestamp the way the Salesforce export does:
    '2024-03-15, 2:45 p.m.' - non-padded 12h clock with a.m./p.m.
    """
    hour_24 = ts.hour
    meridiem = "a.m." if hour_24 < 12 else "p.m."
    hour_12 = hour_24 % 12
    if hour_12 == 0:
        hour_12 = 12
    return f"{ts:%Y-%m-%d}, {hour_12}:{ts:%M} {meridiem}"


def draw_case_dates(rng, is_venting):
    """
    Draw an open date for each case from a time-of-occurrence profile.

    Non-venting cases follow a baseline that starts high at roll-out and decays
    to a flat tail. Venting cases decay faster, tapering to ~zero by VENTING_FIX,
    so their share of the total falls over time. The total venting *count* is
    unchanged - only when those cases land moves.

    `is_venting` is a boolean array aligned to the case rows.
    """
    total_days = (END - START).days
    day_index = np.arange(total_days)

    # Baseline: exp decay from a peak of 1.0 down to a floor of PEAK_TO_TAIL.
    decay = np.exp(-day_index / SETTLE_DAYS)
    baseline = PEAK_TO_TAIL + (1 - PEAK_TO_TAIL) * decay
    baseline /= baseline.sum()

    # Venting: linear taper to zero by the fix date, flat zero after.
    fix_day = (VENTING_FIX - START).days
    venting = np.clip(1.0 - day_index / fix_day, 0.0, 1.0)
    venting /= venting.sum()

    offsets = np.empty(len(is_venting), dtype=int)
    n_base = int((~is_venting).sum())
    n_vent = int(is_venting.sum())
    offsets[~is_venting] = rng.choice(day_index, size=n_base, p=baseline)
    offsets[is_venting] = rng.choice(day_index, size=n_vent, p=venting)

    times = rng.integers(7 * 60, 18 * 60, size=len(is_venting))  # business hours
    return [
        START + pd.Timedelta(days=int(d)) + pd.Timedelta(minutes=int(t))
        for d, t in zip(offsets, times)
    ]


# --------------------------------------------------------------------------
# Generators
# --------------------------------------------------------------------------

def generate_nc_data(rng):
    utility_accounts = build_utility_accounts(rng)

    departments = weighted_choice(rng, DEPARTMENTS, N_CASES)
    problem_flags = weighted_choice(rng, PROBLEM_FLAGS, N_CASES)

    # Root cause depends on problem flag, so it's drawn per row.
    root_causes = [
        weighted_choice(rng, ROOT_CAUSES[flag], 1)[0] for flag in problem_flags
    ]

    # Dates depend on root cause (venting decays faster), so they're drawn after.
    is_venting = np.array([rc == VENTING_ROOT_CAUSE for rc in root_causes])
    opened = draw_case_dates(rng, is_venting)

    origins = weighted_choice(rng, CASE_ORIGINS, N_CASES)

    # Utility cases spread broadly; TM cases dominated by one manufacturer.
    tm_probs = np.array([0.42] + [0.58 / (len(TM_ACCOUNTS) - 1)] * (len(TM_ACCOUNTS) - 1))
    accounts = [
        rng.choice(utility_accounts)
        if origin == "Utility"
        else rng.choice(TM_ACCOUNTS, p=tm_probs)
        for origin in origins
    ]

    df = pd.DataFrame({
        "Case Number": [f"{100000 + i:06d}" for i in range(N_CASES)],
        "Date/Time Opened": [format_salesforce_datetime(ts) for ts in opened],
        "Status": weighted_choice(rng, STATUSES, N_CASES),
        "Priority": weighted_choice(rng, PRIORITIES, N_CASES),
        "Type": weighted_choice(rng, CASE_TYPES, N_CASES),
        "Department": departments,
        "Case Origin": origins,
        "Account Name": accounts,
        "Problem Flag": problem_flags,
        "Root Cause": root_causes,
        "Product": "Gen 3 IFD Sensor",
    })

    # Sort by open date so the file reads like a real chronological export.
    return df.iloc[np.argsort(opened)].reset_index(drop=True)


def generate_sales_data(rng):
    """
    Roughly flat monthly sales with month-to-month noise. Flat, rather than the
    earlier ramp, so the NC-per-unit chart tracks the raw NC decline instead of
    being dragged down by a rising denominator.
    """
    months = pd.date_range(START, END, freq="MS")
    base = np.full(len(months), 12_000.0)   # <-- set level/shape from real sales
    noise = rng.normal(1.0, 0.12, size=len(months))
    units = np.clip(base * noise, 1_000, None).round().astype(int)

    return pd.DataFrame({
        "month_year": months.strftime("%Y-%m-%d"),
        "unit_sensors_sold": units,
    })


# --------------------------------------------------------------------------

def main():
    rng = np.random.default_rng(SEED)

    nc = generate_nc_data(rng)
    sales = generate_sales_data(rng)

    nc_path = f"{OUT_DIR}/NC-raw-data-extra-filtered.csv"
    sales_path = f"{OUT_DIR}/Sales-data.csv"

    # utf-8-sig matches the real export's BOM, so the notebook's read_csv
    # encoding argument stays correct.
    nc.to_csv(nc_path, index=False, encoding="utf-8-sig")
    sales.to_csv(sales_path, index=False, encoding="utf-8-sig")

    print(f"Wrote {len(nc)} NC rows to {nc_path}")
    print(f"Wrote {len(sales)} sales rows to {sales_path}")


if __name__ == "__main__":
    main()