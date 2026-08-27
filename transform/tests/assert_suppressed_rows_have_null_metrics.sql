select *
from {{ ref('sv_rx_demand') }}
where suppression_flag = 'Y'
  and (
      trx_count is not null
      or nrx_count is not null
      or rrx_count is not null
  )
