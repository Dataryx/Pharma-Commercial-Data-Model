{{
  config(
    materialized='table',
    schema='gold',
    meta={'grain': 'layer', 'data_use_class': 'COMMERCIAL_UNRESTRICTED'}
  )
}}

select
    'mdm' as layer,
    precision,
    recall,
    f1,
    false_friends_separated,
    current_timestamp as as_of
from {{ ref('mdm_match_evaluation') }}
