{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'milestone', 'data_use_class': 'PATIENT_RESTRICTED'}
  )
}}

with base as (
    select * from {{ ref('fct_sp_funnel_event') }}
),
counts as (
    select
        count(*) as n_referral,
        sum(reached_enrollment) as n_enrollment,
        sum(reached_bv) as n_bv,
        sum(reached_pa) as n_pa,
        sum(reached_first_ship) as n_first_ship,
        median(time_to_therapy_days) as median_ttt_days,
        quantile_cont(time_to_therapy_days, 0.9) as p90_ttt_days
    from base
)

select
    'funnel' as grain_id,
    n_referral,
    n_enrollment,
    n_bv,
    n_pa,
    n_first_ship,
    n_enrollment / nullif(n_referral, 0) as conv_referral_to_enroll,
    n_bv / nullif(n_enrollment, 0) as conv_enroll_to_bv,
    n_pa / nullif(n_bv, 0) as conv_bv_to_pa,
    n_first_ship / nullif(n_pa, 0) as conv_pa_to_ship,
    n_first_ship / nullif(n_referral, 0) as conv_cumulative_to_ship,
    median_ttt_days,
    p90_ttt_days,
    case when n_referral < {{ var('min_cell_size') }} then true else false end as is_suppressed
from counts
