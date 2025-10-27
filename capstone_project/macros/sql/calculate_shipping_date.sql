{% macro calculate_shipping_performance_tier(shipping_date) %}
    CASE
        WHEN {{ shipping_date }} IS NULL THEN 'Unknown'
        WHEN {{ shipping_date }} <= 7 THEN 'Excellent'
        WHEN {{ shipping_date }} <= 14 THEN 'Good'
        WHEN {{ shipping_date }} <= 30 THEN 'Average'
        WHEN {{ shipping_date }} <= 60 THEN 'Below Average'
        ELSE 'Poor'
    END
{% endmacro %}