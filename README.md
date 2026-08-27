# Pharma Commercial Data Model (PCDM)

Synthetic, reproducible **pharma commercial data warehouse** reference implementation:
Xponent-*style* demand (`rx_demand`), EDI 867 sales-out, specialty pharmacy funnel, HCP/HCO MDM,
territory alignment (as-reported vs current), and tested metric marts.

## Quickstart (Windows / any OS)

```bash
python -m pip install -e ".[dev]"
python -m pcdm all --scale demo --seed 42
python -m streamlit run app/Home.py
```

Or with GNU Make (Git Bash / Linux / macOS):

```bash
make setup
make all SCALE=demo SEED=42
make demo
```

No cloud credentials required. DuckDB warehouse lands in `warehouse/pcdm.duckdb`.

## What makes this pharma-specific

- **Demand ≠ shipments ≠ specialty dispenses** — reconciled in `mart_channel_reconciliation`
- **Projected decimals** and **historical restatements** on `rx_demand`
- **NPI is not a reliable PK** — MDM match-merge + survivorship
- **Alignment restatement** — IC as-reported vs current structure
- **Tokenized patients**, `MIN_CELL_SIZE` suppression, data-use classes

## Architecture

See [docs/architecture.md](docs/architecture.md). Medallion layers: `landing → bronze → silver → mdm → gold → semantic`.

## Six analyst questions

Answered in the Streamlit demo and [notebooks/demo.ipynb](notebooks/demo.ipynb):

1. Brand TRx/NRx/share by geo / territory / payer
2. Growing / declining / switching writers + call activity
3. Demand vs 867 vs SP + channel inventory
4. Specialty funnel drop-off
5. As-reported vs current alignment impact
6. MDM golden record / survivorship

## Synthetic data only

Generator: `python -m pcdm generate --scale demo|small|large --seed 42`  
ZIP space is synthetic `9xxxx`. No real IQVIA/NPPES/patient data.
