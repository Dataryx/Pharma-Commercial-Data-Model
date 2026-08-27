{{
  config(
    materialized='table',
    schema='mdm',
    meta={'grain': 'hcp_key', 'data_use_class': 'IC_ELIGIBLE', 'owner': 'mdm-steward'}
  )
}}

-- Published by pcdm load (Python MDM); dbt re-materializes for lineage
select * from mdm.hcp_golden_raw
