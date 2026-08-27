{{ config(materialized='table', schema='bronze', meta={'grain': 'claim_id', 'data_use_class': 'PATIENT_RESTRICTED'}) }}
select * from {{ source('landing', 'sp_copay') }}
