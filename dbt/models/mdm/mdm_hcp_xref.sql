{{
  config(
    materialized='table',
    schema='mdm',
    meta={'grain': 'source_system, source_record_id', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

select * from mdm.hcp_xref_raw
