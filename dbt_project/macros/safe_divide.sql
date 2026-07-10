-- macros/safe_divide.sql
-- Usage: {{ safe_divide('numerator_col', 'denominator_col') }}
-- Returns null instead of error when denominator is zero.

{% macro safe_divide(numerator, denominator) %}
    case
        when {{ denominator }} = 0 or {{ denominator }} is null
        then null
        else {{ numerator }} / {{ denominator }}
    end
{% endmacro %}
