{{ config(materialized='table', schema='bronze', meta={'grain': 'pa_case_id', 'data_use_class': 'PATIENT_RESTRICTED'}) }}
select * from {{ source('landing', 'sp_prior_auth') }}
