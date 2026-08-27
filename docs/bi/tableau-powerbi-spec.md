# Power BI / Tableau import spec

- Import `gold` star schema: dimensions + facts + aggregate marts
- Relationship direction: dimensions → facts (single direction)
- Use `mart_brand_performance_weekly` and `mart_territory_scorecard` for rep dashboards
- RLS: map user email → `sec_user_territory_access` → filter `territory_id`
- Do not import patient-restricted facts into IC datasets
