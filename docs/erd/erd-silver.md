# Silver / MDM ERD

```mermaid
erDiagram
    SV_RX_DEMAND ||--o{ FCT_RX_DEMAND : feeds
    SV_SHIPMENT_LINE ||--o{ FCT_SHIPMENT : feeds
    SV_SP_DISPENSE ||--o{ FCT_SP_DISPENSE : feeds
    SV_ALIGNMENT ||--o{ SV_HCP_TERRITORY_ASSIGNMENT : precedence
    MDM_HCP_GOLDEN ||--o{ MDM_HCP_XREF : clusters
    MDM_HCP_GOLDEN ||--|| DIM_HCP : publishes
```
