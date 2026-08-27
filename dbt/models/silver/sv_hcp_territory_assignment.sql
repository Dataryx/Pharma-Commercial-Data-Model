{{
  config(
    materialized='table',
    schema='silver',
    meta={'grain': 'hcp_key, overlay_id, as_of_date, territory_id', 'data_use_class': 'IC_ELIGIBLE'}
  )
}}

/*
  Alignment precedence (declarative):
  1 PRESCRIBER, 2 ACCOUNT, 3 GEOGRAPHY, else UNALIGNED
*/
with hcp as (
    select
        hcp_key,
        practice_zip5,
        hcp_key as entity_proxy
    from {{ ref('mdm_hcp_golden') }}
),
-- map truth entity to hcp_key via xref for prescriber basis keys (entity_id)
xref_entity as (
    select distinct
        entity_id_truth as entity_id,
        hcp_key
    from {{ ref('mdm_hcp_xref') }}
    where entity_id_truth is not null
),
prescriber_align as (
    select
        x.hcp_key,
        a.overlay_id,
        a.territory_id,
        cast(a.weight as double) as weight,
        cast(a.valid_from as date) as valid_from,
        cast(a.valid_to as date) as valid_to,
        a.alignment_version_id,
        1 as precedence
    from {{ ref('sv_alignment') }} a
    join xref_entity x on x.entity_id = a.basis_key
    where a.alignment_basis = 'PRESCRIBER'
),
aff as (
    select
        x.hcp_key,
        a.hco_id,
        a.is_primary
    from {{ ref('br_hcp_hco_affiliation') }} a
    join xref_entity x on x.entity_id = a.entity_id
    where coalesce(a.is_primary, true)
),
account_align as (
    select
        aff.hcp_key,
        al.overlay_id,
        al.territory_id,
        cast(al.weight as double) as weight,
        cast(al.valid_from as date) as valid_from,
        cast(al.valid_to as date) as valid_to,
        al.alignment_version_id,
        2 as precedence
    from aff
    join {{ ref('sv_alignment') }} al
      on al.basis_key = aff.hco_id
     and al.alignment_basis = 'ACCOUNT'
),
geo_align as (
    select
        h.hcp_key,
        al.overlay_id,
        al.territory_id,
        cast(al.weight as double) as weight,
        cast(al.valid_from as date) as valid_from,
        cast(al.valid_to as date) as valid_to,
        al.alignment_version_id,
        3 as precedence
    from hcp h
    join {{ ref('sv_alignment') }} al
      on al.basis_key = h.practice_zip5
     and al.alignment_basis = 'GEOGRAPHY'
),
stacked as (
    select * from prescriber_align
    union all select * from account_align
    union all select * from geo_align
),
ranked as (
    select
        *,
        min(precedence) over (partition by hcp_key, overlay_id, valid_from) as best_precedence
    from stacked
),
chosen as (
    select * exclude (best_precedence)
    from ranked
    where precedence = best_precedence
),
-- ensure every hcp has at least UNALIGNED for PRIMARY overlay on V2 window
all_hcp as (
    select distinct hcp_key from hcp
),
with_unaligned as (
    select * from chosen
    union all
    select
        a.hcp_key,
        'PRIMARY' as overlay_id,
        'UNALIGNED' as territory_id,
        1.0 as weight,
        date '2024-01-01' as valid_from,
        date '9999-12-31' as valid_to,
        'ALN_V1' as alignment_version_id,
        99 as precedence
    from all_hcp a
    where not exists (
        select 1 from chosen c where c.hcp_key = a.hcp_key and c.overlay_id = 'PRIMARY'
    )
)

select
    hcp_key,
    overlay_id,
    territory_id,
    weight,
    valid_from,
    valid_to,
    alignment_version_id,
    precedence
from with_unaligned
