{{ config(materialized='table', schema='bronze', meta={'grain': 'dispense_id', 'data_use_class': 'PATIENT_RESTRICTED'}) }}
select * from {{ source('landing', 'sp_dispense') }}
