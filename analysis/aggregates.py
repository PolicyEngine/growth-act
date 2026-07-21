"""National aggregates for direct-route capital gain distributions, 2026.

Baseline vs. a counterfactual zeroing `non_sch_d_capital_gains`; the federal
`income_tax` delta (NIIT included, as a component of income_tax) is the tax
attributable to the distributions. Also reports the state income tax delta
and the share of reporting units (and their dollars) with no tax attributable.
"""

import numpy as np
from importlib.metadata import version
from policyengine_us import Microsimulation

YEAR = 2026

print("pe-us release:", version("policyengine-us"), flush=True)

base = Microsimulation()
print("dataset:", getattr(base, "dataset", None), flush=True)

nsd_tu = base.calculate("non_sch_d_capital_gains", YEAR, map_to="tax_unit")
total_nsd = nsd_tu.sum()
affected = nsd_tu > 0
n_units = affected.sum()  # weighted count via MicroSeries
print(f"non_sch_d_capital_gains total {YEAR}: ${total_nsd/1e9:.2f}B", flush=True)
print(f"tax units reporting >0: {n_units/1e6:.2f}M", flush=True)

base_fed = base.calculate("income_tax", YEAR, map_to="tax_unit")
base_niit = base.calculate("net_investment_income_tax", YEAR, map_to="tax_unit")
base_state = base.calculate("state_income_tax", YEAR, map_to="household")

cf = Microsimulation()
n_persons = len(cf.calculate("non_sch_d_capital_gains", YEAR))
cf.set_input("non_sch_d_capital_gains", YEAR, np.zeros(n_persons))

cf_fed = cf.calculate("income_tax", YEAR, map_to="tax_unit")
cf_niit = cf.calculate("net_investment_income_tax", YEAR, map_to="tax_unit")
cf_state = cf.calculate("state_income_tax", YEAR, map_to="household")

fed_delta = base_fed.sum() - cf_fed.sum()
niit_delta = base_niit.sum() - cf_niit.sum()
state_delta = base_state.sum() - cf_state.sum()
print(f"federal income_tax attributable: ${fed_delta/1e9:.3f}B", flush=True)
print(f"  of which NIIT: ${niit_delta/1e9:.3f}B", flush=True)
print(f"state income tax attributable: ${state_delta/1e9:.3f}B", flush=True)
print(f"avg effective federal rate on the base: {100*fed_delta/total_nsd:.1f}%", flush=True)

# Distribution among reporting units: who pays $0 on their distributions?
unit_delta = base_fed - cf_fed
zero_tax = affected & (np.abs(unit_delta.values) < 0.5)
share_units_zero = zero_tax.sum() / n_units
dollars_zero = nsd_tu[zero_tax.values].sum() / total_nsd
print(f"share of reporting units paying $0 on distributions: {100*share_units_zero:.1f}%", flush=True)
print(f"share of dollars held by those units: {100*dollars_zero:.1f}%", flush=True)
