# GROWTH Act modeling groundwork

Reproducible analysis of the capital gain distributions the GROWTH Act (H.R. 2089 / S. 1839, 119th Congress) would let mutual fund investors defer, using [PolicyEngine US](https://github.com/PolicyEngine/policyengine-us) microsimulation. This is modeling groundwork — measured tax on the affected income under current law — not a revenue score of the bill.

## The bill

The Generating Retirement Ownership Through Long-Term Holding Act (Van Duyne/Sewell in the House, Cornyn in the Senate) would add IRC §1046: no gain recognized on a regulated investment company capital gain dividend that is automatically reinvested through a dividend reinvestment plan. Mechanics that matter for modeling:

- Recapture is pro rata as shares are sold, and full at death — there is no step-up escape.
- Reinvested shares are deemed held more than one year, so gains on them come back long-term regardless of actual holding period (a character rule, not just timing).
- Recapture brings back the deferred gain itself; growth on the reinvested shares is taxed as its own gain at sale.

As of July 2026 the bill is in committee in both chambers with no JCT estimate and no third-party revenue score we are aware of.

## The two reporting routes

Fund capital gain distributions reach individual returns two mutually exclusive ways:

1. **Direct route**: reported on Form 1040 with no Schedule D (PUF `E01100`; the `non_sch_d_capital_gains` variable in PolicyEngine US). This is what this repo measures.
2. **Schedule D route**: line 13, folded into net long-term gains and not separable in any microdata. The SOI Sales of Capital Assets study (TY2015, the latest all-route accounting) put this route at roughly 6× the direct route — direct-route dollars were about 15% of the combined total. Splitting it out per income class is in progress at [microcosm#274](https://github.com/PolicyEngine/microcosm/issues/274); the deterministic national split shipped in [microcosm#282](https://github.com/PolicyEngine/microcosm/pull/282).

Engine groundwork: [policyengine-us#8839](https://github.com/PolicyEngine/policyengine-us/pull/8839) (direct-route distributions in gross income, net capital gain, and net investment income) and [policyengine-us#8850](https://github.com/PolicyEngine/policyengine-us/pull/8850) (Schedule D route memo variable).

## Direct route by AGI class, 2026

Method: baseline vs. a counterfactual with `non_sch_d_capital_gains` zeroed; the per-tax-unit federal `income_tax` delta (NIIT included) is the tax attributable to the distributions. "$0 tax" means no tax attributable to the distributions, not zero income tax overall.

| AGI class | Tax units | Distributions | Tax on them | Effective rate | Share with $0 tax on them |
|---|---:|---:|---:|---:|---:|
| Negative AGI | 683k | $1.1B | $0M | 0.0% | 100% |
| $0–$50k | 1.14M | $2.5B | $10M | 0.4% | 92% |
| $50k–$100k | 874k | $3.5B | $312M | 8.9% | 26% |
| $100k–$200k | 914k | $3.3B | $305M | 9.3% | 45% |
| $200k–$500k | 366k | $2.5B | $424M | 17.2% | 0% |
| $500k–$1M | 33k | $0.8B | $144M | 18.3% | 0% |
| $1M+ | 4k | $0.04B | $9M | 22.1% | 0% |
| **All** | **4.0M** | **$13.7B** | **$1.2B** | **8.8%** | **59%** |

Exact values: [`outputs/by_agi_class_2026.csv`](outputs/by_agi_class_2026.csv); provenance: [`outputs/metadata.json`](outputs/metadata.json).

What the table shows:

- Two-thirds of the units sit at or below $100k of AGI and pay 0–9% on these distributions, so assuming statutory long-term rates overstates the tax attributable for most units. Nearly half the tax comes from the $200k-and-up bands, which hold about a quarter of the dollars.
- The zero-payer share is not monotonic in income (92%, then 26%, then 45% across the $0–$200k bands), partly because the 0% capital gains bracket runs on taxable income with thresholds that differ by filing status ($98,900 joint, $49,450 single, $66,200 head of household in 2026, per Rev. Proc. 25-32).
- About a quarter of the $1.2B is paid by units whose distributions alone would fit inside the 0% bracket — the distributions push other income and gains into taxed territory (see `analysis/zero_bracket_check.py` for the statutory-proxy vs. full-system comparison).

## Scope caveats

1. **Reinvestment is unobservable on tax returns**, and §1046 covers only automatically reinvested distributions. These totals are the direct-route base, not the bill-eligible base; a reinvestment fraction applies on top. ICI's industry figures ($245.5B of long-term fund capital gain distributions paid, $234.0B reinvested, 2023 — [Fact Book table 30](https://www.icifactbook.org/xls/26-fb-table-30.xlsx)) span all account types including retirement and include short-term distributions, so they are broad aggregates rather than a taxable base.
2. **The Schedule D route is bigger and its income-class split is not yet known.** The 6× SOCA ratio is a TY2015 benchmark, not a 2026 gross-up factor, and the direct-route effective rates should not be transferred to it.
3. **A revenue score is a timing exercise this repo does not attempt**: NPV of deferred tax against recapture at sale and death, which turns on returns, rates at recognition, sale and mortality timing, and the discount rate.

## Data note

Computed on the policyengine-us 1.775.8 pinned default dataset (Microcosm US 2024, revision `populace-us-2024-c86a631-…-20260619`), where the direct-route base matches SOI Pub 1304 Table 1.4 concepts. Do not rerun on the unpinned HF-latest Microcosm artifact until [microcosm#462](https://github.com/PolicyEngine/microcosm/issues/462) is resolved — that release carries a known defect inflating `non_sch_d_capital_gains` roughly 7×.

## Reproduce

```bash
uv venv && uv pip install -e .
.venv/bin/python analysis/by_agi_class.py      # the table + CSV + metadata
.venv/bin/python analysis/aggregates.py        # national aggregates
.venv/bin/python analysis/zero_bracket_check.py  # bracket-proxy vs full-system comparison
```

First run downloads the pinned dataset from Hugging Face.
