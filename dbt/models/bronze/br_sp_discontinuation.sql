{{ config(materialized='table', schema='bronze', meta={'grain': 'patient_token_1, event_date', 'data_use_class': 'PATIENT_RESTRICTED'}) }}
select * from {{ source('landing', 'sp_discontinuation') }}
