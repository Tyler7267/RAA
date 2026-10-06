"""
Reserve review on the RAA triangle

Runs chain ladder and Bornhuetter-Ferguson side by side,
also quantifies the chain ladder uncertainty with Mack standard error.
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import chain_ladder as cl
from data import TRIANGLE, ORIGINS, EARNED_PREMIUM, EXPECTED_LOSS_RATIO

pd.set_option("display.width", 200)
pd.set_option("display.float_format", lambda v: f"{v:,.3f}")
 
OUT = "."
 
 
def rule(title):
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)
 
 
def show(df):
    """Print a table with currency columns comma-formatted and ratios at 3dp."""
    ratio_cols = {"cdf", "pct_reported", "pct_unreported", "cv"}
    fmt = {}
    for col in df.columns:
        if col in ratio_cols:
            fmt[col] = lambda v: "" if pd.isna(v) else f"{v:.3f}"
        else:
            fmt[col] = lambda v: "" if pd.isna(v) else f"{v:,.0f}"
    print(df.to_string(formatters=fmt, na_rep=""))
 
 
def main():
    tri = TRIANGLE
    n = tri.shape[0]