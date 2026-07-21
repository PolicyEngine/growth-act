"""Direct-route capital gain distributions by AGI class, 2026.

Method: two Microsimulations on the engine's pinned default dataset — a
baseline and a counterfactual with `non_sch_d_capital_gains` (fund capital
gain distributions reported directly on the 1040 with no Schedule D; PUF
E01100 concept) zeroed. The per-tax-unit federal `income_tax` delta is the
tax attributable to the distributions; NIIT is a component of `income_tax`
so it is included. "Zero tax" below means no tax attributable to the
distributions (|delta| < $0.50), not zero income tax overall.

Writes outputs/by_agi_class_2026.csv (exact values) and outputs/metadata.json.
"""

import csv
import datetime
import json
from importlib.metadata import version
from pathlib import Path

import numpy as np
from policyengine_us import Microsimulation
from policyengine_us.system import DEFAULT_DATASET

YEAR = 2026
# Bands cover the full real line: negative-AGI filers exist and hold
# distributions (683k units, ~$1.1B in 2026) — omitting them understates
# the unit total by 17%.
BANDS = [
    (-np.inf, 0, "Negative AGI"),
    (0, 50e3, "$0-$50k"),
    (50e3, 100e3, "$50k-$100k"),
    (100e3, 200e3, "$100k-$200k"),
    (200e3, 500e3, "$200k-$500k"),
    (500e3, 1e6, "$500k-$1M"),
    (1e6, np.inf, "$1M+"),
]

base = Microsimulation()
nsd = base.calculate("non_sch_d_capital_gains", YEAR, map_to="tax_unit")
agi = base.calculate("adjusted_gross_income", YEAR, map_to="tax_unit")
w = base.calculate("tax_unit_weight", YEAR)
base_fed = base.calculate("income_tax", YEAR, map_to="tax_unit")

cf = Microsimulation()
n_persons = len(cf.calculate("non_sch_d_capital_gains", YEAR))
cf.set_input("non_sch_d_capital_gains", YEAR, np.zeros(n_persons))
cf_fed = cf.calculate("income_tax", YEAR, map_to="tax_unit")

delta = base_fed.values - cf_fed.values
mask = nsd.values > 0
ww, aa, dd, tt = w.values[mask], agi.values[mask], nsd.values[mask], delta[mask]

rows = []
for lo, hi, label in BANDS:
    m = (aa >= lo) & (aa < hi)
    units = ww[m].sum()
    dollars = (dd[m] * ww[m]).sum()
    tax = (tt[m] * ww[m]).sum()
    zero = ww[m][np.abs(tt[m]) < 0.5].sum()
    rows.append(
        {
            "agi_class": label,
            "tax_units": units,
            "distributions_usd": dollars,
            "tax_attributable_usd": tax,
            "effective_rate": tax / dollars if dollars else 0.0,
            "share_units_zero_tax": zero / units if units else 0.0,
            "avg_distribution_usd": dollars / units if units else 0.0,
        }
    )

total = {
    "agi_class": "All",
    "tax_units": ww.sum(),
    "distributions_usd": (dd * ww).sum(),
    "tax_attributable_usd": (tt * ww).sum(),
    "effective_rate": (tt * ww).sum() / (dd * ww).sum(),
    "share_units_zero_tax": ww[np.abs(tt) < 0.5].sum() / ww.sum(),
    "avg_distribution_usd": (dd * ww).sum() / ww.sum(),
}

# Reconciliation guard: bands must partition the affected units exactly.
for field in ("tax_units", "distributions_usd", "tax_attributable_usd"):
    band_sum = sum(r[field] for r in rows)
    assert abs(band_sum - total[field]) <= 1e-6 * max(abs(total[field]), 1), (
        f"{field}: bands sum to {band_sum:,.0f} but total is {total[field]:,.0f}"
    )

out_dir = Path(__file__).resolve().parent.parent / "outputs"
out_dir.mkdir(exist_ok=True)
with open(out_dir / "by_agi_class_2026.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows + [total])

with open(out_dir / "metadata.json", "w") as f:
    json.dump(
        {
            "policyengine_us": version("policyengine-us"),
            "dataset": DEFAULT_DATASET,
            "year": YEAR,
            "generated": datetime.date.today().isoformat(),
            "method": "per-tax-unit income_tax delta from zeroing non_sch_d_capital_gains",
        },
        f,
        indent=2,
    )

print(f"{'AGI class':<14}{'units (k)':>10}{'CGD ($B)':>10}{'tax ($M)':>10}{'eff rate':>9}{'% $0':>7}")
for r in rows + [total]:
    print(
        f"{r['agi_class']:<14}{r['tax_units'] / 1e3:>10,.0f}{r['distributions_usd'] / 1e9:>10.2f}"
        f"{r['tax_attributable_usd'] / 1e6:>10,.0f}{r['effective_rate']:>9.1%}"
        f"{r['share_units_zero_tax']:>7.1%}"
    )
