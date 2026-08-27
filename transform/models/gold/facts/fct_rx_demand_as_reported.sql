{{ config(materialized='view', schema='gold', meta={'data_use_class': 'IC_ELIGIBLE'}) }}

-- Immutable as-reported presentation of demand fact
select * from {{ ref('fct_rx_demand') }}
