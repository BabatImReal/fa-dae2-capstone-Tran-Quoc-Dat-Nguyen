Query Snowflake product dimension table and return one example product for a given product category name.

This tool retrieves a sample product from a specific category. It automatically handles spaces vs underscores in category names.
Use this when the user wants to see an example product from a particular category or needs product details.

Parameters:
- category (str): The product category name (e.g., 'health_beauty' or 'health beauty')

Returns:
- product_id: Unique product identifier
- product_category_name_english: Category name in English
- product_weight_g: Product weight in grams
- product_length_cm: Product length in centimeters
- product_height_cm: Product height in centimeters
- product_width_cm: Product width in centimeters