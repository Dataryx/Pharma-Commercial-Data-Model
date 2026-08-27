{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'week_ending, product_key, outlet_type', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

select
    ship_date as week_ending,
    product_key,
    coalesce(class_of_trade, 'UNKNOWN') as outlet_type,
    sum(eaches) as shipped_in,
    cast(0 as decimal(18, 4)) as dispensed_out,
    sum(eaches) as derived_on_hand,
    cast(null as double) as days_on_hand
from {{ ref('fct_shipment') }}
group by 1, 2, 3
