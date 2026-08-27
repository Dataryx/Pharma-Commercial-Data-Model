{{
  config(
    materialized='table',
    schema='silver',
    meta={'grain': 'prescriber_id, product_id, market_id, geo_id, pay_type, period_end_date, restatement_version',
          'data_use_class': 'IC_ELIGIBLE', 'owner': 'commercial-data-eng'}
  )
}}

with ranked as (
    select
        *,
        max(restatement_version) over (
            partition by prescriber_id, product_id, market_id, geo_id, pay_type, period_end_date
        ) as max_restatement_version
    from {{ ref('br_rx_demand') }}
)

select
    *,
    restatement_version = max_restatement_version as is_current_restatement,
    case
        when suppression_flag = 'Y' then true
        else false
    end as is_suppressed
from ranked
