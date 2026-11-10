# streamlit_app.py
import streamlit as st
import pandas as pd
import json
import os
import sqlite3
import gzip
import math
import plotly.express as px
from pathlib import Path
from phonepe_map_utils import join_states
from phonepe_insights import get_period_insights
from phonepe_district_utils import choose_boundaries

st.set_page_config(layout='wide', page_title='📊 PhonePe Transaction Insights')

# ---------------------------
# Sidebar Configuration
# ---------------------------
st.sidebar.title("⚙️ Configuration")

DB_PATH = st.sidebar.text_input("SQLite DB Path", value="pulse.db")


st.sidebar.markdown("**Data source:** local SQLite DB created by `etl.py`")

# Connect to database
if not os.path.exists(DB_PATH):
    st.error(f"Database not found at {DB_PATH}. Please check your path.")
    st.stop()

conn = sqlite3.connect(DB_PATH)

def load_table(query: str):
    """Run a SQL query and return a DataFrame."""
    return pd.read_sql(query, conn)


@st.cache_data
def load_district_table(path: str, modified_at: float):
    return pd.read_csv(path)


@st.cache_data
def load_archive_table(path: str, modified_at: float):
    return pd.read_csv(path, dtype={'pincode': 'string'})


@st.cache_resource
def load_district_shapes(path: str, modified_at: float):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)

st.title("📈 PhonePe Transaction Insights Dashboard")

# ---------------------------
# Filters
# ---------------------------
years = pd.read_sql("SELECT DISTINCT year FROM aggregated_transaction ORDER BY year", conn)['year'].dropna().tolist()
quarters = pd.read_sql("SELECT DISTINCT quarter FROM aggregated_transaction ORDER BY quarter", conn)['quarter'].dropna().tolist()

col1, col2 = st.sidebar.columns(2)
year = col1.selectbox("📅 Year", options=years, index=len(years) - 1 if years else 0)
quarter = col2.selectbox("🕒 Quarter", options=quarters, index=0 if quarters else 0)

# The commentary is computed for the selected quarter, not hard-coded to 2024.
st.header(f"🔎 Key insights and conclusion — {year} Q{quarter}")
insights = get_period_insights(conn, year, quarter)
if insights is None:
    st.info("No state-level data is available for this selection.")
else:
    amount = insights['total_amount']
    count = insights['total_count']
    count_delta = insights['count_growth']
    amount_delta = insights['amount_growth']
    c1, c2 = st.columns(2)
    c1.metric('Transactions', f"{count / 1e9:,.2f} billion", None if count_delta is None else f"{count_delta:+.1f}% vs same quarter last year")
    c2.metric('Transaction value', f"₹{amount / 1e12:,.2f} lakh crore", None if amount_delta is None else f"{amount_delta:+.1f}% vs same quarter last year")
    if count_delta is None or amount_delta is None:
        st.caption('A comparison with the same quarter of the previous year is unavailable in this snapshot.')
    categories = insights['categories']
    if not categories.empty and count > 0 and amount > 0:
        lead_count = categories['count'].idxmax()
        lead_amount = categories['amount'].idxmax()
        count_share = categories.loc[lead_count, 'count'] / count * 100
        amount_share = categories.loc[lead_amount, 'amount'] / amount * 100
        st.markdown(f"- **Payment mix:** {lead_count} accounted for {count_share:.1f}% of transaction count; {lead_amount} accounted for {amount_share:.1f}% of transaction value.")
    if not insights['states'].empty and insights['top_five_share'] is not None:
        leader = str(insights['states'].index[0]).replace('-', ' ').title()
        st.markdown(f"- **Geographic concentration:** {leader} had the highest transaction value. The five largest state/UT totals contributed {insights['top_five_share']:.1f}% of the selected period's value.")
    st.markdown('**Conclusion:** Compare transaction count and value together: they describe different aspects of payment activity. Use the state map and payment breakdown below to explore the selected period.')
    st.caption('Historical state-level aggregates only; country totals are excluded to avoid double counting. Amounts are not per-person adoption, and these aggregates cannot establish causes.')

# User metrics are reported separately from transactions and use one geography level.
st.header(f"👥 Registered users and app opens — {year} Q{quarter}")
user_total = load_table(f"""
SELECT registered_users, app_opens FROM aggregated_user
WHERE level = 'country' AND year = {year} AND quarter = '{quarter}'
""")
if len(user_total) == 1:
    u1, u2 = st.columns(2)
    u1.metric('Reported registered users', f"{int(user_total.iloc[0]['registered_users']):,}")
    u2.metric('Reported app opens', f"{int(user_total.iloc[0]['app_opens']):,}")
    st.caption('Figures are the country-level values reported in the historical snapshot. Registered users are not the same as active users; app opens are events, not unique people. Do not add user snapshots across quarters.')
    user_states = load_table(f"""
        SELECT state, registered_users, app_opens FROM aggregated_user
        WHERE level = 'state' AND year = {year} AND quarter = '{quarter}'
        ORDER BY registered_users DESC LIMIT 10
    """)
    if not user_states.empty:
        st.dataframe(user_states.style.format({'registered_users': '{:,.0f}', 'app_opens': '{:,.0f}'}))
else:
    st.info('A single country-level user record is not available for this period, so no user total is shown.')

# ---------------------------
# Top States by Transaction
# ---------------------------
st.header(f"🏆 Top States by Transaction Amount — {year} Q{quarter}")

q = f"""
SELECT state, SUM(amount) as total_amount, SUM(count) as total_count
FROM aggregated_transaction
WHERE level = 'state' AND year = {year} AND quarter = '{quarter}' AND state IS NOT NULL
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
WHERE level = 'state'
GROUP BY year, quarter ORDER BY year, CAST(quarter AS INTEGER)
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
st.header(f"💳 Payment Category Breakdown — {year} Q{quarter}")
cat_q = f"""
SELECT txn_type, SUM(amount) as amount
FROM aggregated_transaction
WHERE level = 'state' AND year = {year} AND quarter = '{quarter}'
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

geojson_path = Path(__file__).resolve().parent / "geo" / "india_states.geojson"

if geojson_path.exists():
    with open(geojson_path, 'r', encoding='utf-8') as f:
        gj = json.load(f)
    df_map = load_table(f"""
        SELECT state, SUM(amount) AS total_amount, SUM(count) AS total_count
        FROM aggregated_transaction
        WHERE level = 'state' AND year = {year} AND quarter = '{quarter}'
        GROUP BY state
    """)
    df_map, unmatched = join_states(df_map, gj)
    matched = df_map.dropna(subset=['shape_iso'])
    if unmatched:
        st.warning("No boundary match for: " + ", ".join(unmatched))
    if not matched.empty:
        fig_map = px.choropleth_map(
            matched, geojson=gj, locations='shape_iso',
            featureidkey='properties.shapeISO', color='total_amount',
            hover_name='state', hover_data={'shape_iso': False, 'total_count': ':,'},
            color_continuous_scale='Viridis', map_style='white-bg',
            center={'lat': 22.5, 'lon': 79}, zoom=2.9, opacity=0.8,
            labels={'total_amount': 'Transaction amount (INR)', 'total_count': 'Transactions'},
            title=f'State transaction amount: {year} Q{quarter}',
        )
        fig_map.update_layout(margin={'r': 0, 't': 60, 'l': 0, 'b': 0}, height=600)
        st.plotly_chart(fig_map, use_container_width=True)
        st.caption(f"Matched {len(matched)} of {len(df_map)} state/UT records. Boundaries: geoBoundaries / DataMeet India and Election Commission of India, CC BY 2.5 IN. Boundary vintage may differ from the transaction data.")
    else:
        st.warning("No transaction data with matching boundaries for this quarter.")
else:
    st.warning("The local state boundary file is missing. Restore geo/india_states.geojson.")

# ---------------------------
# District data from a separately sourced, pinned PhonePe Pulse revision.
# ---------------------------
st.markdown("---")
st.header("🌍 District explorer — separate updated source")
st.warning("This section uses a separate PhonePe Pulse revision dated 24 September 2026. The older database used above has different historical values, so do not combine the two snapshots or compare their totals directly.")
district_path = Path(__file__).resolve().parent / 'district_data' / 'district_transactions.csv.gz'
boundary_dir = Path(__file__).resolve().parent / 'district_data'
boundary_files = [('2011 Census', boundary_dir / 'district_boundaries_2011.geojson.gz'),
                  ('2019 collection (mixed 2011–2019 boundaries)', boundary_dir / 'district_boundaries_2019.geojson.gz')]
if district_path.exists():
    district_all = load_district_table(str(district_path), district_path.stat().st_mtime)
    period_districts = district_all[(district_all['year'] == int(year)) & (district_all['quarter'] == int(quarter))]
    if not period_districts.empty:
        states = sorted(period_districts['state'].unique())
        default_state = states.index('karnataka') if 'karnataka' in states else 0
        selected_state = st.selectbox('District state / union territory', states, index=default_state,
                                      format_func=lambda s: s.replace('-', ' ').title())
        districts = period_districts[period_districts['state'] == selected_state].copy()
        districts = districts.sort_values('transaction_amount', ascending=False)
        st.subheader(f"District transaction values — {selected_state.replace('-', ' ').title()}, {year} Q{quarter}")
        st.dataframe(districts[['district', 'transaction_count', 'transaction_amount']].style.format(
            {'transaction_count': '{:,.0f}', 'transaction_amount': '₹{:,.0f}'}))
        st.download_button('Download district data CSV',
                           districts[['state', 'year', 'quarter', 'district', 'transaction_count', 'transaction_amount']].to_csv(index=False).encode('utf-8'),
                           f'districts_{selected_state}_{year}_Q{quarter}.csv', 'text/csv')
        sources = [(label, load_district_shapes(str(path), path.stat().st_mtime))
                   for label, path in boundary_files if path.exists()]
        if sources:
            boundary_label, district_shapes, matched, unmatched = choose_boundaries(districts, selected_state, sources)
            matched = matched.dropna(subset=['shape_key'])
            st.caption(f"Matched {len(matched)} of {len(districts)} district names using {boundary_label}. The app selects one historical boundary collection for each state based on name matches. Boundaries may have changed or split; colors do not show exact current boundaries.")
            if not matched.empty:
                keys=set(matched['shape_key'])
                features=[f for f in district_shapes['features'] if f['properties']['shape_key'] in keys]
                boxes=[f['properties']['bbox'] for f in features]
                west=min(x[0] for x in boxes); south=min(x[1] for x in boxes)
                east=max(x[2] for x in boxes); north=max(x[3] for x in boxes)
                span=max(east-west,north-south,0.1)
                zoom=max(2.5,min(7.5,math.log2(360.0/span*0.45)+0.75))
                fig_district=px.choropleth_map(
                    matched, geojson={'type':'FeatureCollection','features':features},
                    locations='shape_key', featureidkey='properties.shape_key',
                    color='transaction_amount', hover_name='district',
                    hover_data={'shape_key':False,'transaction_count':':,'},
                    labels={'transaction_amount':'Transaction amount (INR)','transaction_count':'Transactions'},
                    color_continuous_scale='Viridis', map_style='white-bg',
                    center={'lat':(south+north)/2,'lon':(west+east)/2}, zoom=zoom, opacity=0.8,
                    title=f'Partial district map — {boundary_label}')
                fig_district.update_layout(height=560,margin={'r':0,'t':60,'l':0,'b':0})
                st.plotly_chart(fig_district, use_container_width=True)
            else:
                st.info('No district names matched the available historical boundaries for this state.')
            if unmatched:
                with st.expander('Districts not shown on the map'):
                    st.write(', '.join(unmatched))
            st.caption('2011 boundaries: DataMeet India community, CC BY 2.5 IN. The 2019 collection: Guneet Narula and contributors, MIT, with DataMeet attribution. PhonePe Pulse data: CDLA-Permissive-2.0. Full attribution, dates and source commits are included in district_data/.')
        else:
            st.info('The optional district-boundary files are missing; the district data table remains available.')
    else:
        st.info('The updated district source has no records for this quarter.')
else:
    st.info('The optional district source files are missing; restore the district_data folder.')
st.markdown('---')
st.header('📍 PIN codes and insurance — historical archive')
st.caption('This section uses an archived third-party mirror of the older PhonePe Pulse release, pinned to 4 March 2025. Its 5,034 overlapping transaction-category records and 682 insurance records matched the local database; it is separate from the restated 2026 district data above. Insurance values are already represented in the older database and must not be added again to its totals.')
archive_dir=Path(__file__).resolve().parent / 'archive_data'
pin_path=archive_dir / 'transaction_top_pincodes.csv.gz'
insurance_path=archive_dir / 'aggregated_insurance.csv.gz'
if pin_path.exists():
    pins=load_archive_table(str(pin_path),pin_path.stat().st_mtime)
    period_pins=pins[(pins.year==int(year)) & (pins.quarter==int(quarter))]
    if not period_pins.empty:
        state_options=['India']+sorted(period_pins.loc[period_pins.level=='state','state'].unique())
        scope=st.selectbox('PIN code coverage',state_options,format_func=lambda s:s.replace('-',' ').title())
        selected_pins=period_pins[(period_pins.state==scope) & (period_pins.level==('country' if scope=='India' else 'state'))].sort_values('source_rank')
        st.subheader(f'Top reported PIN codes — {scope.replace("-", " ").title()}, {year} Q{quarter}')
        st.caption('The source provides up to ten leading PIN codes ranked by transaction count, not all PIN codes. The amount column refers to those same selected PIN codes; it is not a ranking by amount.')
        st.dataframe(selected_pins[['source_rank','pincode','count','amount']].rename(columns={'source_rank':'rank','count':'transaction_count','amount':'transaction_amount'}).style.format({'transaction_count':'{:,.0f}','transaction_amount':'₹{:,.0f}'}))
        st.download_button('Download reported PIN codes CSV',selected_pins.to_csv(index=False).encode('utf-8'),f'phonepe_top_pins_{scope}_{year}_Q{quarter}.csv','text/csv')
    else:
        st.info('The historical archive has no PIN-code entries for this quarter.')
else:
    st.info('Historical PIN-code data is unavailable; restore archive_data/.')

if insurance_path.exists():
    insurance=load_archive_table(str(insurance_path),insurance_path.stat().st_mtime)
    period_ins=insurance[(insurance.year==int(year)) & (insurance.quarter==int(quarter))]
    national=period_ins[period_ins.level=='country']
    states_ins=period_ins[period_ins.level=='state'].sort_values('count',ascending=False)
    st.subheader(f'Insurance — {year} Q{quarter}')
    if not national.empty:
        totals=national.iloc[0]
        col_a,col_b=st.columns(2)
        col_a.metric('Reported insurance count',f"{int(totals['count']):,}")
        col_b.metric('Reported insurance amount',f"₹{float(totals['amount']):,.0f}")
    if not states_ins.empty:
        st.plotly_chart(px.bar(states_ins.head(10),x='state',y='count',
                               title='Ten states/UTs with highest reported insurance count',
                               labels={'state':'State / UT','count':'Insurance count'}),use_container_width=True)
        st.dataframe(states_ins[['state','count','amount']].style.format({'count':'{:,.0f}','amount':'₹{:,.0f}'}))
    if national.empty and states_ins.empty:
        st.info('The historical archive has no insurance data for this quarter.')
else:
    st.info('Historical insurance data is unavailable; restore archive_data/.')
st.caption('Archive source, commit and license are recorded in archive_data/. Rankings and totals describe the historical data, not current activity or per-person adoption.')

# ---------------------------
# Footer
# ---------------------------
st.markdown("---")
st.caption("📘 Built by Antony | Data Source: PhonePe Pulse | Visualization: Streamlit + Plotly")
