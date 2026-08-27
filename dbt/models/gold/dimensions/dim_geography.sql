{{ config(materialized='table', schema='gold', meta={'grain': 'geography_key', 'data_use_class': 'IC_ELIGIBLE'}) }}

select distinct
    geo_id as geography_key,
    geo_type,
    geo_id,
    geo_id as zip5
from {{ ref('sv_rx_demand') }}
