{% macro generate_date_spine(start_date=var('date_spine_start', '2023-01-01'), end_date='current_date()') %}

    select date
    from unnest(
        generate_date_array(date '{{ start_date }}', {{ end_date }})
    ) as date

{% endmacro %}
