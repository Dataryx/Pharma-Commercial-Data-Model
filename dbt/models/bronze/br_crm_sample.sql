{{ config(materialized='table', schema='bronze', meta={'grain': 'sample_id', 'data_use_class': 'IC_ELIGIBLE'}) }}
select * from {{ source('landing', 'crm_sample') }}
