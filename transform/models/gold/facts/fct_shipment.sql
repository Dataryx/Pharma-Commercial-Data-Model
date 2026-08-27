{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'outlet_key, product_key, ship_date, invoice_line', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

select
    coalesce(shipto_dea, shipto_hin, 'UNRESOLVED_OUTLET') as outlet_key,
    coalesce(product_id_resolved, product_id) as product_key,
    ship_date,
    invoice_number || '-' || cast(line_number as varchar) as invoice_line,
    quantity_eaches as eaches,
    case when quantity_uom = 'PK' then quantity else quantity / nullif(1, 0) end as packs,
    standard_units,
    quantity * unit_price_wac as wac_amount,
    cast(null as decimal(18, 2)) as contract_amount,
    case when transfer_type_code = 'CB' then unit_price_wac else 0 end as chargeback_amount,
    is_return as return_flag,
    class_of_trade,
    shipto_340b_id is not null as is_340b_shipto,
    is_chargeback_only,
    interchange_control_number,
    wholesaler_id
from {{ ref('sv_shipment_line') }}
where not is_chargeback_only
