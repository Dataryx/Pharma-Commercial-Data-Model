{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'territory_id, product_id, ic_period', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

select * from {{ ref('mart_territory_scorecard') }}
