# rx_demand — Xponent-style projected retail prescriptions

**Internal name:** `rx_demand` (Xponent-*style* lineage; not a proprietary layout copy).

**Grain:** prescriber × product × market × geo × pay_type × period_end × restatement_version

**Delivery:** pipe-delimited `RXD_<MARKET>_W_<YYYYMMDD>_v<restatement>.txt`

## Injected defects

| Defect | Rate | Handling |
|---|---|---|
| Unmatched prescriber | ~6% | `UNMATCHED` hcp_key |
| Invalid/missing NPI | ~4% | Luhn validation |
| Restatement of history | weekly v1/v2 | `is_current_restatement` |
| Suppression | low volume | null metrics + flag |
