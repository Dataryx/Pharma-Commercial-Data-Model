{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'call_id', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

select
    call_id,
    cast(call_date as date) as call_date,
    rep_id,
    account_hcp_id,
    product_id,
    detail_position,
    duration_minutes,
    1 as call_count
from {{ ref('sv_call_activity') }}
