"""Statutory bracket proxy vs. full-system delta for "pays $0 on distributions".

Compares three definitions of a unit paying nothing on its direct-route
distributions: (1) a bracket proxy stacking the distributions first against
the 0% capital gains breakpoint, (2) the same test with correct stacking
(the whole preferential stack under the breakpoint), and (3) the full-system
income_tax delta. The gap between (1)/(2) and (3) is displacement of other
gains within the preferential schedule plus AGI-side interactions — about a
quarter of the total tax comes from units the bracket proxy calls zero-rate.
"""

import numpy as np
from policyengine_us import Microsimulation

YEAR = 2026

base = Microsimulation()
tu_dist = base.calculate("non_sch_d_capital_gains", YEAR, map_to="tax_unit")
w = base.calculate("tax_unit_weight", YEAR)
ti = base.calculate("taxable_income", YEAR, map_to="tax_unit")
ncg = base.calculate("net_capital_gain", YEAR, map_to="tax_unit")
fs = base.calculate("filing_status", YEAR, map_to="tax_unit")
base_fed = base.calculate("income_tax", YEAR, map_to="tax_unit")

bp = {"SINGLE": 49_450, "JOINT": 98_900, "SEPARATE": 49_450,
      "HEAD_OF_HOUSEHOLD": 66_200, "SURVIVING_SPOUSE": 98_900}
bps = np.array([bp.get(str(x), 49_450) for x in fs])
ordinary = np.maximum(ti.values - ncg.values, 0)

mask = tu_dist.values > 0
ww = w.values[mask]
dd = tu_dist.values[mask] * ww

# (1) naive bracket proxy: distributions stacked first
in_zero_orig = (ordinary + tu_dist.values <= bps)[mask]
print(f"(1) ORIGINAL test  — units: {(ww*in_zero_orig).sum()/ww.sum():.1%}, dollars: {(dd*in_zero_orig).sum()/dd.sum():.1%}")

# (2) corrected stacking: whole preferential stack must fit under the breakpoint
in_zero_stack = (ordinary + ncg.values <= bps)[mask]
print(f"(2) CORRECT stack  — units: {(ww*in_zero_stack).sum()/ww.sum():.1%}, dollars: {(dd*in_zero_stack).sum()/dd.sum():.1%}")

# (3) full-system delta
cf = Microsimulation()
n = len(cf.calculate("non_sch_d_capital_gains", YEAR))
cf.set_input("non_sch_d_capital_gains", YEAR, np.zeros(n))
cf_fed = cf.calculate("income_tax", YEAR, map_to="tax_unit")
delta = (base_fed.values - cf_fed.values)[mask]
zero_delta = np.abs(delta) < 0.5
print(f"(3) DELTA test     — units: {(ww*zero_delta).sum()/ww.sum():.1%}, dollars: {(dd*zero_delta).sum()/dd.sum():.1%}")

# interaction: among original-test '0% bracket' units, share actually paying tax
pay_anyway = in_zero_orig & ~zero_delta
print(f"(4) of (1)'s 0%-bracket units, share still paying >$0.50 via AGI interactions: {(ww*pay_anyway).sum()/(ww*in_zero_orig).sum():.1%}")
print(f"    tax they pay: ${(delta[pay_anyway]*ww[pay_anyway]).sum()/1e9:.3f}B of ${(delta*ww).sum()/1e9:.3f}B total")
