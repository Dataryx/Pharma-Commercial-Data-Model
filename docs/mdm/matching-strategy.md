# Matching strategy

1. Standardize names/addresses
2. Deterministic: valid NPI / ME / DEA
3. Block on soundex(last)+first initial+state
4. Score with Jaro–Winkler + zip/specialty weights
5. Auto-merge above upper threshold; review band; reject below
6. Connected components with max cluster size and conflicting-ID guards
