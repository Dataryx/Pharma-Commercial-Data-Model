{{ config(materialized='table', schema='gold', meta={'grain': 'hco_key', 'data_use_class': 'IC_ELIGIBLE'}) }}

select * from {{ ref('mdm_hco_golden') }}
