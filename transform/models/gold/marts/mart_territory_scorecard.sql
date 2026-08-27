{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'territory_id, product_id, ic_period', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

with actuals as (
    select
        territory_id,
        product_key as product_id,
        sum(trx_count) as actual_trx
    from {{ ref('fct_rx_demand') }}
    where product_key = '{{ var("brand_product_id") }}'
      and not is_suppressed
    group by 1, 2
),
goals as (
    select * from {{ ref('br_targets') }}
)

select
    coalesce(g.territory_id, a.territory_id) as territory_id,
    coalesce(g.product_id, a.product_id) as product_id,
    coalesce(g.ic_period, '2024Q2') as ic_period,
    g.goal_trx as goal,
    a.actual_trx as actual,
    a.actual_trx / nullif(g.goal_trx, 0) as attainment_pct,
    rank() over (order by coalesce(a.actual_trx, 0) desc) as national_rank
from goals g
full outer join actuals a using (territory_id, product_id)
