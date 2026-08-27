{{
  config(
    materialized='table',
    schema='silver',
    meta={'grain': 'rep_id, territory_id, valid_from', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

select
    *,
    coalesce(is_vacant, false) as is_vacant_flag
from {{ ref('br_roster') }}
