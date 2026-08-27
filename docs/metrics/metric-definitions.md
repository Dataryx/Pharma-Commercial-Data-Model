# Metric definitions

| Metric | Definition | Caveats |
|---|---|---|
| **TRx** | Sum of projected `trx_count` | Decimal; dispensed/projected retail, not written |
| **NRx** | Sum of `nrx_count` | Includes new-to-brand and switches at Rx level |
| **RRx** | Sum of `rrx_count` | `TRx = NRx + RRx` enforced |
| **NBRx** | Patients with no brand dispense in prior 12 months | **Specialty only** — cannot be derived from projected demand |
| **TRx share** | brand_trx / market_basket_trx | Must be in [0,1]; basket must sum to 1 |
| **R13 / MAT** | Trailing 13 / 52 weeks | Null if window incomplete |
| **EI** | brand growth index / market growth index × 100 | Documented for extension |
| **Sales-out** | 867 standard units | Not demand |
| **TTT** | Days referral → first ship | Report median/P90 |

Worked demo numbers are produced by `mart_brand_performance_weekly` after `pcdm all --scale demo --seed 42`.
