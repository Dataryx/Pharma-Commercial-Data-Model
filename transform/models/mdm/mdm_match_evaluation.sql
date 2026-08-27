{{
  config(
    materialized='table',
    schema='mdm',
    meta={'grain': 'metric_row', 'data_use_class': 'COMMERCIAL_UNRESTRICTED'}
  )
}}

select * from mdm.match_evaluation
