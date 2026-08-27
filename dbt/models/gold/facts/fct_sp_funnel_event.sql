{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'patient_token_1', 'data_use_class': 'PATIENT_RESTRICTED'}
  )
}}

select
    patient_token_1,
    referral_date,
    enrollment_date,
    bv_date,
    pa_date,
    approved_date,
    first_ship_date,
    discontinued_date,
    time_to_therapy_days,
    case when referral_date is not null then 1 else 0 end as reached_referral,
    case when enrollment_date is not null then 1 else 0 end as reached_enrollment,
    case when bv_date is not null then 1 else 0 end as reached_bv,
    case when pa_date is not null then 1 else 0 end as reached_pa,
    case when first_ship_date is not null then 1 else 0 end as reached_first_ship
from {{ ref('sv_sp_patient_journey') }}
