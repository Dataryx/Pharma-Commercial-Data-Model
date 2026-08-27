{{
  config(
    materialized='table',
    schema='gold',
    meta={
      'grain': 'hcp_key, product_key, market_id, geography_key, pay_type_key, date_key, alignment_version_id',
      'data_use_class': 'IC_ELIGIBLE',
      'owner': 'commercial-data-eng'
    }
  )
}}

with demand as (
    select *
    from {{ ref('sv_rx_demand') }}
    where is_current_restatement
),
-- resolve vendor prescriber_id -> hcp_key via xref (RXD source ids)
xref as (
    select
        source_record_id,
        hcp_key
    from {{ ref('mdm_hcp_xref') }}
    where source_system = 'rx_demand'
),
aligned as (
    select
        d.*,
        coalesce(x.hcp_key, 'UNMATCHED') as hcp_key,
        a.territory_id,
        a.weight as alignment_weight,
        a.alignment_version_id,
        a.overlay_id
    from demand d
    left join xref x on x.source_record_id = d.prescriber_id
    left join {{ ref('sv_hcp_territory_assignment') }} a
      on a.hcp_key = coalesce(x.hcp_key, 'UNMATCHED')
     and a.overlay_id = 'PRIMARY'
     and d.period_end_date >= a.valid_from
     and d.period_end_date < a.valid_to
)

select
    hcp_key,
    product_id as product_key,
    market_id,
    geo_id as geography_key,
    pay_type as pay_type_key,
    cast(strftime(period_end_date, '%Y%m%d') as integer) as date_key,
    period_end_date,
    coalesce(alignment_version_id, 'ALN_UNKNOWN') as alignment_version_id,
    coalesce(territory_id, 'UNALIGNED') as territory_id,
    coalesce(alignment_weight, 1.0) as alignment_weight,
    coalesce(overlay_id, 'PRIMARY') as overlay_id,
    trx_count * coalesce(alignment_weight, 1.0) as trx_count,
    nrx_count * coalesce(alignment_weight, 1.0) as nrx_count,
    rrx_count * coalesce(alignment_weight, 1.0) as rrx_count,
    trx_units * coalesce(alignment_weight, 1.0) as trx_units,
    trx_dollars * coalesce(alignment_weight, 1.0) as trx_dollars,
    projection_factor,
    suppression_flag,
    is_suppressed,
    restatement_version
from aligned
