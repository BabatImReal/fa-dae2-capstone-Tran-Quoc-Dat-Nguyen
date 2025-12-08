from typing import Dict, Any, List, Optional
import os
import re
from pathlib import Path
import snowflake.connector 
from langchain.tools import tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def tool_with_docs(func):
    """Decorator that loads tool description from markdown file based on function name.

    Args:
        func: The function to decorate as a LangChain tool.

    Returns:
        A decorated function with tool name and description loaded from markdown.
    """
    tool_docs_dir = Path(__file__).parent / "tool_docs"
    md_path = tool_docs_dir / f"{func.__name__}.md"
    description = md_path.read_text().strip()
    return tool(func.__name__, description=description)(func)

def get_snowflake_connection():
	# Minimal helper: reads credentials from environment and returns connection
	params = {
		"account": os.getenv("SNOWFLAKE_ACCOUNT"),
		"user": os.getenv("SNOWFLAKE_USER"),
		"authenticator": "SNOWFLAKE_JWT",
		"private_key_file": os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PATH"),
		"private_key_file_pwd": os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD"),
		"warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
		"database": os.getenv("SNOWFLAKE_DATABASE"),
		"schema": os.getenv("SNOWFLAKE_SCHEMA"),
		"role": os.getenv("SNOWFLAKE_ROLE"),
	}
	# Debug: print connection params (mask sensitive values)
	print(f"❄️ Snowflake Connection Params:")
	print(f"   Account: {params['account']}")
	print(f"   User: {params['user']}")
	print(f"   Authenticator: {params['authenticator']}")
	print(f"   Private Key File: {params['private_key_file']}")
	print(f"   Private Key Pwd: {'*' * len(params['private_key_file_pwd']) if params['private_key_file_pwd'] else 'None'}")
	print(f"   Warehouse: {params['warehouse']}")
	print(f"   Database: {params['database']}")
	print(f"   Schema: {params['schema']}")
	print(f"   Role: {params['role']}")
	return snowflake.connector.connect(**params)



def validate_identifier(value: str):
    """Very simple whitelist validation to avoid SQL injection."""
    if not re.match(r"^[A-Za-z0-9_ ]+$", value):
        raise ValueError("Invalid category name")
    return value


@tool_with_docs
def get_all_product_categories_from_snowflake() -> Dict[str, Any]:
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


@tool_with_docs
def get_product_by_category_from_snowflake(category: str) -> Dict[str, Any]:
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


@tool_with_docs
def get_order_summary_by_quarter_from_snowflake(year: str, quarter: str) -> Dict[str, Any]:
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


