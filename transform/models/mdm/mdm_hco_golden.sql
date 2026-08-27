{{
  config(
    materialized='table',
    schema='mdm',
    meta={'grain': 'hco_id', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

select
    hco_id as hco_key,
    hco_id,
    hco_name,
    class_of_trade,
    parent_hco_id,
    idn_id,
    gpo_id,
    is_340b,
    zip5,
    dea_number,
    hin,
    level
from {{ ref('br_hco_master') }}
