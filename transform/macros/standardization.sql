{% macro validate_npi(npi_expr) %}
(
  {{ npi_expr }} is not null
  and length(cast({{ npi_expr }} as varchar)) = 10
  and try_cast({{ npi_expr }} as bigint) is not null
)
{% endmacro %}

{% macro normalize_ndc(ndc_expr) %}
(
  lpad(replace(cast({{ ndc_expr }} as varchar), '-', ''), 11, '0')
)
{% endmacro %}

{% macro suppress_small_cells(patient_count_col, min_size=None) %}
{% set thresh = min_size if min_size is not none else var('min_cell_size', 5) %}
case when {{ patient_count_col }} < {{ thresh }} then null else {{ patient_count_col }} end
{% endmacro %}

{% macro standardize_name(first, last) %}
upper(regexp_replace(coalesce({{ first }}, ''), '[^A-Z ]', '', 'g'))
{% endmacro %}
