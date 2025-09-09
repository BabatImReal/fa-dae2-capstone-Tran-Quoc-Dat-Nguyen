## Data Schema Overview

This project uses two main data sources for financial analytics:

### 1. Batch/Static Source: Financial Transactions Dataset (Kaggle)
- **cards_data**:  
  - `id`, `client_id`, `card_brand`, `card_type`, `card_number`, `expires`, `cvv`, `has_chip`, `num_cards_issued`, `credit_limit`, `acct_open_date`, `year_pin_last_changed`, `card_on_dark_web`
- **transaction_data**:  
  - `id`, `date`, `client_id`, `card_id`, `amount`, `use_chip`, `merchant_id`, `merchant_city`, `merchant_state`, `zip`, `mcc`, `errors`
- **user data**:  
  - `id`, `current_age`, `retirement_age`, `birth_year`, `birth_month`, `gender`, `address`, `latitude`, `longitude`, `per_capita_income`, `yearly_income`, `total_debt`, `credit_score`, `num_credit_cards`
- **mcc_codes.json**:  
  - Standard classification codes for business types
  - Enables transaction categorization and spending analysis
  - Industry-standard MCC codes with descriptions (4-digit codes)
- **train_fraud_labels.json**:  
  - Binary classification labels for transactions
  - Indicates fraudulent vs. legitimate transactions
  - Ideal for training supervised fraud detection models

### 2. Real-Time Source: Stripe API
- Used for collecting up-to-date transaction and customer data for real-time analytics and integration.

This schema supports a wide range of financial analytics, including fraud detection, customer profiling, and transaction pattern analysis.

### Attribute/Column Explanations

#### cards_data
- `id`: Unique identifier for the card record
- `client_id`: Identifier linking the card to a specific user/client
- `card_brand`: Brand of the card (e.g., Visa, MasterCard)
- `card_type`: Type of card (e.g., credit, debit, prepaid)
- `card_number`: Masked or synthetic card number
- `expires`: Card expiration date (MM/YY)
- `cvv`: Card Verification Value (masked or synthetic)
- `has_chip`: Whether the card has a chip (boolean)
- `num_cards_issued`: Number of cards issued to the client
- `credit_limit`: Credit limit assigned to the card
- `acct_open_date`: Date the card account was opened
- `year_pin_last_changed`: Year when the card PIN was last changed
- `card_on_dark_web`: Indicator if the card is found on the dark web (boolean)

#### transaction_data
- `id`: Unique identifier for the transaction
- `date`: Date and time of the transaction
- `client_id`: Identifier for the user/client making the transaction
- `card_id`: Identifier for the card used in the transaction
- `amount`: Transaction amount
- `use_chip`: Whether the card chip was used (boolean)
- `merchant_id`: Identifier for the merchant
- `merchant_city`: City where the merchant is located
- `merchant_state`: State where the merchant is located
- `zip`: ZIP/postal code of the merchant
- `mcc`: Merchant Category Code (industry classification)
- `errors`: Any errors or issues during the transaction

#### user data
- `id`: Unique identifier for the user/client
- `current_age`: Current age of the user
- `retirement_age`: Expected or planned retirement age
- `birth_year`: Year of birth
- `birth_month`: Month of birth
- `gender`: Gender of the user
- `address`: User's address
- `latitude`: Latitude coordinate of the address
- `longitude`: Longitude coordinate of the address
- `per_capita_income`: Per capita income in the user's area
- `yearly_income`: User's annual income
- `total_debt`: Total outstanding debt
- `credit_score`: User's credit score
- `num_credit_cards`: Number of credit cards owned by the user
