-- macros/generate_date_spine.sql
-- Generates a continuous sequence of dates between two bounds.
-- Usage: {{ generate_date_spine('2022-01-01', '2024-12-31') }}

{% macro generate_date_spine(start_date, end_date) %}

with date_spine as (
    select
        date_add(date('{{ start_date }}'), interval n day) as calendar_date
    from
        unnest(
            generate_array(
                0,
                date_diff(date('{{ end_date }}'), date('{{ start_date }}'), day)
            )
        ) as n
)

select * from date_spine

{% endmacro %}
