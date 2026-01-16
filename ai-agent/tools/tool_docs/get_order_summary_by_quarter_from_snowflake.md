Query Snowflake sc_analytics.fact_orders and sc_analytics.dim_date to return order and revenue summary for a given year and quarter.

This tool aggregates order statistics for a specific quarter. Use this when the user asks about quarterly performance, sales trends, or order metrics.

Parameters:
- year (str): Year to query (e.g., '2017', '2018')
- quarter (str): Quarter number ('1', '2', '3', or '4')

Returns:
- year: The queried year
- quarter: The queried quarter
- total_orders: Total number of orders in that quarter
- total_revenue: Sum of all order values
- total_orders_quantity: Total quantity of items ordered
- avg_shipping_date: Average shipping time in days
- avg_review_score: Average customer review score
- unique_customers: Number of unique customers who placed orders