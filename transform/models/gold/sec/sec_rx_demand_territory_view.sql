{{ config(materialized='view', schema='sec', meta={'data_use_class': 'COMMERCIAL_UNRESTRICTED'}) }}

-- Demo RLS pattern: filter to territories granted in sec_user_territory_access.
-- Production: replace literal with session-scoped user id from the BI tool or middleware.
select f.*
from {{ ref('fct_rx_demand') }} f
join {{ ref('sec_user_territory_access') }} a
  on a.territory_id = f.territory_id
where a.user_id = 'rep_demo'
