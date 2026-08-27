{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'period_end_date, territory_id, product_key', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

with weekly as (
    select
        f.period_end_date,
        f.territory_id,
        f.product_key,
        p.is_brand,
        sum(case when not f.is_suppressed then f.trx_count end) as trx,
        sum(case when not f.is_suppressed then f.nrx_count end) as nrx,
        sum(case when not f.is_suppressed then f.rrx_count end) as rrx
    from {{ ref('fct_rx_demand') }} f
    join {{ ref('dim_product') }} p on p.product_key = f.product_key
    where f.market_id = '{{ var("market_id") }}'
    group by 1, 2, 3, 4
),
market as (
    select
        period_end_date,
        territory_id,
        sum(trx) as market_trx,
        sum(nrx) as market_nrx
    from weekly
    group by 1, 2
),
brand as (
    select * from weekly where is_brand
)

select
    b.period_end_date,
    b.territory_id,
    b.product_key,
    b.trx as brand_trx,
    b.nrx as brand_nrx,
    b.rrx as brand_rrx,
    m.market_trx,
    m.market_nrx,
    b.trx / nullif(m.market_trx, 0) as trx_share,
    b.nrx / nullif(m.market_nrx, 0) as nrx_share,
    case
        when count(*) over (
            partition by b.territory_id, b.product_key
            order by b.period_end_date
            rows between 12 preceding and current row
        ) = 13
        then sum(b.trx) over (
            partition by b.territory_id, b.product_key
            order by b.period_end_date
            rows between 12 preceding and current row
        )
    end as brand_trx_r13,
    case
        when count(*) over (
            partition by b.territory_id, b.product_key
            order by b.period_end_date
            rows between 51 preceding and current row
        ) = 52
        then sum(b.trx) over (
            partition by b.territory_id, b.product_key
            order by b.period_end_date
            rows between 51 preceding and current row
        )
    end as brand_trx_mat,
    lag(b.trx) over (partition by b.territory_id, b.product_key order by b.period_end_date) as prior_trx,
    (b.trx - lag(b.trx) over (partition by b.territory_id, b.product_key order by b.period_end_date))
        / nullif(lag(b.trx) over (partition by b.territory_id, b.product_key order by b.period_end_date), 0) as growth_pct
from brand b
join market m using (period_end_date, territory_id)
