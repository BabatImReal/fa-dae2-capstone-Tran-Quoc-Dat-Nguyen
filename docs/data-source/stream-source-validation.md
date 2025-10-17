## Streaming Data Source

### Faker-generated User Event Data
- **Type**: Real-time/Streaming
- **Format**: JSON
- **Generation Method**: Python scripts using the Faker library
- **Event Types**: 
  - `page_view` - User visits a page
  - `product_view` - User views a product
  - `search` - User performs a search
  - `add_to_cart` - User adds item to cart
  - `remove_from_cart` - User removes item from cart
  - `checkout_click` - User proceeds to checkout

#### Data Schema:
- `event_id` (UUID) - Unique identifier for the event
- `user_id` (UUID) - Identifier for the user
- `session_id` (UUID) - Identifier for the user session
- `event_type` (string) - Type of user event
- `event_timestamp` (ISO timestamp string) - When the event occurred
- `user_agent` (string) - Browser information
- `ip_address` (string) - User's IP address
- `page_url` (string) - URL of the page
- `page_title` (string) - Title of the page
- `referrer` (string) - Referring page
- `product_id` (UUID) - Identifier for the product (if applicable)
- `product_name` (string) - Name of the product (if applicable)
- `category` (string) - Product category (if applicable)
- `price` (float) - Product price (if applicable)
- `quantity` (integer) - Quantity of products (if applicable)
- `search_query` (string) - Search terms (if applicable)
- `results_count` (integer) - Number of search results (if applicable)
- `filters_applied` (boolean) - Whether filters were applied (if applicable)
- `checkout_step` (string) - Current checkout step (if applicable)
- `cart_value` (float) - Total value of cart (if applicable)
- `item_count` (integer) - Number of items in cart (if applicable)
- `ingested_at` (ISO timestamp string) - When the event was ingested

#### Data Pipeline Integration:
- **Generation Script**: `scripts/ingestion/collect_fake_data.py`
- **Storage Location**: `data/external/` directory
- **File Naming**: `user_event_DD_MM_YYYY_HH_MM.json`
- **Processing**: Real-time generation with configurable event count
---


## Backup Options
*None required. The music transaction schema is stable and fully synthetic.*


## Testing Results
- [x] Faker data generation accessible
- [x] Data quality configurable
- [x] No rate limits
- [x] Documentation: [Faker library](https://faker.readthedocs.io/)


---


**Sample Output (Faker-generated music transaction):**
```json
{
  "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "b2c3d4e5-f678-90ab-cdef-1234567890ab",
  "session_id": "c3d4e5f6-7890-abcd-ef12-34567890abcd",
  "song_id": "d4e5f678-90ab-cdef-1234-567890abcdef",
  "song_title": "Bohemian Rhapsody",
  "artist": "Queen",
  "album": "A Night at the Opera",
  "genre": "Rock",
  "duration_seconds": 355,
  "position_seconds": 120,
  "event_action": "play",
  "device_type": "smartphone",
  "platform": "mobile_app",
  "timestamp": "2025-10-17 10:30:00",
  "user_premium": true,
  "ingested_at": "2025-10-17 10:30:05"
}
```


**Data Schema:**
- event_id (UUID)
- user_id (UUID)
- session_id (UUID)
- song_id (UUID)
- song_title (string)
- artist (string)
- album (string)
- genre (string)
- duration_seconds (integer)
- position_seconds (integer)
- event_action (string) - play, pause, next, previous, skip, like, stop
- device_type (string) - smartphone, tablet, desktop, smart_speaker
- platform (string) - mobile_app, web_player, desktop_app
- timestamp (ISO timestamp string)
- user_premium (boolean)
- ingested_at (ISO timestamp string)


---


**Summary:**
Faker-generated synthetic music transaction data is now used as the main streaming source for development and testing. It provides flexible, on-demand data generation for real-time pipeline validation in music analytics. The schema is stable and tailored for music streaming platforms, with no external dependencies required. The data includes realistic music listening events such as play, pause, next, and skip actions to simulate user behavior.