# Stewardship runbook

1. Review `mdm.candidates` where decision=REVIEW
2. Insert override into `mdm_steward_override` (seed/table)
3. Rebuild MDM — overrides win
4. Confirm `mdm_match_evaluation` still passes CI gates
