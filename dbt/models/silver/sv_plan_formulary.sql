{{
  config(
    materialized='table',
    schema='silver',
    meta={'grain': 'plan_id, product_id, valid_from', 'data_use_class': 'PAYER_RESTRICTED'}
  )
}}

select
    *,
    cast(valid_from as date) as valid_from_date,
    cast(valid_to as date) as valid_to_date
from {{ ref('br_plan_formulary') }}
