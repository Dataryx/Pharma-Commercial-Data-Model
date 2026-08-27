{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'patient_token_1, product_id, fill_seq_derived', 'data_use_class': 'PATIENT_RESTRICTED'}
  )
}}

select
    patient_token_1,
    patient_token_2,
    product_id,
    fill_seq_derived,
    quantity,
    days_supply,
    copay_amount as copay,
    assistance_amount as assistance,
    is_first_fill,
    is_free_goods_flag as is_free_goods,
    ship_date,
    dispense_date,
    payer_type,
    plan_id,
    sp_pharmacy_id,
    prescriber_npi
from {{ ref('sv_sp_dispense') }}
where not coalesce(is_free_goods_flag, false)
