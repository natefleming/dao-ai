# Brand Rep Product Education Demo Data

This directory contains the minimal set of tables and data needed to support the **Nike Air Max Brand Representative Product Education Demo**. The data is designed to answer specific questions that arise during brand training sessions and demonstrate how Databricks Genie can provide real-time customer intelligence to store associates.

## Demo Overview

The demo shows store associate Marcus preparing for and participating in a Nike brand representative training session on Air Max SC products. Marcus uses the BrickMart AI Assistant powered by Databricks Genie to transform generic product training into personalized, data-driven sales intelligence.

## Tables Created

### 1. `customer_brand_profiles`
**Purpose**: Customer demographics and brand preferences for Nike buyers
- **Key Fields**: age_group, lifestyle_category, brand_preference, price_sensitivity, shopping_pattern
- **Demo Support**: Answers "What should I know about our customers who buy Nike?"

### 2. `product_performance` 
**Purpose**: Product sales analytics and performance metrics
- **Key Fields**: units_sold_6m, return_rate, avg_rating, seasonal_trend, profit_margin
- **Demo Support**: Answers "Show me how Nike Air Max products perform at our store"

### 3. `customer_feedback`
**Purpose**: Customer reviews and feedback on products
- **Key Fields**: rating, review_text, feedback_category, sentiment
- **Demo Support**: Provides insights into customer satisfaction and common issues

### 4. `competitive_insights`
**Purpose**: Nike vs Adidas competitive analysis
- **Key Fields**: decision_factor, price_comparison, customer_comment, purchase_decision
- **Demo Support**: Answers "What do customers say when they choose Adidas over Nike?"

### 5. `sales_interactions`
**Purpose**: Sales conversations and customer objections
- **Key Fields**: customer_objection, objection_category, resolution_strategy, outcome
- **Demo Support**: Provides real sales conversation data and objection handling

## Demo Questions Supported

### Question 1: "Nike brand representative is coming to train us on Air Max SC. What should I know about our customers who buy Nike?"

**Expected Response Data**:
- **Top Buyers**: Ages 18-35 (68%), fitness enthusiasts and students
- **Peak Sales**: Weekends and after 5 PM on weekdays  
- **Price Sensitivity**: 45% wait for sales, average purchase $89
- **Common Questions**: Durability for running, sizing vs. other brands
- **Cross-sell Opportunities**: Athletic socks (78% attach rate), Nike apparel

### Question 2: "Show me how Nike Air Max products perform at our store."

**Expected Response Data**:
- **Best Sellers**: Air Max 90 (127 units), Air Max 270 (89 units)
- **Slow Movers**: Air Max Plus (12 units) - price point issue
- **Return Rate**: 8% (mainly sizing issues)
- **Customer Feedback**: 'Comfortable but runs small' (recurring theme)
- **Seasonal Trends**: 40% sales increase March-May

### Question 3: "What do customers say when they choose Adidas over Nike?"

**Expected Response Data**:
- **Adidas Wins**: Price promotions (35% of switches), wider width options
- **Nike Wins**: Brand loyalty (52% repeat rate), performance features
- **Common Objections**: 'Nike is overpriced' (counter: highlight durability)
- **Opportunity**: Customers buying Adidas often ask about Nike comfort
- **Timing**: Nike loses sales during Adidas promotion periods

### Question 4: "How does Air Max SC cushioning compare to our top-selling Air Max 90?"

**Expected Response Data**:
- **Air Max 90**: Full-length Air unit, premium materials, $120 price point
- **Air Max SC**: Heel Air unit, synthetic materials, $70 price point
- **Positioning**: SC targets budget-conscious customers wanting Air Max style
- **Sales Angle**: 'Air Max look and comfort at an accessible price'

## Sample Data Highlights

### Customer Demographics (Nike Buyers at Downtown Market)
- 8 Nike customers with varied profiles
- Age groups: 18-25 (50%), 26-35 (37.5%), 36-45 (12.5%)
- Price sensitivity: High (50%), Medium (37.5%), Low (12.5%)
- Shopping patterns: Weekend shoppers, after 5PM, sale hunters

### Product Performance (Air Max Products)
- **Nike Air Max 90**: 127 units sold (6m), 8.2% return rate, 4.3 rating
- **Nike Air Max 270**: 89 units sold (6m), 6.8% return rate, 4.5 rating  
- **Nike Air Max SC**: 45 units sold (6m), 5.2% return rate, 4.1 rating
- **Nike Air Max Plus**: 12 units sold (6m), 12.5% return rate, 3.8 rating

### Competitive Insights
- 7 competitive decision scenarios between Nike and Adidas
- Key factors: Price (3 cases), Fit Options (1), Brand Loyalty (1), Performance (1), Promotion Timing (1)
- Price objections: "Nike is overpriced compared to Adidas"
- Fit issues: "Need wide width shoes, Nike does not have them"

### Sales Interactions
- 8 documented sales conversations with Nike products
- Common objections: Price (3), Sizing (2), Technology (1), Product Knowledge (1), Fit (1)
- Success rate: 50% (4 sales completed, 4 no sales)
- Average interaction time: 15.6 minutes

## Genie Query Examples

The `brand_rep_demo_queries.sql` file contains sample SQL queries that demonstrate how Genie would analyze this data to answer the demo questions. Key query types include:

1. **Customer Demographics Analysis**: Age groups, shopping patterns, price sensitivity
2. **Product Performance Metrics**: Sales volumes, return rates, seasonal trends
3. **Competitive Analysis**: Decision factors, price comparisons, customer comments
4. **Product Comparisons**: Air Max SC vs Air Max 90 positioning
5. **Sales Intelligence**: Objection patterns, successful strategies, timing insights

## Usage in Genie Room

These tables should be loaded into the Genie space `01f03432c01a1b18b710fe597c2d68ee` to enable natural language querying during the demo. The Genie tool can then answer questions like:

- "What are the demographics of our Nike customers?"
- "Which Air Max products sell best and why?"
- "How do we compete against Adidas on price?"
- "What are common customer objections to Nike products?"
- "How should we position Air Max SC vs Air Max 90?"

## Data Volume

- **customer_brand_profiles**: 12 records (8 Nike, 4 Adidas customers)
- **product_performance**: 9 records (5 Nike Air Max, 4 Adidas products)
- **customer_feedback**: 12 records (9 Nike, 3 Adidas reviews)
- **competitive_insights**: 7 records (Nike vs Adidas decisions)
- **sales_interactions**: 8 records (Nike sales conversations)

**Total**: 48 records across 5 tables - minimal but comprehensive data to support all demo scenarios.

## Integration Notes

- All data is focused on **Downtown Market (Store 101)** for consistency
- Customer IDs link across tables for comprehensive customer journey analysis
- Product IDs connect performance data with customer feedback
- Date ranges span recent months (Jan-Mar 2024) for realistic recency
- SKU codes follow existing pattern (NIKE-AMXX-001, ADI-XXX-001)

This streamlined dataset provides rich insights while maintaining simplicity for demo purposes and Genie room integration. 