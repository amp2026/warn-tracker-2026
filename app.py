import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="US Layoff Tracker (BLN Data)", layout="wide")

# --- DATA SOURCE ---
# This is the direct link to the Big Local News consolidated national dataset
DATA_URL = "https://storage.googleapis.com/bln-data-public/warn-layoffs/national_historical.csv"

@st.cache_data(ttl=86400) # Cache for 24 hours
def load_bln_data():
    df = pd.read_csv(DATA_URL)
    
    # Standardizing BLN columns to our app's needs
    # BLN usually uses 'p_company' or 'company' and 'p_workers' or 'workers'
    # We'll normalize them here:
    df = df.rename(columns={
        'p_company': 'company_name',
        'company': 'company_name',
        'p_workers': 'workers_affected',
        'workers': 'workers_affected',
        'p_date': 'date_filed',
        'date': 'date_filed',
        'p_state': 'state',
        'state': 'state'
    })
    
    # Convert date and ensure workers is numeric
    df['date_filed'] = pd.to_datetime(df['date_filed'], errors='coerce')
    df['workers_affected'] = pd.to_numeric(df['workers_affected'], errors='coerce').fillna(0)
    
    return df

df = load_bln_data()

# --- DASHBOARD UI ---
st.title("📉 National Layoff Monitor")
st.caption("Powered by Big Local News (Stanford University) Open Data")

if not df.empty:
    # Top Metrics
    total_workers = int(df['workers_affected'].sum())
    st.metric("Total Workers Affected (Historical)", f"{total_workers:,}")

    # Map Visualization
    st.subheader("Impact by State")
    state_totals = df.groupby('state')['workers_affected'].sum().reset_index()
    fig = px.choropleth(
        state_totals,
        locations='state',
        locationmode="USA-states",
        color='workers_affected',
        scope="usa",
        color_continuous_scale="Reds"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Search Table
    st.subheader("🔍 Search All Records")
    search = st.text_input("Search company...")
    if search:
        df = df[df['company_name'].str.contains(search, case=False, na=False)]
    
    st.dataframe(df[['state', 'company_name', 'workers_affected', 'date_filed']].head(500), use_container_width=True)
