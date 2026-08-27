# Privacy and suppression

- No PHI in bronze or above for specialty patients (tokens only).
- Macro `suppress_small_cells` nulls counts below `var('min_cell_size')`.
- Suppressed demand cells: `suppression_flag='Y'` with null metrics (unknown ≠ zero).
