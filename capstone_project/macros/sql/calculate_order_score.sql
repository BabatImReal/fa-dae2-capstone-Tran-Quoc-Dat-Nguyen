{% macro calculate_review_score_tier(review_score) %}
    CASE
        WHEN {{ review_score }} IS NULL THEN 'No Review'
        WHEN {{ review_score }} = 5 THEN 'Excellent'
        WHEN {{ review_score }} = 4 THEN 'Good'
        WHEN {{ review_score }} = 3 THEN 'Average'
        WHEN {{ review_score }} = 2 THEN 'Poor'
        WHEN {{ review_score }} = 1 THEN 'Very Poor'
        ELSE 'Invalid'
    END
{% endmacro %}