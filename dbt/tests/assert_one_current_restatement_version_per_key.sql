-- Exactly one current restatement version flag per natural key
select
    prescriber_id, product_id, market_id, geo_id, pay_type, period_end_date,
    count(*) as n_current
from {{ ref('sv_rx_demand') }}
where is_current_restatement
group by 1, 2, 3, 4, 5, 6
having count(*) <> 1
