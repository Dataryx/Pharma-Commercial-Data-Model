{{ config(materialized='table', schema='bronze', meta={'grain': 'sp_pharmacy_id, ndc11, inventory_date', 'data_use_class': 'COMMERCIAL_UNRESTRICTED'}) }}
select * from {{ source('landing', 'sp_inventory') }}
