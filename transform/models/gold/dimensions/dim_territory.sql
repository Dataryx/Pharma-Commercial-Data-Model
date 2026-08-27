{{ config(materialized='table', schema='gold', meta={'grain': 'territory_key', 'data_use_class': 'IC_ELIGIBLE'}) }}

select
    territory_id as territory_key,
    territory_id,
    territory_name,
    level as territory_level,
    parent_territory_id,
    overlay_id,
    cast(is_active as boolean) as is_active
from {{ source('landing', 'territories') }}
