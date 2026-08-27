{{ config(materialized='table', schema='gold', meta={'grain': 'hcp_key', 'data_use_class': 'IC_ELIGIBLE'}) }}

select
    hcp_key,
    npi,
    first_name,
    last_name,
    specialty_code,
    practice_address1,
    practice_zip5,
    practice_state,
    do_not_contact,
    sample_eligible,
    is_active
from {{ ref('mdm_hcp_golden') }}
