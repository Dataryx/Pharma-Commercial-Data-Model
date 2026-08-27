select *
from {{ ref('mart_brand_performance_weekly') }}
where trx_share is not null
  and (trx_share < 0 or trx_share > 1.000001)
