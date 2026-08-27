{{ config(materialized='table', schema='bronze', meta={'grain': 'patient_token_1, status_code, status_date, seq', 'data_use_class': 'PATIENT_RESTRICTED'}) }}
select * from {{ source('landing', 'sp_status_history') }}
