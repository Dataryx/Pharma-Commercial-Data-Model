{{ config(materialized='table', schema='gold', meta={'grain': 'pay_type_key', 'data_use_class': 'IC_ELIGIBLE'}) }}

select distinct
    pay_type as pay_type_key,
    pay_type
from {{ ref('sv_rx_demand') }}
