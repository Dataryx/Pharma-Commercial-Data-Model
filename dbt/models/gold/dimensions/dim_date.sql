{{ config(materialized='table', schema='gold', meta={'grain': 'date_key', 'data_use_class': 'COMMERCIAL_UNRESTRICTED'}) }}

with bounds as (
    select
        min(period_end_date) as d0,
        max(period_end_date) as d1
    from {{ ref('sv_rx_demand') }}
),
spine as (
    select unnest(generate_series(d0, d1, interval '1 day'))::date as date_day
    from bounds
)

select
    cast(strftime(date_day, '%Y%m%d') as integer) as date_key,
    date_day as date_actual,
    extract('year' from date_day) as year,
    extract('month' from date_day) as month,
    extract('quarter' from date_day) as quarter,
    cast(extract('year' from date_day) as varchar) || '-Q' || cast(extract('quarter' from date_day) as varchar) as fiscal_quarter,
    case when extract('dow' from date_day) = 5 then true else false end as is_week_ending_friday
from spine
