{{ config(materialized='table', schema='gold', meta={'grain': 'product_key', 'data_use_class': 'IC_ELIGIBLE'}) }}

select distinct
    product_id as product_key,
    product_id,
    product_name,
    cast(is_brand as boolean) as is_brand,
    ndc9,
    ndc11,
    strength,
    pack_size,
    units_per_pack,
    standard_units_factor
from {{ source('landing', 'product_master') }}
