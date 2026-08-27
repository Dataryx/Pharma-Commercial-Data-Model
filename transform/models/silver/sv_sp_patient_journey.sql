{{
  config(
    materialized='table',
    schema='silver',
    meta={'grain': 'patient_token_1', 'data_use_class': 'PATIENT_RESTRICTED'}
  )
}}

with pivoted as (
    select
        patient_token_1,
        min(case when status_code = 'REFERRAL' then cast(status_date as date) end) as referral_date,
        min(case when status_code = 'ENROLLMENT' then cast(status_date as date) end) as enrollment_date,
        min(case when status_code = 'BV' then cast(status_date as date) end) as bv_date,
        min(case when status_code = 'PA' then cast(status_date as date) end) as pa_date,
        min(case when status_code = 'APPROVED' then cast(status_date as date) end) as approved_date,
        min(case when status_code = 'FIRST_SHIP' then cast(status_date as date) end) as first_ship_status_date,
        min(case when status_code = 'DISCONTINUED' then cast(status_date as date) end) as discontinued_date
    from {{ ref('br_sp_status_history') }}
    group by 1
),
ships as (
    select
        patient_token_1,
        min(cast(ship_date as date)) as first_ship_date
    from {{ ref('sv_sp_dispense') }}
    where not coalesce(is_free_goods_flag, false)
    group by 1
)

select
    p.*,
    s.first_ship_date,
    date_diff('day', p.referral_date, s.first_ship_date) as time_to_therapy_days
from pivoted p
left join ships s using (patient_token_1)
