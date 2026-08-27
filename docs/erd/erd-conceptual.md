# Conceptual ERD

```mermaid
erDiagram
    DIM_HCP ||--o{ FCT_RX_DEMAND : prescribes
    DIM_PRODUCT ||--o{ FCT_RX_DEMAND : of_product
    DIM_TERRITORY ||--o{ FCT_RX_DEMAND : aligned_to
    DIM_OUTLET ||--o{ FCT_SHIPMENT : ships_to
    DIM_HCP ||--o{ FCT_SP_DISPENSE : prescribes
    DIM_HCP }o--o{ DIM_HCO : affiliated
    MDM_HCP_XREF }o--|| DIM_HCP : resolves_to
```
