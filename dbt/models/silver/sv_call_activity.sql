{{
  config(
    materialized='table',
    schema='silver',
    meta={'grain': 'call_id', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

select distinct * from {{ ref('br_crm_call') }}
