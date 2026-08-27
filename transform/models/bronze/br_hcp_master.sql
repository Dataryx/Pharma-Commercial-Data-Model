{{ config(materialized='table', schema='bronze', meta={'grain': 'source_record_id', 'data_use_class': 'IC_ELIGIBLE'}) }}
select * from {{ source('landing', 'hcp_master') }}
