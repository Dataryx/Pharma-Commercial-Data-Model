{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'hcp_key', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

with vol as (
    select
        hcp_key,
        sum(case when product_key = '{{ var("brand_product_id") }}' and not is_suppressed then trx_count end) as brand_trx,
        sum(case when not is_suppressed then trx_count end) as market_trx
    from {{ ref('fct_rx_demand') }}
    group by 1
),
calls as (
    select
        account_hcp_id as entity_id,
        count(*) as call_count
    from {{ ref('fct_call_activity') }}
    group by 1
),
xref as (
    select distinct entity_id_truth as entity_id, hcp_key
    from {{ ref('mdm_hcp_xref') }}
    where entity_id_truth is not null
)

select
    h.hcp_key,
    h.npi,
    h.first_name,
    h.last_name,
    h.specialty_code,
    h.practice_zip5,
    h.practice_state,
    v.brand_trx,
    v.market_trx,
    v.brand_trx / nullif(v.market_trx, 0) as brand_share,
    ntile(10) over (order by coalesce(v.brand_trx, 0)) as volume_decile,
    coalesce(c.call_count, 0) as call_count,
    a.territory_id,
    a.alignment_version_id
from {{ ref('dim_hcp') }} h
left join vol v using (hcp_key)
left join xref x on x.hcp_key = h.hcp_key
left join calls c on c.entity_id = x.entity_id
left join (
    select hcp_key, territory_id, alignment_version_id,
           row_number() over (partition by hcp_key order by valid_from desc) as rn
    from {{ ref('sv_hcp_territory_assignment') }}
    where overlay_id = 'PRIMARY'
) a on a.hcp_key = h.hcp_key and a.rn = 1
