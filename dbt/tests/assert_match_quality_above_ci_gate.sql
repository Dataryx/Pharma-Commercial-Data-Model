select *
from {{ ref('mdm_match_evaluation') }}
where precision < 0.98 or recall < 0.95 or false_friends_separated = false
