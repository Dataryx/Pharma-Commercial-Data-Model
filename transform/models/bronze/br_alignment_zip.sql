{{ config(materialized='table', schema='bronze', meta={'grain': 'overlay_id, basis_key, territory_id, valid_from', 'data_use_class': 'IC_ELIGIBLE'}) }}
select * from {{ source('landing', 'alignment_zip') }}
