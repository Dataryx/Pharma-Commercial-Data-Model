{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'plan_id, product_id', 'data_use_class': 'PAYER_RESTRICTED'}
  )
}}

select
    plan_id,
    product_id,
    tier,
    pa_required,
    step_edit,
    valid_from_date,
    valid_to_date,
    is_current
from {{ ref('sv_plan_formulary') }}
where coalesce(is_current, true)
