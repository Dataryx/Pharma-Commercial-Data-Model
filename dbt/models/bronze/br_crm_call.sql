{{ config(materialized='table', schema='bronze', meta={'grain': 'call_id', 'data_use_class': 'IC_ELIGIBLE'}) }}
select * from {{ source('landing', 'crm_call') }}
