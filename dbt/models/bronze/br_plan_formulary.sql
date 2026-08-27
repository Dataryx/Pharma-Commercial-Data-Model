{{ config(materialized='table', schema='bronze', meta={'grain': 'plan_id, product_id, valid_from', 'data_use_class': 'PAYER_RESTRICTED'}) }}
select * from {{ source('landing', 'plan_formulary') }}
