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
    
    rule("1. AGE-TO-AGE FACTORS")
 
    ratios = cl.link_ratios(tri)
    ratio_tbl = pd.DataFrame(
        ratios,
        index=pd.Index(ORIGINS, name="origin"),
        columns=[f"{k+1}-{k+2}" for k in range(n - 1)],
    )
    print("\nIndividual link ratios by origin year:")
    print(ratio_tbl.to_string(na_rep="", float_format=lambda v: f"{v:,.3f}"))
 
    ldf_all = cl.development_factors(tri)
    ldf_5yr = cl.development_factors(tri, n_years=5)
    cdf_all = cl.cumulative_factors(ldf_all)
 
    sel = pd.DataFrame({
        "volume_wtd_all": ldf_all,
        "volume_wtd_5yr": ldf_5yr,
        "simple_avg": np.nanmean(ratios, axis=0),
    }, index=[f"{k+1}-{k+2}" for k in range(n - 1)])
    print("\nSelected factors under three averaging bases:")
    print(sel.to_string(float_format=lambda v: f"{v:,.4f}"))
 
    print(f"\nAll-year volume-weighted selected, cumulative to ultimate:")
    print(pd.Series(cdf_all, index=[f"{k+1}" for k in range(n)],
                    name="cdf").to_string(float_format=lambda v: f"{v:,.4f}"))
 
    
    spread = np.nanmax(ratios[:, 0]) / np.nanmin(ratios[:, 0])
    print(f"\n1-2 link ratios range from {np.nanmin(ratios[:, 0]):.2f} to "
          f"{np.nanmax(ratios[:, 0]):.2f} ({spread:.0f}x spread).")
    
    
    rule("2. CHAIN LADDER")
 
    cl_res = cl.chain_ladder(tri, ldf_all, origins=ORIGINS)
    print()
    show(cl_res)
    print(f"\nTotal chain ladder reserve: {cl_res['ibnr'].sum():,.0f}")
    
    
    rule("3. BORNHUETTER-FERGUSON")
 
    bf_res = cl.bornhuetter_ferguson(
        tri, EARNED_PREMIUM, EXPECTED_LOSS_RATIO, ldf_all, origins=ORIGINS
    )
    print(f"\nA priori expected loss ratio: {EXPECTED_LOSS_RATIO:.0%} (assumed)")
    print()
    show(bf_res)
    print(f"\nTotal Bornhuetter-Ferguson reserve: {bf_res['ibnr'].sum():,.0f}")
    
    
    rule("4. MACK STANDARD ERROR ON THE CHAIN LADDER")
 
    mack_tbl, se_total = cl.mack_standard_error(tri, ldf_all, origins=ORIGINS)
    print()
    show(mack_tbl)
 
    total_ibnr = mack_tbl["ibnr"].sum()
    print(f"\nTotal reserve   : {total_ibnr:,.0f}")
    print(f"Total Mack S.E. : {se_total:,.0f}")
    print(f"Coefficient of variation: {se_total / total_ibnr:.1%}")
    
    
    lo_n = total_ibnr - 1.96 * se_total
    hi_n = total_ibnr + 1.96 * se_total
    s2 = np.log(1.0 + (se_total / total_ibnr) ** 2)
    mu = np.log(total_ibnr) - s2 / 2.0
    lo_l = np.exp(mu - 1.96 * np.sqrt(s2))
    hi_l = np.exp(mu + 1.96 * np.sqrt(s2))
    print(f"\n95% interval, normal    : {lo_n:>10,.0f} to {hi_n:>10,.0f}")
    print(f"95% interval, lognormal : {lo_l:>10,.0f} to {hi_l:>10,.0f}")
    print("\nThe normal lower bound is negative, which is not a possible")
    print("reserve. The lognormal respects positive support and right skew,")
    print("and is the interval Mack recommends for this reason.")
    
    
    rule("5. METHOD COMPARISON")
 
    comp = pd.DataFrame({
        "latest": cl_res["latest"],
        "pct_reported": cl_res["pct_reported"],
        "cl_ibnr": cl_res["ibnr"],
        "bf_ibnr": bf_res["ibnr"],
        "difference": bf_res["ibnr"] - cl_res["ibnr"],
        "mack_se": mack_tbl["mack_se"],
    })
    print()
    show(comp)
 
    print(f"\nChain ladder total        : {cl_res['ibnr'].sum():,.0f}")
    print(f"Bornhuetter-Ferguson total: {bf_res['ibnr'].sum():,.0f}")
    print(f"Difference                : {bf_res['ibnr'].sum() - cl_res['ibnr'].sum():,.0f}")
 
    green = comp.loc[1989:1990]
    print(f"\nThe two most recent years hold "
          f"{green['cl_ibnr'].sum() / cl_res['ibnr'].sum():.0%} of the chain "
          f"ladder reserve on {green['latest'].sum() / cl_res['latest'].sum():.0%} "
          f"of reported losses.")
 
    comp.to_csv("reserve_summary.csv", float_format="%.2f")
    print("\nWrote reserve_summary.csv")
 
    charts(tri, ratios, ldf_all, cl_res, bf_res, mack_tbl)
    print("Wrote exhibits.png")
 
 
def charts(tri, ratios, ldfs, cl_res, bf_res, mack_tbl):
    fig, ax = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("RAA reserve review: development, uncertainty, method comparison",
                 fontsize=13, y=0.98)
 
    # (a) Cumulative development by origin
    a = ax[0, 0]
    for i, yr in enumerate(ORIGINS):
        obs = tri[i][~np.isnan(tri[i])]
        a.plot(range(1, len(obs) + 1), obs, marker="o", ms=3, lw=1.2, label=str(yr))
    a.set_title("(a) Cumulative incurred loss by origin year")
    a.set_xlabel("Development period")
    a.set_ylabel("Cumulative incurred")
    a.legend(fontsize=7, ncol=2)
    a.grid(alpha=0.3)
 
    # (b) Link ratio dispersion
    b = ax[0, 1]
    for k in range(ratios.shape[1]):
        vals = ratios[:, k][~np.isnan(ratios[:, k])]
        b.scatter([k + 1] * len(vals), vals, s=18, alpha=0.55,
                  color="steelblue", zorder=3)
    b.plot(range(1, len(ldfs) + 1), ldfs, color="crimson", lw=2,
           marker="s", ms=5, label="Volume-weighted selection", zorder=4)
    b.axhline(1.0, color="grey", ls="--", lw=0.8)
    b.set_yscale("log")
    b.set_title("(b) Individual link ratios vs selected factor")
    b.set_xlabel("Development period")
    b.set_ylabel("Age-to-age factor (log scale)")
    b.legend(fontsize=8)
    b.grid(alpha=0.3, which="both")
 
    # (c) Reserve with Mack uncertainty
    c = ax[1, 0]
    y = np.arange(len(ORIGINS))
    c.barh(y, mack_tbl["ibnr"], color="steelblue", alpha=0.85)
    c.errorbar(mack_tbl["ibnr"], y, xerr=mack_tbl["mack_se"], fmt="none",
               ecolor="black", capsize=3, lw=1.2)
    c.set_yticks(y)
    c.set_yticklabels(ORIGINS)
    c.invert_yaxis()
    c.set_title("(c) Chain ladder reserve +/- 1 Mack standard error")
    c.set_xlabel("IBNR")
    c.grid(alpha=0.3, axis="x")
 
    # (d) Method comparison
    d = ax[1, 1]
    w = 0.38
    d.bar(y - w / 2, cl_res["ibnr"], w, label="Chain ladder", color="steelblue")
    d.bar(y + w / 2, bf_res["ibnr"], w, label="Bornhuetter-Ferguson", color="darkorange")
    d.set_xticks(y)
    d.set_xticklabels(ORIGINS, rotation=45)
    d.set_title("(d) Reserve by method and origin year")
    d.set_ylabel("IBNR")
    d.legend(fontsize=8)
    d.grid(alpha=0.3, axis="y")
 
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig("exhibits.png", dpi=150)
    plt.close(fig)
 
 
if __name__ == "__main__":
    main()