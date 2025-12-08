Return the latest ingested product event from PostgreSQL staging.user_events table.

This tool queries the most recent product event from the real-time streaming data pipeline.
Use this when the user asks about the latest ingested data, most recent product, or wants to check if data is flowing.

No parameters required.

Returns:
- product_name: Name of the product
- category: Product category
- price: Product price
- quantity: Quantity in the event