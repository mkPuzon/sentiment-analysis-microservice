'''dashboard/app.py

Logic for dashboard service using PostgreSQL db data to analye trends in API request 
data and model performance.

Nov 2025
'''

import streamlit as st
import pandas as pd
import plotly.express as px
import os
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

# Setup page config
st.set_page_config(
    page_title="Sentiment Analysis Dashboard",
    layout="wide"
)

st.title("Real-time Sentiment Analysis Dashboard")

# Initialize connection
@st.cache_resource
def get_database_connection():
    if not DATABASE_URL:
        st.error("DATABASE_URL environment variable is not set.")
        return None
    try:
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None

engine = get_database_connection()

def load_data():
    if engine is None:
        return pd.DataFrame()
    
    try:
        # Increased limit to allow for better filtering
        query = "SELECT * FROM query_logs ORDER BY timestamp DESC LIMIT 5000"
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# --- Sidebar Controls ---
st.sidebar.header("Controls")

st.sidebar.divider()
st.sidebar.header("Filters")

df = load_data()

if not df.empty:
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    time_filter = st.sidebar.selectbox(
        "Time Range",
        ["All Time", "Last Hour", "Last 24 Hours", "Last 7 Days"]
    )

    # Apply Time Filter
    if time_filter == "Last Hour":
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        df = df[df['timestamp'] > cutoff]
    elif time_filter == "Last 24 Hours":
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        df = df[df['timestamp'] > cutoff]
    elif time_filter == "Last 7 Days":
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        df = df[df['timestamp'] > cutoff]

    if df.empty:
        st.info("No data available for the selected time range.")

    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_queries = len(df)
    positive_count = df[df['model_label'] == 'POSITIVE'].shape[0]
    negative_count = df[df['model_label'] == 'NEGATIVE'].shape[0]
    avg_score = df['model_score'].mean() if total_queries > 0 else 0
    
    col1.metric("Total Queries", total_queries)
    col2.metric("Positive", positive_count)
    col3.metric("Negative", negative_count)
    col4.metric("Avg Confidence", f"{avg_score:.2f}")
    
    st.divider()

    # Charts Row 1
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Sentiment Distribution")
        if total_queries > 0:
            fig_pie = px.pie(
                df, 
                names='model_label', 
                title="Positive vs Negative Ratio",
                color='model_label',
                color_discrete_map={'POSITIVE': "#00CC96", 'NEGATIVE': '#EF553B'}
            )
            st.plotly_chart(fig_pie, width=True)
        else:
            st.info("No data for distribution.")

    with col_chart2:
        st.subheader("Confidence Score Distribution")
        if total_queries > 0:
            fig_hist = px.histogram(
                df, 
                x='model_score', 
                nbins=20, 
                title="Score Distribution",
                color='model_label',
                color_discrete_map={'POSITIVE': '#00CC96', 'NEGATIVE': '#EF553B'}
            )
            st.plotly_chart(fig_hist, width=True)
        else:
            st.info("No data for histogram.")

    # Charts Row 2
    st.subheader("Sentiment Trends Over Time")
    if total_queries > 0:
        fig_scatter = px.scatter(
            df, 
            x='timestamp', 
            y='model_score', 
            color='model_label',
            hover_data=['input_text'],
            color_discrete_map={'POSITIVE': '#00CC96', 'NEGATIVE': '#EF553B'}
        )
        st.plotly_chart(fig_scatter, width=True)
    
    # Recent Logs
    st.subheader("Recent Query Logs")
    
    # Download Button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "Download Data as CSV",
        csv,
        "sentiment_logs.csv",
        "text/csv",
        key=f'download-csv-{int(time.time())}' # Unique key to prevent duplicate id error on refresh
    )
    
    st.dataframe(
        df[['timestamp', 'input_text', 'model_label', 'model_score']],
        width="stretch",
        hide_index=True
    )
