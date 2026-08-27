{{ config(materialized='table', schema='bronze', meta={'grain': 'rep_id, territory_id, valid_from', 'data_use_class': 'IC_ELIGIBLE'}) }}
select * from {{ source('landing', 'roster') }}
