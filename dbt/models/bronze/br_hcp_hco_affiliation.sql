{{ config(materialized='table', schema='bronze', meta={'grain': 'entity_id, hco_id, valid_from', 'data_use_class': 'IC_ELIGIBLE'}) }}
select * from {{ source('landing', 'hcp_hco_affiliation') }}
