select *
from {{ ref('mart_specialty_funnel') }}
where is_suppressed = false
  and n_referral < {{ var('min_cell_size') }}
