## Selected Batch Source: Brazilian E-commerce Public Dataset (Kaggle)
- **Primary Dataset**: `olistbr/brazilian-ecommerce`
- **URL**: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
- **Authentication**: Kaggle account required for download
- **Data Format**: Multiple CSV files
- **Dataset Details**: Comprehensive dataset of Brazilian e-commerce transactions from 2016 to 2018, including customer, order, product, and review information.
- **Volume**: ~100,000 orders across multiple tables
- **Update Frequency**: Static snapshot
- **Download Location**: `data/external/` directory
- **Why Selected**: Public, well-documented, and suitable for e-commerce analytics. Easily accessible via kaggle API and integrates with the pipeline. Contains rich data for analysis including customer behavior, product information, and order details.


## Fallback Datasets (Tested)
*None required. The Brazilian e-commerce dataset is stable and public.*


## Data Pipeline Integration
- **Collection Script**: `scripts/ingestion/collect_batch_data.py`
- **Target Directory**: `data/external/`
- **Processing**: Automated download and extraction via kaggle API


## Testing Results
- [x] Primary dataset (`olistbr/brazilian-ecommerce`) accessible
- [x] Dataset files successfully downloaded and extracted
- [x] Data copied to project directory
- [x] File structure validated
- [x] Kaggle API integration working
- [x] Automated download pipeline functional

---


**Sample Output (olist_orders_dataset.csv):**
```csv
order_id,customer_id,order_status,order_purchase_timestamp,order_approved_at,order_delivered_carrier_date,order_delivered_customer_date,order_estimated_delivery_date
e481f51cbdc54678b7cc49136f2d6af7,9ef432eb6251297304e76186210cde1e,delivered,2017-10-02 10:56:33,2017-10-02 11:07:15,2017-10-04 19:55:00,2017-10-10 21:25:13,2017-10-18 00:00:00
53cdb2fc8bc7dce0b6741e2150273451,b0830fb4747a6c6d20dea0b8c9f4f022,delivered,2018-07-24 20:41:37,2018-07-26 03:24:27,2018-07-26 14:31:00,2018-08-07 15:34:57,2018-08-13 00:00:00
```

**Key Data Files:**
- `olist_orders_dataset.csv` - Order information
- `olist_order_items_dataset.csv` - Items in each order
- `olist_products_dataset.csv` - Product information
- `olist_customers_dataset.csv` - Customer information
- `olist_sellers_dataset.csv` - Seller information
- `olist_order_payments_dataset.csv` - Payment information
- `olist_order_reviews_dataset.csv` - Customer reviews
- `product_category_name_translation.csv` - Product category translations

**Download Process:**
```bash
# Automated via collect_batch_data.py
📥 Trying dataset: olistbr/brazilian-ecommerce
Files in download path:
  - olist_orders_dataset.csv
  - olist_order_items_dataset.csv
  - olist_products_dataset.csv
  - olist_customers_dataset.csv
  - olist_sellers_dataset.csv
  - olist_order_payments_dataset.csv
  - olist_order_reviews_dataset.csv
  - product_category_name_translation.csv
✅ Successfully downloaded olistbr/brazilian-ecommerce
```


**Summary:**
The Brazilian E-commerce Public Dataset (`olistbr/brazilian-ecommerce`) is successfully integrated as the primary batch data source. The dataset provides comprehensive transactional data for e-commerce analysis, automatically downloaded via the Kaggle API and processed by the data pipeline. The pipeline is robust, with automated validation and integration steps.