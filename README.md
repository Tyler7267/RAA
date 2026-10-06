# RAA - Reinsurance Association of America
A reserve review on a claims development triangle, implemented in Python.  Estimates outstanding claim liabilities two ways, quantifies uncertainty in the estimate and shows where the two methods disagree and why.

Results are validated against the published figures for this dataset.

THE PROBLEM
An insurer has to book a liability today for claims that have occurred but are not yet fully paid or even reported. The data available is a development triangle: each origin year's losses observed at successive valuation dates. Older years are nearly complete and recent years are barely developed. The reserving question is what those recent years will ultimately cost.

DATA
The RAA triangle: cumulative incurred losses for automatic facultative general liability business, origin years 1981-1990, reported by the Reinsurance Association of America. Comes from the R ChainLadder package.

Bornhuette-Ferguson requires needs an exposure base. The dataset has no
premium, so earned premium and the expected loss ratio are assumed and 
documented in data.py.

RESULTS (Reserve (IBNR))

Chain Ladder: 52,135
Bornhuetter-Ferguson: 60,435
Mack Standard Error(on chain ladder): 26,909
Coefficient of Variation: 51.6%

The estimate is far less precise than a point estimate suggests. 
The standard error is over half the reserve itself. Nearly all the risk
sits in two origin years, 1989 and 1990 account for 52% of the total reserve but only 5% of reported losses to date. The 1990 reserve has a 
coefficient of variation of 150%, its standard error exceeds its own point estimate, because a single observation of 2,063 is being multiplied by a cumumlative factor of 8.92.

That leverage mainly comes from  one volatile factor. The individual 1-2 link ratios range from 1.65 to 40.43, around a 25x spread driven by 1982 developing from 106 to 4,285. The volume-weighted average absorbs this reasonably, but a simple average would select 8.21 instead of 3.00 and roughly double the newest year's projection. The choice of the averaging basis is doing more work than the choice of method.

Bornhuetter-Ferguson comes in 8,300 higher, concentrated in the recent years. BF exceeds the chain ladder in 1989 and 1990, and i slighlty  lower in the mature years. 


LIMITATIONS

No tail factor.

Incurred only. A full review would include a paid  triangle as well to better determine changes in case reserving strength.

Assumed exposure base.

No inflation or trend adjustment

Mack measures parameter and process uncertainty in the chain ladder model. It does not capture model risk, like the possibility chain ladder is  the wrong method for this book.

REFERENCE
Mack, T.(1993). "Distribution-Free Calculation of the Standard Error of 
Chain Ladder Reserve Estimates."
ASTIN Bulletin 23(2), 213-225.