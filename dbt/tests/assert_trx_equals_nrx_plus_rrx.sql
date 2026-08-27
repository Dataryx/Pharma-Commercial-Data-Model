-- Assert TRx = NRx + RRx on current non-suppressed silver demand
select *
from {{ ref('sv_rx_demand') }}
where suppression_flag = 'N'
  and abs(coalesce(trx_count, 0) - (coalesce(nrx_count, 0) + coalesce(rrx_count, 0))) >= 0.001
