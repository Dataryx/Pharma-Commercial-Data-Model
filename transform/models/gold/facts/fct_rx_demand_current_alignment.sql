{{ config(materialized='view', schema='gold', meta={'data_use_class': 'IC_ELIGIBLE'}) }}

with current_map as (
    select hcp_key, territory_id, weight
    from (
        select
            hcp_key,
            territory_id,
            weight,
            row_number() over (partition by hcp_key order by valid_from desc) as rn
        from {{ ref('sv_hcp_territory_assignment') }}
        where overlay_id = 'PRIMARY'
    ) q
    where rn = 1
)

select
    f.* exclude (territory_id, alignment_weight),
    coalesce(c.territory_id, 'UNALIGNED') as territory_id,
    coalesce(c.weight, 1.0) as alignment_weight
from {{ ref('fct_rx_demand') }} f
left join current_map c on c.hcp_key = f.hcp_key
