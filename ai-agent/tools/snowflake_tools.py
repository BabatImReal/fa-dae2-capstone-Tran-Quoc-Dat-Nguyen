from typing import Dict, Any, List, Optional
import os
import re
import snowflake.connector 
from langchain.tools import tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_snowflake_connection():
	# Minimal helper: reads credentials from environment and returns connection
	return snowflake.connector.connect(
		user=os.getenv("SNOWFLAKE_USER"),
		password=os.getenv("SNOWFLAKE_PASSWORD"),
		account=os.getenv("SNOWFLAKE_ACCOUNT"),
		warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
		database=os.getenv("SNOWFLAKE_DATABASE"),
		schema=os.getenv("SNOWFLAKE_SCHEMA"),
	)



def validate_identifier(value: str):
    """Very simple whitelist validation to avoid SQL injection."""
    if not re.match(r"^[A-Za-z0-9_ ]+$", value):
        raise ValueError("Invalid category name")
    return value


@tool("get_product_by_category")
def get_product_by_category(category: str) -> Dict[str, Any]:
    """
    Return 1 product from a specific product_category.
    Returns: product_id, product_category_name_english, 
             product_weight_g, product_length_cm, 
             product_height_cm, product_width_cm
    """

    category_safe = validate_identifier(category)

    sql = f"""
        SELECT 
            product_id,
            product_category_name_english,
            product_weight_g,
            product_length_cm,
            product_height_cm,
            product_width_cm
        FROM sc_analytics.dim_products
        WHERE LOWER(product_category_name_english) = LOWER('{category_safe}')
        LIMIT 1
    """.strip()

    # Connect to Snowflake
    conn = get_snowflake_connection()

    cur = conn.cursor()
    cur.execute(sql)

    row = cur.fetchone()
    columns = [col[0] for col in cur.description]

    cur.close()
    conn.close()

    return {
        "sql_used": sql,
        "row_count": 1 if row else 0,
        "row": dict(zip(columns, row)) if row else None
    }

@tool("get_all_shipping_tiers")
def get_all_shipping_tiers(_: str) -> Dict[str, Any]:
    """
    Return all distinct shipping_tier values from sc_analytics.fact_orders.
    """

    sql = """
        SELECT DISTINCT shipping_tier
        FROM sc_analytics.fact_orders
        ORDER BY shipping_tier
    """.strip()

    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(sql)

    rows = cur.fetchall()
    columns = [col[0] for col in cur.description]

    cur.close()
    conn.close()

    return {
        "sql_used": sql,
        "row_count": len(rows),
        "rows": [dict(zip(columns, r)) for r in rows]
    }

@tool("get_shipping_tier_summary")
def get_shipping_tier_summary(tier: str) -> Dict[str, Any]:
    """
    Return count(order_id) and avg(shipping_date) for a specific shipping_tier.
    """

    tier_safe = validate_identifier(tier)

    sql = f"""
        SELECT
            shipping_tier,
            COUNT(order_id) AS total_orders,
            AVG(shipping_date) AS avg_shipping_date
        FROM sc_analytics.fact_orders
        WHERE shipping_tier = '{tier_safe}'
        GROUP BY shipping_tier
    """.strip()

    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(sql)

    rows = cur.fetchall()
    columns = [col[0] for col in cur.description]

    cur.close()
    conn.close()

    return {
        "sql_used": sql,
        "row_count": len(rows),
        "rows": [dict(zip(columns, r)) for r in rows]
    }

@tool("get_order_summary_by_quarter")
def get_order_summary_by_quarter(params: Dict[str, str]) -> Dict[str, Any]:
    """
    Return order summary for a specific year + quarter.
    Required params:
        - year (e.g., '2017')
        - quarter (e.g., '4')
    """

    # Extract safely
    year = validate_identifier(params.get("year", ""))
    quarter = validate_identifier(params.get("quarter", ""))

    if not year or not quarter:
        return {"error": "Both 'year' and 'quarter' must be provided."}

    sql = f"""
        SELECT 
            d.year,
            d.quarter,
            COUNT(fo.order_id) AS total_orders,
            SUM(fo.total_order_value) AS total_revenue,
            AVG(fo.shipping_date) AS avg_shipping_date,
            AVG(fo.review_score) AS avg_review_score,
            COUNT(DISTINCT fo.customer_id) AS unique_customers
        FROM sc_analytics.fact_orders fo
        JOIN sc_analytics.dim_date d 
            ON d.date_key = fo.order_date_key
        WHERE d.year = '{year}'
          AND d.quarter = '{quarter}'
        GROUP BY d.year, d.quarter
        ORDER BY d.year, d.quarter
    """.strip()

    conn = get_snowflake_connection()
    cur = conn.cursor()
    cur.execute(sql)

    rows = cur.fetchall()
    columns = [col[0] for col in cur.description]

    cur.close()
    conn.close()

    return {
        "sql_used": sql,
        "row_count": len(rows),
        "rows": [dict(zip(columns, r)) for r in rows]
    }