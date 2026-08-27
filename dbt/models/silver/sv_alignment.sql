{{
  config(
    materialized='table',
    schema='silver',
    meta={'grain': 'overlay_id, alignment_basis, basis_key, territory_id, valid_from',
          'data_use_class': 'IC_ELIGIBLE'}
  )
}}

with unioned as (
    select * from {{ ref('br_alignment_zip') }}
    union all
    select * from {{ ref('br_alignment_account') }}
    union all
    select * from {{ ref('br_alignment_prescriber') }}
),
-- quarantine injected overlaps: keep first row per key+territory+valid_from
dedup as (
    select
        *,
        row_number() over (
            partition by overlay_id, alignment_basis, basis_key, territory_id, valid_from
            order by change_reason
        ) as rn
    from unioned
)

select
    * exclude (rn),
    cast(valid_from as date) as valid_from_date,
    cast(valid_to as date) as valid_to_date,
    true as is_current
from dedup
where rn = 1
  and coalesce(change_reason, '') != 'INJECTED_OVERLAP'
