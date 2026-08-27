{{
  config(
    materialized='table',
    schema='silver',
    meta={'grain': 'patient_token_1, rx_number, fill_seq_derived', 'data_use_class': 'PATIENT_RESTRICTED'}
  )
}}

with base as (
    select
        *,
        row_number() over (
            partition by patient_token_1, product_id
            order by cast(ship_date as date), dispense_id
        ) as fill_seq_derived
    from {{ ref('br_sp_dispense') }}
)

select
    *,
    cast(is_free_goods as boolean) as is_free_goods_flag,
    fill_seq_derived = 1 as is_first_fill
from base
