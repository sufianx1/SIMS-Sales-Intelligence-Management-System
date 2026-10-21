# Analytics & Financial Metric Definitions: SIMS

## 1. Executive Summary & Philosophy

Financial metrics in SIMS are computed deterministically to eliminate rounding discrepancies, double-counting, and division-by-zero exceptions. All metrics are strictly scoped to the active tenant (`company_id`), with optional store-level filtering (`store_id`).

---

## 2. Core KPI Formulas

### 2.1 Total Sales (Revenue)
- **Definition**: The gross recognized sales across all finalized orders for the active tenant.
- **Formula**:
  $$\text{Total Sales} = \sum_{i=1}^{N} \text{orders}[i].\text{total\_sales}$$
- **Order-Line Consistency**: Each order's `total_sales` equals the sum of its itemized line net sales:
  $$\text{total\_sales} = \sum \text{lines}[j].\text{sales}$$

### 2.2 Total Cost
- **Definition**: The total cost basis of products sold across all finalized orders.
- **Formula**:
  $$\text{Total Cost} = \sum_{i=1}^{N} \text{orders}[i].\text{total\_cost}$$
  where $\text{total\_cost} = \sum (\text{lines}[j].\text{quantity} \times \text{lines}[j].\text{unit\_cost})$.

### 2.3 Total Profit & Profit Margin
- **Definition**: Net financial return generated from sales after deducting product cost basis and discounts.
- **Formulas**:
  $$\text{Total Profit} = \sum_{i=1}^{N} \text{orders}[i].\text{total\_profit} = \text{Total Sales} - \text{Total Cost}$$
  $$\text{Profit Margin (\%)} = \begin{cases} \left(\frac{\text{Total Profit}}{\text{Total Sales}}\right) \times 100 & \text{if Total Sales} > 0 \\ 0.0 & \text{if Total Sales} = 0 \end{cases}$$
- **Zero-Division Defense**: Handled at the pipeline level to return `0.0%` when no sales exist.

### 2.4 Total Orders & Units Sold
- **Total Orders**: $\text{Count of unique orders matching tenant and store filter}$.
- **Units Sold**: $\sum_{i=1}^{N} \text{orders}[i].\text{total\_quantity}$.

### 2.5 Average Order Value (AOV)
- **Definition**: The average revenue generated per completed customer transaction.
- **Formula**:
  $$\text{AOV} = \begin{cases} \frac{\text{Total Sales}}{\text{Total Orders}} & \text{if Total Orders} > 0 \\ 0.0 & \text{if Total Orders} = 0 \end{cases}$$

---

## 3. Line-Item Financial Pricing & Discount Engine

For each order line item:
1. **Gross Value**:
   $$\text{Gross} = \text{quantity} \times \text{unit\_price}$$
2. **Net Line Sales (Post-Discount)**:
   $$\text{line\_sales} = \text{round}\big(\text{Gross} \times (1.0 - \text{discount\_rate}), 2\big)$$
3. **Cost Basis**:
   $$\text{cost\_basis} = \text{round}(\text{quantity} \times \text{unit\_cost}, 2)$$
4. **Net Line Profit**:
   $$\text{line\_profit} = \text{round}(\text{line\_sales} - \text{cost\_basis}, 2)$$

---

## 4. Multi-Store Inventory Valuation & Alerts

### 4.1 Stock Valuation
- **Formula**:
  $$\text{Valuation} = \text{quantity\_on\_hand} \times \text{unit\_cost}$$
- Evaluated strictly using verified product cost basis.

### 4.2 Stock Threshold Alerts
- **CRITICAL (Stockout)**: $\text{quantity\_on\_hand} = 0$.
- **WARNING (Low Stock)**: $0 < \text{quantity\_on\_hand} \le \text{min\_threshold}$.

---

## 5. Explainable Business Insights Rules

| Insight Category | Trigger Condition | Severity | Rationale Explained to User |
| :--- | :--- | :--- | :--- |
| **INVENTORY_ALERT** | $\text{quantity\_on\_hand} = 0$ | `CRITICAL` | Item is out of stock at the specific store, risking lost sales. |
| **INVENTORY_ALERT** | $\text{quantity\_on\_hand} \le \text{min\_threshold}$ | `WARNING` | Stock is at or below safety stock threshold; reorder recommended. |
| **CATEGORY_PERFORMANCE** | Category profit margin $< 15.0\%$ | `WARNING` | Product category exhibits low margin relative to target; vendor pricing or discounts should be reviewed. |
| **CONCENTRATION_RISK** | Top SKU generates $\ge 30.0\%$ of sales | `INFO` | Single product accounts for disproportionate revenue share; diversification recommended. |
| **OPERATIONAL_HEALTH** | No active alerts or margin warnings | `INFO` | All store operations and inventory levels are within normal bounds. |
