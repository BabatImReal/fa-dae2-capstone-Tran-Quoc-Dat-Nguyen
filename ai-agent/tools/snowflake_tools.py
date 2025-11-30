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
		account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        authenticator="SNOWFLAKE_JWT",
        private_key_file=os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PATH"),
        private_key_file_pwd=os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        role=os.getenv("SNOWFLAKE_ROLE"),
	)



def validate_identifier(value: str):
    """Very simple whitelist validation to avoid SQL injection."""
    if not re.match(r"^[A-Za-z0-9_ ]+$", value):
        raise ValueError("Invalid category name")
    return value


@tool("get_all_product_categories",
      description="Query Snowflake (sc_analytics.dim_products) and return all distinct product categories.")
def get_all_product_categories() -> Dict[str, Any]:
    """
    Return all distinct product categories from sc_analytics.dim_products.
    """

    sql = """
        SELECT DISTINCT product_category_name_english
        FROM sc_analytics.dim_products
        ORDER BY product_category_name_english
    """.strip()

    # Connect to Snowflake
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
        "rows": [dict(zip(columns, row)) for row in rows]
    }


@tool("get_product_by_category",
      description="Query Snowflake product dimension table. Returns one example product for a given product category name. Automatically handles spaces vs underscores in category names.")
def get_product_by_category(category: str) -> Dict[str, Any]:
    """
    Return 1 product from a specific product_category.
    Returns: product_id, product_category_name_english, 
             product_weight_g, product_length_cm,
             product_height_cm, product_width_cm
    """

    # Convert spaces → underscores to match Snowflake naming
    category_normalized = category.replace(" ", "_")

    # Validate after normalization
    category_safe = validate_identifier(category_normalized)

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


@tool("get_all_shipping_tiers",
      description="Query Snowflake (sc_analytics.fact_orders) to return all distinct shipping_tier values.")
def get_all_shipping_tiers() -> Dict[str, Any]:
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

@tool("get_shipping_tier_summary",
      description="Query Snowflake fact_orders for a specific shipping_tier. Returns order count, total quantity, and average shipping_date.")
def get_shipping_tier_summary(tier: str) -> Dict[str, Any]:
    """
    Return count(order_id) and avg(shipping_date) for a specific shipping_tier.
    """

    tier_safe = validate_identifier(tier)

    sql = f"""
        SELECT
            shipping_tier,
            COUNT(order_id) AS total_orders,
            SUM(order_qty) AS total_orders_quantity,
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


@tool(
    "get_order_summary_by_quarter",
    description="Query Snowflake sc_analytics.fact_orders and sc_analytics.dim_date to return order + revenue summary for a given year and quarter.",
    args_schema={
        "type": "object",
        "properties": {
            "year": {
                "type": "string",
                "description": "Year to query, e.g. '2017'"
            },
            "quarter": {
                "type": "string",
                "description": "Quarter number: '1', '2', '3', or '4'"
            }
        },
        "required": ["year", "quarter"]
    }
)


def get_order_summary_by_quarter(year: str, quarter: str) -> Dict[str, Any]:
    year_safe = validate_identifier(year)
    quarter_safe = validate_identifier(quarter)

    sql = f"""
        SELECT 
            d.year,
            d.quarter,
            COUNT(fo.order_id) AS total_orders,
            SUM(fo.total_order_value) AS total_revenue,
            SUM(fo.order_qty) AS total_orders_quantity,
            AVG(fo.shipping_date) AS avg_shipping_date,
            AVG(fo.review_score) AS avg_review_score,
            COUNT(DISTINCT fo.customer_id) AS unique_customers
        FROM sc_analytics.fact_orders fo
        JOIN sc_analytics.dim_date d 
            ON d.date_key = fo.order_date_key
        WHERE d.year = '{year_safe}'
          AND d.quarter = '{quarter_safe}'
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
