# Data Analytics & Brief Analysis

This document provides a brief analysis of the key metrics and trends observed in the **Fact Dashboard**.

---

## Executive Summary

The e-commerce platform has shown consistent growth in order volume from 2016 to 2018. Customer satisfaction is high, with an average review score of **4.1/5** and the majority of reviews rated as "Excellent." Shipping performance averages **12.5 days**, which may present an opportunity for improvement. Credit cards dominate payment methods, while alternative payment options (Boleto, Voucher, Debit) remain secondary.

---

## Key Findings

### 1. Order Growth Trend

| Year | Total Orders | YoY Growth |
|------|--------------|------------|
| 2016 | ~300         | —          |
| 2017 | ~45,000      | +14,900%   |
| 2018 | ~54,000      | +20%       |

- **Observation:** The platform experienced explosive growth from 2016 to 2017, likely due to market expansion or marketing efforts. Growth stabilized in 2018 at ~20%.
- **Recommendation:** Investigate what drove the 2017 surge and replicate successful strategies.

---

### 2. Product Category Distribution

| Rank | Category               | Share   |
|------|------------------------|---------|
| 1    | bed_bath_table         | 9.42%   |
| 2    | health_beauty          | 8.92%   |
| 3    | sports_leisure         | 7.78%   |
| 4    | computers_accessories  | 6.75%   |
| 5    | furniture_decor        | 6.44%   |

- **Observation:** The top 5 categories account for ~39% of all orders. The distribution is relatively balanced, with no single category dominating.
- **Recommendation:** Focus inventory and marketing efforts on top categories while exploring growth opportunities in underperforming categories.

---

### 3. Customer Satisfaction (Reviews)

| Review Tier | Count   | Percentage |
|-------------|---------|------------|
| Excellent   | ~57,000 | ~58%       |
| Good        | ~19,000 | ~19%       |
| Very Poor   | ~10,000 | ~10%       |
| Average     | ~7,000  | ~7%        |
| Poor        | ~4,000  | ~4%        |
| No Review   | ~2,000  | ~2%        |

- **Observation:** ~77% of reviews are positive (Excellent + Good). However, ~14% are negative (Very Poor + Poor), which is notable.
- **Recommendation:** Analyze negative reviews to identify common complaints (e.g., shipping delays, product quality) and address root causes.

---

### 4. Shipping Performance

| Metric                    | Value      |
|---------------------------|------------|
| Average Shipping Time     | 12.5 days  |

- **Observation:** A 12.5-day average shipping time may be acceptable for certain regions but could be a pain point for customers expecting faster delivery.
- **Recommendation:** Segment shipping times by region/seller and identify bottlenecks. Consider partnerships with faster logistics providers.

---

### 5. Payment Method Trends

| Payment Type | Trend Description                                      |
|--------------|--------------------------------------------------------|
| CREDIT_CARD  | Dominant method; peaks around month 8 (~10,000 txns)   |
| BOLETO       | Steady usage (~2,000–4,000 txns/month)                 |
| VOUCHER      | Low but stable (~50–100 txns/month)                    |
| DEBIT_CARD   | Minimal usage (~50–100 txns/month)                     |

- **Observation:** Credit card is the preferred payment method, accounting for the majority of transactions. Boleto (a Brazilian bank slip) is a secondary option, likely used by customers without credit cards.
- **Recommendation:** Ensure credit card processing is optimized. Consider promotions for underutilized payment methods if margin-friendly.

---

## Actionable Insights

| Area               | Insight                                                                 | Action                                                    |
|--------------------|-------------------------------------------------------------------------|-----------------------------------------------------------|
| Growth             | 2017 had explosive growth; 2018 stabilized.                             | Analyze 2017 drivers; replicate successful campaigns.     |
| Categories         | Top 5 categories = ~39% of orders.                                      | Prioritize inventory/marketing for top categories.        |
| Customer Satisfaction | 77% positive reviews; 14% negative.                                  | Deep-dive into negative reviews; fix root causes.         |
| Shipping           | 12.5-day average may be too slow.                                       | Segment by region; optimize logistics.                    |
| Payments           | Credit card dominates; Boleto is secondary.                             | Ensure smooth credit card UX; consider Boleto promotions. |

---

## Next Steps

1. **Deep-Dive Analysis:** Create detailed reports for each category and region.
2. **Customer Feedback:** Analyze text of negative reviews for common themes.
3. **A/B Testing:** Test promotions for alternative payment methods.
4. **Logistics Optimization:** Partner with faster couriers or optimize seller fulfillment.

---

## Data Sources

- `fact_orders` — order-level metrics
- `fact_payments` — payment type and timing
- `fact_reviews` — customer review scores and text
- `dim_product` — product category information
- `dim_date` — date dimensions for time-series analysis

---

*Last updated: December 2025*
