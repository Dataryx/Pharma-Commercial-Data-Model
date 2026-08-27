{{
  config(
    materialized='table',
    schema='silver',
    meta={'grain': 'interchange_control_number, transaction_set_control_number, line_number',
          'data_use_class': 'IC_ELIGIBLE'}
  )
}}

with prod as (
    select distinct
        ndc11,
        product_id,
        units_per_pack,
        standard_units_factor
    from {{ source('landing', 'product_master') }}
)

select
    s.*,
    case
        when s.quantity_uom = 'PK' then s.quantity * coalesce(p.units_per_pack, 1)
        else s.quantity
    end as quantity_eaches,
    case
        when s.quantity_uom = 'PK' then s.quantity * coalesce(p.units_per_pack, 1) * coalesce(p.standard_units_factor, 1)
        else s.quantity * coalesce(p.standard_units_factor, 1)
    end as standard_units,
    coalesce(p.product_id, s.product_id) as product_id_resolved,
    case when s.transfer_type_code = 'CB' and coalesce(s.quantity, 0) = 0 then true else false end as is_chargeback_only
from {{ ref('br_edi867_line') }} s
left join prod p on {{ normalize_ndc('s.ndc11') }} = {{ normalize_ndc('p.ndc11') }}
