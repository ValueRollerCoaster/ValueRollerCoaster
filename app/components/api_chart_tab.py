import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import logging

# --- Data Fetching and Processing Functions (Largely unchanged) ---

# API endpoints dictionary
API_ENDPOINTS = {
    "Industry_Production": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/teiis090?format=JSON&lastTimePeriod=6&unit=PCH_M12_CA&indic_bt=PRD&nace_r2=C&lang=en",
    "Industry_Turnover": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/teiis150?format=JSON&unit=PCH_M12_CA&indic_bt=NETTUR&nace_r2=C&lang=en",
    "Producer_Prices_Intermediate_Goods": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/teiis040?format=JSON&unit=PCH_M12_NSA&indic_bt=PRC_PRR_DOM&nace_r2=MIG_ING&s_adj=NSA&lang=en",
    "Construction_Production": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/teiis500?format=JSON&unit=PCH_M12_CA&indic_bt=PRD&nace_r2=F&lang=en"
}
INDICATOR_COLUMNS = list(API_ENDPOINTS.keys())
EU_BENCHMARK_NAME = "European Union - 27 countries (from 2020)"

# Improved error handling and logging

def fetch_and_process_eurostat_data(indicator_name: str, url: str) -> pd.DataFrame:
    """Fetches and processes data from a single Eurostat API endpoint with robust error handling."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        try:
            data = response.json()
        except Exception as json_err:
            snippet = response.text[:300] if response.text else "<empty>"
            msg = f"Could not decode JSON for {indicator_name}. Status: {response.status_code}. Response: {snippet}"
            st.error(msg)
            logging.error(msg)
            return pd.DataFrame()
        if not data:
            msg = f"Empty response for {indicator_name}. Status: {response.status_code}"
            st.error(msg)
            logging.error(msg)
            return pd.DataFrame()
    except Exception as e:
        snippet = ''
        try:
            snippet = response.text[:300]
        except Exception:
            pass
        msg = f"Could not fetch data for {indicator_name}. Error: {e}. Response: {snippet}"
        st.warning(msg)
        logging.error(msg)
        return pd.DataFrame()

    dimensions = data.get('dimension', {})
    geo_labels = dimensions.get('geo', {}).get('category', {}).get('label', {})
    time_labels = dimensions.get('time', {}).get('category', {}).get('label', {})
    if not all([geo_labels, time_labels]): return pd.DataFrame()

    id_order, sizes = data['id'], data['size']
    time_pos, geo_pos = id_order.index('time'), id_order.index('geo')
    time_stride = 1
    for i in range(time_pos + 1, len(sizes)): time_stride *= sizes[i]
    geo_stride = 1
    for i in range(geo_pos + 1, len(sizes)): geo_stride *= sizes[i]
    values = data.get('value', {})
    records = []
    total_size = len(geo_labels) * len(time_labels)
    for i in range(total_size):
        if str(i) in values:
            time_index = (i // time_stride) % len(time_labels)
            geo_index = (i // geo_stride) % len(geo_labels)
            records.append({
                "Country": geo_labels[list(geo_labels.keys())[geo_index]],
                "Period": time_labels[list(time_labels.keys())[time_index]],
                indicator_name: values[str(i)]
            })
    return pd.DataFrame(records)

@st.cache_data(show_spinner="Fetching data from Eurostat APIs...")
def get_merged_data():
    """Fetches, merges, and cleans data. Cached for performance."""
    all_dataframes = [fetch_and_process_eurostat_data(name, url) for name, url in API_ENDPOINTS.items()]
    valid_dataframes = [df for df in all_dataframes if not df.empty]
    if not valid_dataframes: return pd.DataFrame()

    merged_df = valid_dataframes[0]
    for df_to_merge in valid_dataframes[1:]:
        merged_df = pd.merge(merged_df, df_to_merge, on=["Country", "Period"], how="outer")

    merged_df['Period'] = pd.to_datetime(merged_df['Period'], format='%Y-%m')
    country_order = sorted([c for c in merged_df['Country'].unique() if c != EU_BENCHMARK_NAME])
    # Ensure the EU Benchmark is always first in the list
    if EU_BENCHMARK_NAME in merged_df['Country'].unique():
        country_order.insert(0, EU_BENCHMARK_NAME)
    
    merged_df['Country'] = pd.Categorical(merged_df['Country'], categories=country_order, ordered=True)
    merged_df = merged_df.sort_values(by=['Country', 'Period']).reset_index(drop=True)
    return merged_df

# --- Streamlit App Definition ---

def api_chart_tab():
    st.header("Economic Indicator Trends vs. EU Benchmark")
    st.info(f"""
        Select a country to see its economic indicator trends.
        The data is automatically compared against the **{EU_BENCHMARK_NAME}** (shown as dashed lines)
        to provide a clear performance benchmark.
    """)

    # --- Load Data and Create Controls ---
    merged_df = get_merged_data()

    if merged_df.empty:
        st.error("Failed to fetch or process data from Eurostat APIs. Please try again later.")
        st.stop()
    
    country_options = merged_df['Country'].unique()
    selected_country = st.selectbox(
        "Select Country/Region:",
        options=country_options,
        index=0 
    )

    st.markdown("---")

    # Prepare data for faceted chart
    plot_df = pd.DataFrame()
    for indicator in INDICATOR_COLUMNS:
        # Country data
        country_df = merged_df[merged_df['Country'] == selected_country][['Period', indicator]].copy()
        if not isinstance(country_df, pd.DataFrame):
            country_df = pd.DataFrame()
        country_df['Series'] = selected_country
        country_df['Indicator'] = indicator
        country_df = country_df.rename(columns={indicator: 'Value'})
        # EU benchmark data
        eu_df = merged_df[merged_df['Country'] == EU_BENCHMARK_NAME][['Period', indicator]].copy()
        if not isinstance(eu_df, pd.DataFrame):
            eu_df = pd.DataFrame()
        eu_df['Series'] = 'EU Benchmark'
        eu_df['Indicator'] = indicator
        eu_df = eu_df.rename(columns={indicator: 'Value'})
        # Combine
        combined = pd.concat([country_df, eu_df])
        plot_df = pd.concat([plot_df, combined])

    # Clean up for plotting
    plot_df = plot_df.dropna(subset=['Value'], how='all')
    plot_df['Period'] = pd.to_datetime(plot_df['Period'])

    # Faceted line chart
    fig = px.line(
        plot_df,
        x='Period',
        y='Value',
        color='Series',
        facet_col='Indicator',
        facet_col_wrap=2,
        markers=True,
        title=f'Economic Indicator Trends vs. EU Benchmark: {selected_country}',
        labels={'Value': 'YoY % Change', 'Indicator': 'Economic Indicator'}
    )
    fig.update_traces(opacity=0.85)
    fig.update_layout(height=500, legend_title_text='Series', margin=dict(t=60, b=40, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

# To run this file directly for testing:
if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="Eurostat Dashboard")
    api_chart_tab()