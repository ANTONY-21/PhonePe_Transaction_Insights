<<<<<<< HEAD
# PhonePe Transaction Insights

## Project Summary
Analyze PhonePe Pulse JSON dataset to create aggregated analytics, choropleth maps, top regions and business insights. Deliverables: ETL scripts, SQL schema, analytics queries, and a Streamlit interactive dashboard.

## Prerequisites
- Python 3.9+
- git clone https://github.com/PhonePe/pulse.git
- PostgreSQL (optional) or SQLite

## Setup
1. Clone repo:
   ```
   git clone https://github.com/PhonePe/pulse.git
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   If geopandas fails, consider conda install or skip map features.

3. Run ETL to create SQLite DB:
   ```
   python etl.py --pulse_path ./pulse --db sqlite --sqlite_path pulse.db
   ```

4. Launch Streamlit dashboard:
   ```
   streamlit run streamlit_app.py
   ```

## Files
- `db_schema.sql` — SQL schema for DB.
- `etl.py` — extract JSON -> DB.
- `streamlit_app.py` — dashboard.
- `queries.sql` — analysis queries.
- `presentation.md` — slides outline.

## Notes & Troubleshooting
- Pulse JSON structures vary; ETL aims to handle typical cases. If you find missing records, open the JSON file and add a small parser branch in `etl.py`.
- GeoJSON naming sometimes uses different keys. Adjust `featureidkey` in `streamlit_app.py` to match the property used in the geojson file.
=======
# PhonePe_Transaction_Insights
Data Analysis and Visualization of PhonePe Pulse dataset using Python, SQL, and Streamlit
>>>>>>> edfc9612977516cb0cb7c2ea2725e712c9dfef3d
