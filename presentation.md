Slide 1 — Title
PhonePe Transaction Insights
Your Name | Date

Slide 2 — Project Overview
Objective: Analyze PhonePe transaction data to derive geographic, category and user insights.
Domain: Finance / Payment Systems
Skills demonstrated: Data extraction, SQL, visualization, Streamlit

Slide 3 — Data & Tools
Data: PhonePe Pulse (JSON & GeoJSON)
Tools: Python, Pandas, PostgreSQL/SQLite, Streamlit, Plotly, GeoJSON

Slide 4 — Approach
1. Extract JSON files from repo
2. Load into SQL tables (ETL)
3. SQL analysis for business questions
4. Visualize using Streamlit & maps
5. Generate insights & recommendations

Slide 5 — Schema & ETL
Show db_schema.sql brief structure:
- aggregated_transaction, aggregated_user, aggregated_insurance
- map_values, top_map
ETL: python etl.py → loads SQLite / Postgres

Slide 6 — Key Visualizations
- Top states by transaction amount (bar)
- Time series: quarter-wise txn amount
- Payment category breakdown (pie)
- State-level choropleth (map)

Slide 7 — Business Use-cases & Queries
- Customer segmentation query
- Fraud detection heuristic (avg txn > 4x median)
- Insurance-specific trends table

Slide 8 — Insights (example)
- Top 3 states: Maharashtra, Karnataka, Tamil Nadu (example)
- Category leader: Merchant Payments (example)
- Recommendation: Boost services and merchant onboarding in top Tier-2 districts.

Slide 9 — Recommendations
- Tailor marketing to high-value districts
- Use anomaly detection to flag suspicious transaction spikes
- Improve insurance product UX in states with rising insurance counts

Slide 10 — Project Deliverables
- ETL script, DB schema, Streamlit app, queries, documentation & slides

Slide 11 — Next steps
- Add forecasting (Prophet/ARIMA)
- Add more granular pincode-level analytics
- Deploy Streamlit to Streamlit Cloud / Heroku

Slide 12 — Q&A
