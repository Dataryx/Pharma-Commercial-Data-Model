-- Alignment weights must sum to 1 per overlay/basis_key/valid_from
select
    overlay_id,
    alignment_basis,
    basis_key,
    valid_from,
    abs(sum(weight) - 1.0) as drift
from {{ ref('sv_alignment') }}
group by 1, 2, 3, 4
having abs(sum(weight) - 1.0) > 1e-6
