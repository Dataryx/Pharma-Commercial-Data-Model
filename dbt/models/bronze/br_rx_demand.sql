{{
  config(
    materialized='table',
    schema='bronze',
    meta={'grain': 'prescriber_id, product_id, market_id, geo_id, pay_type, period_end_date, restatement_version',
          'owner': 'commercial-data-eng', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

-- Grain: prescriber × product × market × geo × pay_type × period × restatement_version
select
    data_supplier_id,
    period_type,
    cast(period_end_date as date) as period_end_date,
    cast(restatement_version as integer) as restatement_version,
    cast(delivery_date as date) as delivery_date,
    cast(prescriber_id as varchar) as prescriber_id,
    cast(me_number as varchar) as me_number,
    cast(npi as varchar) as npi,
    cast(dea_number as varchar) as dea_number,
    cast(product_id as varchar) as product_id,
    cast(ndc9 as varchar) as ndc9,
    cast(market_id as varchar) as market_id,
    cast(geo_type as varchar) as geo_type,
    cast(geo_id as varchar) as geo_id,
    cast(pay_type as varchar) as pay_type,
    cast(plan_id as varchar) as plan_id,
    cast(trx_count as decimal(18, 4)) as trx_count,
    cast(nrx_count as decimal(18, 4)) as nrx_count,
    cast(rrx_count as decimal(18, 4)) as rrx_count,
    cast(trx_units as decimal(18, 4)) as trx_units,
    cast(nrx_units as decimal(18, 4)) as nrx_units,
    cast(trx_dollars as decimal(18, 2)) as trx_dollars,
    cast(projection_factor as decimal(10, 6)) as projection_factor,
    cast(sample_flag as varchar) as sample_flag,
    cast(suppression_flag as varchar) as suppression_flag,
    _batch_id,
    _loaded_at,
    _source_file,
    _record_status,
    _reject_reason,
    _row_hash
from {{ source('landing', 'rx_demand') }}
