# streamlit_app.py
import streamlit as st
import pandas as pd
import json
import os
import sqlite3
import plotly.express as px
from pathlib import Path

st.set_page_config(layout='wide', page_title='📊 PhonePe Transaction Insights')

# ---------------------------
# Sidebar Configuration
# ---------------------------
st.sidebar.title("⚙️ Configuration")

DB_PATH = st.sidebar.text_input("SQLite DB Path", value="pulse.db")
PULSE_PATH = st.sidebar.text_input("Pulse repo path (for geojson)", value="./pulse")

st.sidebar.markdown("**Data source:** local SQLite DB created by `etl.py`")

# Connect to database
if not os.path.exists(DB_PATH):
    st.error(f"Database not found at {DB_PATH}. Please check your path.")
    st.stop()

conn = sqlite3.connect(DB_PATH)

@st.cache_data
def load_table(query: str):
    """Run a SQL query and return a DataFrame."""
    return pd.read_sql(query, conn)

st.title("📈 PhonePe Transaction Insights Dashboard")

# ---------------------------
# Filters
# ---------------------------
years = pd.read_sql("SELECT DISTINCT year FROM aggregated_transaction ORDER BY year", conn)['year'].dropna().tolist()
quarters = pd.read_sql("SELECT DISTINCT quarter FROM aggregated_transaction ORDER BY quarter", conn)['quarter'].dropna().tolist()

col1, col2 = st.sidebar.columns(2)
year = col1.selectbox("📅 Year", options=years, index=len(years) - 1 if years else 0)
quarter = col2.selectbox("🕒 Quarter", options=quarters, index=0 if quarters else 0)

# ---------------------------
# Top States by Transaction
# ---------------------------
st.header(f"🏆 Top States by Transaction Amount — {year} Q{quarter}")

q = f"""
SELECT state, SUM(amount) as total_amount, SUM(count) as total_count
FROM aggregated_transaction
WHERE year = {year} AND quarter = '{quarter}' AND state IS NOT NULL
GROUP BY state
ORDER BY total_amount DESC
LIMIT 20
"""
top_states = load_table(q)

if not top_states.empty:
    st.dataframe(top_states.style.format({"total_amount": "₹{:,.0f}", "total_count": "{:,.0f}"}))
    fig = px.bar(
        top_states,
        x='state',
        y='total_amount',
        title='Top 20 States by Transaction Amount',
        color='total_amount',
        color_continuous_scale='Blues',
        labels={'total_amount': 'Total Amount (₹)'},
    )
    st.plotly_chart(fig, use_container_width=True)
    st.download_button("📥 Download CSV", top_states.to_csv(index=False).encode('utf-8'),
                       "top_states.csv", "text/csv")
else:
    st.warning("No transaction data available for the selected year and quarter.")

# ---------------------------
# Trend Over Time
# ---------------------------
st.header("📉 Transaction Trend: Total Amount by Quarter (All Years)")
ts = load_table("""
SELECT year || '-' || quarter as period, SUM(amount) as total_amount
FROM aggregated_transaction
GROUP BY year, quarter ORDER BY year, quarter
""")
if not ts.empty:
    fig2 = px.line(ts, x='period', y='total_amount', markers=True,
                   title='Transaction Trend Over Time',
                   labels={'total_amount': 'Total Amount (₹)'})
    fig2.update_traces(hovertemplate="Quarter %{x}<br>₹%{y:,.0f}")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.warning("No trend data available.")

# ---------------------------
# Payment Category Breakdown
# ---------------------------
st.header("💳 Payment Category Breakdown")
cat_q = """
SELECT txn_type, SUM(amount) as amount
FROM aggregated_transaction
GROUP BY txn_type
ORDER BY amount DESC
LIMIT 20
"""
cats = load_table(cat_q)
if not cats.empty:
    st.dataframe(cats.style.format({"amount": "₹{:,.0f}"}))
    fig3 = px.pie(
        cats,
        names='txn_type',
        values='amount',
        title='Share of Payment Categories',
        hole=0.3,
    )
    st.plotly_chart(fig3, use_container_width=True)
    st.download_button("📥 Download CSV", cats.to_csv(index=False).encode('utf-8'),
                       "payment_categories.csv", "text/csv")
else:
    st.warning("No payment category data found.")

# ---------------------------
# Choropleth Map by State
# ---------------------------
st.header("🗺️ Choropleth: State-Level Transaction Amounts")

geojson_path = Path(PULSE_PATH) / "data" / "geojson" / "india_states.geojson"

if geojson_path.exists():
    with open(geojson_path, 'r', encoding='utf-8') as f:
        gj = json.load(f)

    df_map = load_table(f"""
    SELECT state, SUM(amount) as total_amount
    FROM aggregated_transaction
    WHERE year = {year} AND quarter = '{quarter}' AND state IS NOT NULL
    GROUP BY state
    """)

    if not df_map.empty:
        # Normalize DB state names to match GeoJSON "NAME_1"
        df_map['state'] = (
            df_map['state']
            .str.replace('-', ' ', regex=False)
            .str.replace('&', 'and', regex=False)
            .str.title()
        )

        # Plot Map
        try:
            fig_map = px.choropleth_mapbox(
                df_map,
                geojson=gj,
                locations='state',
                featureidkey='properties.NAME_1',
                color='total_amount',
                hover_name='state',
                color_continuous_scale='Viridis',
                mapbox_style="carto-positron",
                center={"lat": 22.0, "lon": 78.0},
                zoom=3.5,
                opacity=0.7,
                labels={'total_amount': 'Total Amount (₹)'}
            )
            fig_map.update_traces(hovertemplate="<b>%{location}</b><br>₹%{z:,.0f}")
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
        except Exception as e:
            st.error(f"Map plotting failed: {e}")
    else:
        st.warning("No data available for map rendering.")
else:
    st.warning("⚠️ GeoJSON not found. Place it at: pulse/data/geojson/india_states.geojson")

# ---------------------------
# Top Regions (from top_map)
# ---------------------------
st.markdown("---")
st.header("🌍 Top Regions from Top Map Table")

top_df = load_table("""
SELECT category, region, amount, rank, year, quarter
FROM top_map
ORDER BY year DESC, rank ASC
LIMIT 100
""")

if not top_df.empty:
    st.dataframe(top_df.style.format({"amount": "₹{:,.0f}"}))
    st.download_button("📥 Download CSV", top_df.to_csv(index=False).encode('utf-8'),
                       "top_regions.csv", "text/csv")
else:
    st.warning("No top region data found.")

# ---------------------------
# Footer
# ---------------------------
st.markdown("---")
st.caption("📘 Built by Antony | Data Source: PhonePe Pulse | Visualization: Streamlit + Plotly")
