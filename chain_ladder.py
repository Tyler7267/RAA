import numpy as np
import pandas as pd


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

    n = tri.shape[0]
    f = np.zeros(n - 1)
    for i in range(n - 1):
        rows = n - i - 1
        start = 0 if n_years is None else max(0, rows - n_years)
        num = np.nansum(tri[start:rows, i + 1])
        den = np.nansum(tri[start:rows, i])
        f[i] = num/den
    return f