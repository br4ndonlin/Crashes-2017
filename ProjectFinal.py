"""
Name: Brandon Lin
CS230: Section 02
Data: Motor Vehicle Crashes in Massachusetts in 2017
Description:
This provides an easy way to look at motor vehicle crash data in Massachusetts for 2017. 
Users can:
- Filter data by year, city, or month to see specific crash details.
- View charts that show the number of crashes in each city and daily crashes each month.
- Explore a map that marks crash locations with details on their severity.
"""

import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk

# Setup the page configuration and aesthetics.
st.set_page_config(
    page_title="Massachusetts Traffic Crash Analysis",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_data(filepath):
    """
    Load and processes data from a CSV file.
    Perameters:
        filepath: The path to the CSV file containing the data.
    Returns:
        pandas.DataFrame: A DataFrame with
    """
    # Load CSV data
    data = pd.read_csv(filepath)
    # Convert the date column to a date time format
    data['CRASH_DATE_TEXT'] = pd.to_datetime(data['CRASH_DATE_TEXT'])
    return data

def get_data_by_city(df, city_name):
    """
    Filters data by specified city.
    Parameters:
        df: DataFrame containing the data.
        city_name: City name to filter data.
    Returns:
        Filtered DataFrame, severity counts DataFrame, total crash count.
    """
    # Filter data for the selected city
    filtered_data = df[df['CITY_TOWN_NAME'] == city_name]
    # Count occurrences of each severity
    severity_counts = filtered_data['CRASH_SEVERITY_DESCR'].value_counts().reset_index()
    severity_counts.columns = ['Severity', 'Count']
    # Calculate the total number of crashes
    total_crashes = filtered_data.shape[0]
    return filtered_data, severity_counts, total_crashes

def get_data_by_month(df, selected_month):
    """
    Filters and aggregates crash data by specified month.
    
    Parameters:
        df: DataFrame containing crash data.
        selected_month: Month number to filter data.
    
    Returns:
        Filtered DataFrame, daily crash counts, average crashes per day.
    """
    # Filter data for the selected month
    filtered_data = df[df['CRASH_DATE_TEXT'].dt.month == selected_month]
    # Count daily occurrences of crashes
    daily_counts = filtered_data['CRASH_DATE_TEXT'].dt.day.value_counts().reset_index()
    daily_counts.columns = ['Day', 'Count']
    # Calculate the average number of crashes per day
    average_crashes = daily_counts['Count'].mean()
    return filtered_data, daily_counts, average_crashes

# Create the sidebar.
with st.sidebar:
    st.title('🚗 Crash Data Analysis')
    filepath = '2017_Crashes_10000_sample.csv'
    df = load_data(filepath)
    
    # Allow the user to choose a year for the analysis
    year_list = sorted(df['CRASH_DATE_TEXT'].dt.year.dropna().unique())
    selected_year = st.selectbox('Select a Year', options=year_list)
    # Filter the data for the selected year
    df_selected_year = df[df['CRASH_DATE_TEXT'].dt.year == selected_year]
    
    # Allow the user to choose a month for the analysis
    month_list = sorted(df_selected_year['CRASH_DATE_TEXT'].dt.month.unique())
    selected_month = st.selectbox('Select a Month', month_list)
    
    # Allow the user to choose a city for the analysis
    city_list = sorted(df_selected_year['CITY_TOWN_NAME'].dropna().unique())
    selected_city = st.selectbox('Select a City', city_list)

    # Process data based on user choices
    df_selected_month, daily_counts, avg_crashes = get_data_by_month(df_selected_year, selected_month)
    df_selected_city, severity_counts, total_crashes = get_data_by_city(df_selected_year, selected_city)

    # Allow the user to select crash severities for the map
    severity_types = sorted(df_selected_year['CRASH_SEVERITY_DESCR'].dropna().unique())
    selected_severities = st.multiselect('Select Crash Severities to Display on Map', options=severity_types, default=severity_types)

# Display the main dashboard sections
col1, col2 = st.columns((1, 1))
with col1:
    st.markdown('#### Overall Crashes by City')
    st.write(f'Total crashes in {selected_city}: {total_crashes}')
    if not df_selected_city.empty:
        # Generate a bar chart of crash severities in the selected city
        city_chart = alt.Chart(severity_counts).mark_bar().encode(
            x='Severity:N', 
            y='Count:Q',
            color='Severity:N',
            tooltip=['Severity', 'Count']
        ).properties(width=400, height=300)
        st.altair_chart(city_chart, use_container_width=True)
    else:
        st.write("No data available for the selected city.")

with col2:
    st.markdown('#### Overall Crashes by Month')
    st.write(f'Average daily crashes in {selected_month}: {avg_crashes:.2f}')
    if not df_selected_month.empty:
        # Generate a bar chart of daily crashes in the selected month
        daily_chart = alt.Chart(daily_counts).mark_bar().encode(
            x='Day:O', 
            y='Count:Q',
            color='Count:Q', 
            tooltip=['Day', 'Count']
        ).properties(width=400, height=300)
        st.altair_chart(daily_chart, use_container_width=True)

# Map visualization using PyDeck 
st.markdown('#### Map of Crashes by Severity')
df_map = df_selected_year[(df_selected_year['CRASH_SEVERITY_DESCR'].isin(selected_severities)) & df_selected_year['LAT'].notna() & df_selected_year['LON'].notna()]
if not df_map.empty:
    # Setup the view state of the map
    view_state = pdk.ViewState(latitude=df_map['LAT'].mean(), longitude=df_map['LON'].mean(), zoom=10, pitch=50)
    # Create a layer for crash spots
    crash_layer = pdk.Layer(
        'ScatterplotLayer',
        data=df_map,
        get_position='[LON, LAT]',
        get_color='[200, 30, 0, 160]',
        get_radius=100,
        pickable=True,
        auto_highlight=True
    )
    # Define tooltip to show crash severity when hovering over a marker
    tooltip = {"text": "Severity: {CRASH_SEVERITY_DESCR}"}
    # Render the map
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=view_state,
        layers=[crash_layer],
        tooltip=tooltip
    ))
else:
    st.write("No data available for the selected severities or missing location data.")

with st.expander('About this dashboard'):
    st.write("""
        This dashboard provides an in-depth analysis of traffic crashes in Massachusetts. 
        Users can explore data based on city, month, and crash severity, with visualizations
    """)
