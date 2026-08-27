# Data-use guardrails

| Class | Meaning |
|---|---|
| `COMMERCIAL_UNRESTRICTED` | Aggregates OK for broad use |
| `IC_ELIGIBLE` | May feed incentive compensation |
| `PATIENT_RESTRICTED` | Tokenized patient-level; not for IC |
| `PAYER_RESTRICTED` | Formulary / access sensitive |
| `340B_RESTRICTED` | Covered-entity sensitive |

Enforced by model `meta.data_use_class` and `tests/compliance/test_data_use_lineage.py`.

Patients exist only as `patient_token_1` / `patient_token_2`. `MIN_CELL_SIZE` default 5.
