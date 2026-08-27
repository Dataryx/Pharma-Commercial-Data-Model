{{ config(materialized='table', schema='bronze', meta={'grain': 'hco_id', 'data_use_class': 'IC_ELIGIBLE'}) }}
select * from {{ source('landing', 'hco_master') }}
