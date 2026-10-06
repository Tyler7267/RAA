import numpy as np
import pandas as pd

"""
Loss reserving methods for claims development triangles.

1. Chain Ladder - project each origin year using observed development


All functions take a cumulative triangle as a 2D numpy array with origin
years along the rows and development periods (in months) across the columns
Unobserved cells are labeled np.nan.
"""

def link_ratios(tri):
    """
    Individual age-to-age factors for every observed cell pair.
    
    The ratio C[i, k+1] / C[i, k] measures how much origin year i grew 
    between development period k and k+1. We will use this as a way to spot 
    outliers
    """
    n = tri.shape[0]
    out = np.full((n, n-1), np.nan)
    
    for i in range(n):
        for k in range(n-1):
            if not np.isnan(tri[i, k]) and not np.isnan(tri[i, k+1]):
                out[i, k] = tri[i, k+1] / tri[i, k]
    
    return out


def development_factors(tri, n_years = None):
    """
    Volume-Weighted average age-to-age factors
    
    Parameters:
    
    n_years : int, optional
        Use only the most recent n_years diagonals for each factor.
    """
    n = tri.shape[0]
    f = np.zeros(n - 1)
    for i in range(n - 1):
        rows = n - i - 1
        start = 0 if n_years is None else max(0, rows - n_years)
        num = np.nansum(tri[start:rows, i + 1])
        den = np.nansum(tri[start:rows, i])
        f[i] = num/den
    return f


def cumulative_factors(ldfs, tail = 1.0):
    """
    Cummulative development factors (CDFs) from age i to ultimate.
    
    Defaulting tail to 1.0 assumes the triangle is fully developed at
    the final column
    """
    n = len(ldfs) + 1
    cdf = np.ones(n)
    running = tail
    for i in range(n - 2, -1, -1):
        running *= ldfs[i]
        cdf[i] = running
    cdf[n - 1] = tail
    return cdf


def square_triangle(tri, ldfs, tail = 1.0):
    """
    Fill the lower-right of the triangle using the selected factors.
    """
    n = tri.shape[0]
    full = tri.copy()
    for i in range(1,n):
        for j in range(1,n):
            full[i,j] = full[i, j-1] * ldfs[j-1]
    return full


def latest_diagonal(tri):
    """The most recent observed value for each year."""
    n = tri.shape[0]
    return np.array([tri[i, n - 1 - i] for i in range(n)])  


###############################################################################
#   RESERVING METHODS
###############################################################################

def chain_ladder(tri, ldfs = None, tail = 1.0, origins = None):
    """
    Chain ladder reserve estimate.
    
    Ultimate = latest observed loss x cumulative development factor.
    IBNR = Ultimate - latest.
    
    This method relies on the assumption that past development is predictive
    of future development. 
    
    Its weakness is leverage on the most recent years. 
    """
    n = tri.shape[0]
    if ldfs is None:
        ldfs = development_factors(tri)
    cdf = cumulative_factors(ldfs, tail)
    full = square_triangle(tri, ldfs, tail)
    latest = latest_diagonal(tri)
    
    age = np.array([n - 1 - i for i in range(n)])
    cdf_i = cdf[age]
    ultimate = latest * cdf_i
    ibnr = ultimate - latest

    if origins is None:
        index = pd.RangeIndex(n)
    else:
        index = pd.Index(origins)

    return pd.DataFrame({
        "latest": latest,
        "cdf": cdf_i,
        "pct_reported": 1.0 / cdf_i,
        "ultimate": ultimate,
        "ibnr": ibnr,
    }, index=index)    
    

def bornhuetter_ferguson(tri, premium, elr, ldfs = None, tail = 1.0,
                         origins = None):
    
    n = tri.shape[0]
    if ldfs is None:
        ldfs = development_factors(tri)
    cdf = cumulative_factors(ldfs, tail)
    
    premium = np.asarray(premium, dtype = float)
    elr = np.broadcast_to(np.asarray(elr,  dtype=float), (n,))
    
    latest = latest_diagonal(tri)
    age = np.array([n - 1 - i for i in range(n)])
    cdf_i = cdf[age]
    pct_unreported = 1.0 - 1.0/cdf_i
    
    a_priori = premium * elr
    ibnr = pct_unreported * a_priori
    ultimate = latest + ibnr

    if origins is None:
        index = pd.RangeIndex(n)
    else:
        index = pd.Index(origins)

    return pd.DataFrame({
        "latest": latest,
        "premium":  premium,
        "a_priori_loss": a_priori,
        "pct_unreported": pct_unreported,
        "ultimate": ultimate,
        "ibnr": ibnr,
    }, index=index)
    
    
def mack_standard_error(tri, ldfs = None, origins = None):
    
    n = tri.shape[0]
    if ldfs is None:
        ldfs = development_factors(tri)
    full = square_triangle(tri, ldfs)
    latest = latest_diagonal(tri)
    ultimate = full[:,-1]
    ibnr = ultimate - latest
    
    colsum = np.array([np.nansum(tri[:n - i - 1, i]) for i in range(n-1)])
    
    sigma2 = np.zeros(n-1)
    for i in range(n-2):
        m = n - i - 1
        C = tri[:m, i]
        F = tri[:m, i + 1] / tri[:m, i]
        sigma2[i] = np.sum(C * (F-ldfs[i]) ** 2) / (m-1)
        
    sigma2[n-2] = min(
        sigma2[n-3] ** 2 / sigma2[n-4],
        min(sigma2[n-3], sigma2[n-4])
    )
    
    # Mean squared error per origin
    mse = np.zeros(n)
    for i in range(1, n):
        s = 0.0
        for j in range(n - 1 - i, n - 1):
            s += (sigma2[j] / ldfs[j] ** 2) * (1.0 / full[i,j] + 
                                               1.0 / colsum[j])
        mse[i] = ultimate[i] ** 2 * s
    se = np.sqrt(mse)
    
    # Total, includes covariance across origin years
    total_mse = 0.0
    for i in range(1, n):
        inner = 0.0
        for j in range(n - 1  - i, n - 1):
            inner += 2.0 * sigma2[j] / (ldfs[j] ** 2 * colsum[j])
            
        total_mse += mse[i] + ultimate[i] * np.sum(ultimate[i + 1:]) * inner
    se_total = np.sqrt(total_mse)
    
    with np.errstate(divide = "ignore", invalid = "ignore"):
        cv = np.where(ibnr > 0, se / ibnr, np.nan)
        
        
    if origins is None:
        index = np.IndexRange(n)
    else:
        index = np.Index(origins)
        
    table = pd.DataFrame({
        "ibnr": ibnr,
        "mack_se": se,
        "cv": cv
    }, index = index)
    
    return table, se_total