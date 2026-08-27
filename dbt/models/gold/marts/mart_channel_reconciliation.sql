{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'week_ending, product_key', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

with demand as (
    select
        period_end_date as week_ending,
        product_key,
        sum(trx_units) as demand_units
    from {{ ref('fct_rx_demand') }}
    where not is_suppressed
    group by 1, 2
),
ship as (
    select
        ship_date as week_ending,
        product_key,
        sum(standard_units) as sales_out_units
    from {{ ref('fct_shipment') }}
    group by 1, 2
),
sp as (
    select
        cast(ship_date as date) as week_ending,
        product_id as product_key,
        sum(quantity) as sp_units
    from {{ ref('fct_sp_dispense') }}
    group by 1, 2
)

select
    coalesce(d.week_ending, s.week_ending, p.week_ending) as week_ending,
    coalesce(d.product_key, s.product_key, p.product_key) as product_key,
    d.demand_units,
    s.sales_out_units,
    p.sp_units,
    coalesce(s.sales_out_units, 0) - coalesce(d.demand_units, 0) as sales_out_minus_demand,
    sum(coalesce(s.sales_out_units, 0) - coalesce(d.demand_units, 0) - coalesce(p.sp_units, 0))
        over (partition by coalesce(d.product_key, s.product_key, p.product_key) order by coalesce(d.week_ending, s.week_ending, p.week_ending))
        as cumulative_inventory_proxy,
    'Stocking lag, returns, specialty channel gap, and projection explain variance' as variance_notes
from demand d
full outer join ship s using (week_ending, product_key)
full outer join sp p using (week_ending, product_key)
