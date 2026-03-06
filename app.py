import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="US WARN Tracker | National Layoff Database",
    page_icon="📉",
    layout="wide"
)

# Custom CSS for a clean, professional look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DATA LOADING ---
# Replace 'your-username' and 'your-repo' with your actual GitHub details
DATA_URL = "https://raw.githubusercontent.com/your-username/your-repo/main/national_warn_master.csv"

@st.cache_data(ttl=3600) # Refreshes every hour
def load_data():
    try:
        df = pd.read_csv(DATA_URL)
        # Ensure date column is proper datetime objects
        df['date_filed'] = pd.to_datetime(df['date_filed'], errors='coerce')
        # Sort by most recent
        df = df.sort_values(by='date_filed', ascending=False)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

df = load_data()

# --- SIDEBAR: FILTERS & HEALTH ---
with st.sidebar:
    st.title("Settings & Health")
    
    if not df.empty:
        st.subheader("🛰️ Data Freshness")
        # Check the latest date for each state to see if scrapers are working
        latest_per_state = df.groupby('state')['date_filed'].max().sort_values(ascending=False)
        
        for state, last_date in latest_per_state.items():
            if pd.isna(last_date):
                continue
            # If data is older than 7 days, flag it
            is_fresh = last_date > (datetime.now() - timedelta(days=7))
            icon = "✅" if is_fresh else "⚠️"
            color = "green" if is_fresh else "orange"
            st.markdown(f"{icon} **{state}**: :{color}[{last_date.strftime('%Y-%m-%d')}]")
    
    st.divider()
    st.write("Data aggregated from State Departments of Labor via the WARN Act.")

# --- MAIN DASHBOARD ---
st.title("📉 National WARN Notice Tracker")
st.markdown("Automated monitoring of mass layoffs and plant closures across the United States.")

if df.empty:
    st.warning("No data found. Ensure your GitHub Action has run and created 'national_warn_master.csv'.")
else:
    # --- ROW 1: KEY METRICS ---
    total_workers = int(df['workers_affected'].sum())
    total_notices = len(df)
    unique_companies = df['company_name'].nunique()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Workers Affected", f"{total_workers:,}")
    m2.metric("Total WARN Notices", f"{total_notices:,}")
    m3.metric("Unique Companies", f"{unique_companies:,}")

    # --- ROW 2: VISUALIZATIONS ---
    st.divider()
    col_map, col_bar = st.columns([2, 1])

    with col_map:
        st.subheader("Geographical Distribution")
        state_counts = df.groupby('state')['workers_affected'].sum().reset_index()
        fig_map = px.choropleth(
            state_counts,
            locations='state',
            locationmode="USA-states",
            color='workers_affected',
            scope="usa",
            color_continuous_scale="Reds",
            labels={'workers_affected': 'Impacted Workers'}
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)

    with col_bar:
        st.subheader("Top 10 Largest Layoffs")
        # Filter for top 10 companies by total workers affected
        top_10 = df.groupby('company_name')['workers_affected'].sum().nlargest(10).reset_index()
        fig_bar = px.bar(
            top_10,
            x='workers_affected',
            y='company_name',
            orientation='h',
            color='workers_affected',
            color_continuous_scale="Reds",
            labels={'company_name': 'Company', 'workers_affected': 'Workers'}
        )
        fig_bar.update_layout(showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- ROW 3: SEARCHABLE DATA ---
    st.divider()
    st.subheader("🔍 Search Records")
    
    # Filtering options
    search_col1, search_col2 = st.columns(2)
    with search_col1:
        query = st.text_input("Search by Company Name", placeholder="e.g. Amazon, Tesla...")
    with search_col2:
        states = st.multiselect("Filter by State", options=sorted(df['state'].unique()))

    # Apply filters
    filtered_df = df
    if query:
        filtered_df = filtered_df[filtered_df['company_name'].str.contains(query, case=False, na=False)]
    if states:
        filtered_df = filtered_df[filtered_df['state'].isin(states)]

    # Display Table
    st.dataframe(
        filtered_df[['state', 'company_name', 'workers_affected', 'date_filed']], 
        use_container_width=True,
        hide_index=True
    )

    # Download Button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Data (CSV)",
        data=csv,
        file_name="warn_layoffs_export.csv",
        mime="text/csv",
    )
