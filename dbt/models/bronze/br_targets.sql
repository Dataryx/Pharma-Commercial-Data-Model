{{ config(materialized='table', schema='bronze', meta={'grain': 'territory_id, product_id, ic_period', 'data_use_class': 'IC_ELIGIBLE'}) }}
select * from {{ source('landing', 'targets') }}
