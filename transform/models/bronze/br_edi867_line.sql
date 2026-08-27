{{
  config(
    materialized='table',
    schema='bronze',
    meta={'grain': 'interchange_control_number, transaction_set_control_number, line_number',
          'owner': 'commercial-data-eng', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

select
    cast(interchange_control_number as varchar) as interchange_control_number,
    cast(group_control_number as varchar) as group_control_number,
    cast(transaction_set_control_number as varchar) as transaction_set_control_number,
    cast(report_id as varchar) as report_id,
    cast(report_date as date) as report_date,
    cast(report_purpose_code as varchar) as report_purpose_code,
    cast(line_number as integer) as line_number,
    cast(transfer_type_code as varchar) as transfer_type_code,
    cast(ndc11 as varchar) as ndc11,
    cast(product_id as varchar) as product_id,
    cast(quantity as decimal(18, 4)) as quantity,
    cast(quantity_uom as varchar) as quantity_uom,
    cast(unit_price_wac as decimal(18, 4)) as unit_price_wac,
    cast(ship_date as date) as ship_date,
    cast(invoice_number as varchar) as invoice_number,
    cast(shipto_dea as varchar) as shipto_dea,
    cast(shipto_hin as varchar) as shipto_hin,
    cast(shipto_340b_id as varchar) as shipto_340b_id,
    cast(shipto_name as varchar) as shipto_name,
    cast(shipto_address as varchar) as shipto_address,
    cast(shipto_city as varchar) as shipto_city,
    cast(shipto_state as varchar) as shipto_state,
    cast(shipto_zip as varchar) as shipto_zip,
    cast(class_of_trade as varchar) as class_of_trade,
    cast(wholesaler_id as varchar) as wholesaler_id,
    cast(is_return as boolean) as is_return,
    _batch_id,
    _loaded_at,
    _source_file,
    _record_status,
    _reject_reason
from {{ source('landing', 'edi867_line') }}
