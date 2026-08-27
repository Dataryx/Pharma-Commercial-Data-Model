{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'territory_id', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

/*
  As-reported uses alignment stamped on fct_rx_demand.
  Current alignment re-resolves via latest assignment version (max valid_from).
*/
with as_reported as (
    select
        territory_id,
        sum(trx_count) as trx_as_reported
    from {{ ref('fct_rx_demand') }}
    where product_key = '{{ var("brand_product_id") }}'
      and not is_suppressed
    group by 1
),
current_map as (
    select hcp_key, territory_id
    from (
        select
            hcp_key,
            territory_id,
            row_number() over (partition by hcp_key order by valid_from desc) as rn
        from {{ ref('sv_hcp_territory_assignment') }}
        where overlay_id = 'PRIMARY'
    ) q
    where rn = 1
),
current_aligned as (
    select
        coalesce(c.territory_id, 'UNALIGNED') as territory_id,
        sum(f.trx_count) as trx_current_alignment
    from {{ ref('fct_rx_demand') }} f
    left join current_map c on c.hcp_key = f.hcp_key
    where f.product_key = '{{ var("brand_product_id") }}'
      and not f.is_suppressed
    group by 1
)

select
    coalesce(a.territory_id, c.territory_id) as territory_id,
    a.trx_as_reported,
    c.trx_current_alignment,
    coalesce(c.trx_current_alignment, 0) - coalesce(a.trx_as_reported, 0) as trx_delta
from as_reported a
full outer join current_aligned c using (territory_id)
