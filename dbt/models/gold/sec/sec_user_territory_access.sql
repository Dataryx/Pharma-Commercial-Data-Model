{{ config(materialized='table', schema='sec') }}

select * from {{ ref('sec_user_territory_access') }}
