# Inventory Replenishment Agent

This project builds a simple inventory replenishment agent for a small supply chain scenario. The agent uses historical sales data to forecast demand, calculates safety stock, and decides whether to place a purchase order or wait. The goal is to reduce stockouts while also controlling total inventory-related cost.

## Project Goal
The agent is designed to:
- minimize stockouts
- improve fill rate
- control total cost

## Inputs
The project uses 3 CSV files:
- `sales.csv` — daily sales by SKU  
  Columns: `date, sku, qty_sold`
- `inventory.csv` — starting inventory by SKU  
  Columns: `sku, opening_stock`
- `params.csv` — policy and cost settings by SKU  
  Columns: `sku, unit_cost, holding_cost_per_day, stockout_cost, lead_time_days, min_order_qty, service_level`

## Outputs
The code produces:
- `daily_agent_log.csv` — daily agent decisions and rationale
- `daily_baseline_log.csv` — baseline simulation log
- `agent_summary.csv` — final agent results
- `baseline_summary.csv` — final baseline results
- `evaluation_comparison.csv` — comparison between agent and baseline

## Agent Logic
The agent:
1. Loads and aggregates demand per SKU per day
2. Forecasts demand using EWMA
3. Computes safety stock using service level and forecast error
4. Projects inventory over the lead time
5. Places an order if projected inventory falls below the reorder point
6. Respects minimum order quantity
7. Simulates purchase order arrivals after lead time
8. Logs each daily decision with a short explanation

## Baseline
The baseline uses a simpler replenishment rule without the EWMA forecasting logic. This provides a comparison point for stockouts, fill rate, and total cost.

## Metrics
The project evaluates:
- stockouts
- fill rate
- total cost

Total cost includes:
- holding cost
- stockout cost

## Files in This Repo
- `inventory_replenishment_agent.ipynb` or `inventory_replenishment_agent.py` — main notebook/code
- `sales.csv` — sales data
- `inventory.csv` — starting stock
- `params.csv` — SKU parameters
- `daily_agent_log.csv` — daily agent decisions
- `daily_baseline_log.csv` — daily baseline output
- `agent_summary.csv` — agent results summary
- `baseline_summary.csv` — baseline summary
- `evaluation_comparison.csv` — side-by-side performance comparison
- `design_doc.docx` — short design document
- `scaling_note.docx` — short scaling note

## How to Run
1. Open the notebook in Google Colab or run the Python script locally
2. Make sure `sales.csv`, `inventory.csv`, and `params.csv` are in the same folder
3. Run the notebook/script
4. Review the output CSV files

## Result Summary
The agent improved inventory performance compared to the baseline by reducing stockouts and improving fill rate while managing total cost.

## Trust and Business Considerations
This agent is designed to support reliable product availability while avoiding unrealistic over-ordering. Daily decision logs make the agent easier to review and trust. This helps balance customer service reliability with cost responsibility.
