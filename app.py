import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide", page_title="Interactive Analytics")

# ------------------------------------------------------------
# Helper: IQR outlier removal
# ------------------------------------------------------------
def remove_outliers_iqr(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    return df[(df[column] >= lower) & (df[column] <= upper)]

# ------------------------------------------------------------
# CUSTOMER DASHBOARD
# ------------------------------------------------------------
def customer_dashboard():
    st.title("🛍️ Customer Personality Analysis")

    # ---- Load default data ----
    @st.cache_data
    def get_default_customer():
        df = pd.read_csv("marketing_campaign.csv", sep='\t')
        spend_cols = ['MntWines','MntFruits','MntMeatProducts','MntFishProducts','MntSweetProducts','MntGoldProds']
        df['TotalSpent'] = df[spend_cols].sum(axis=1)
        df['Age'] = datetime.now().year - df['Year_Birth']
        df['Spending_Segment'] = pd.qcut(df['TotalSpent'], q=4, labels=['Low','Medium','High','Premium'])
        return df

    # ---- Import custom CSV ----
    with st.expander("📁 Import custom data (optional)"):
        uploaded = st.file_uploader("Upload CSV with same structure as marketing_campaign.csv", type="csv", key="cust_upload")
        if uploaded:
            df = pd.read_csv(uploaded)
            st.success("Using uploaded data")
        else:
            df = get_default_customer()

    # ---- Sidebar Filters ----
    with st.sidebar:
        st.header("Global Filters")
        edu = st.multiselect("Education", df['Education'].unique(), default=df['Education'].unique())
        marital = st.multiselect("Marital Status", df['Marital_Status'].unique(), default=df['Marital_Status'].unique())
        income_range = st.slider("Income ($)", int(df['Income'].min()), int(df['Income'].max()), (30000,100000))
        age_range = st.slider("Age", int(df['Age'].min()), int(df['Age'].max()), (25,65))
        seg = st.multiselect("Spending Segment", df['Spending_Segment'].cat.categories, default=df['Spending_Segment'].cat.categories)

    filtered = df[(df['Education'].isin(edu)) & (df['Marital_Status'].isin(marital)) &
                  (df['Income'].between(*income_range)) & (df['Age'].between(*age_range)) &
                  (df['Spending_Segment'].isin(seg))]

    # ---- KPIs ----
    st.subheader("Key Metrics")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Customers", f"{len(filtered):,}")
    c2.metric("Avg Income", f"${filtered['Income'].mean():,.0f}")
    c3.metric("Avg Total Spent", f"${filtered['TotalSpent'].mean():,.0f}")
    c4.metric("Response Rate", f"{(filtered['Response']==1).mean()*100:.1f}%")

    # ---- Interactive Chart Builder ----
    st.subheader("🔧 Build Your Own Chart")
    with st.container():
        col1,col2,col3 = st.columns(3)
        chart_type = col1.selectbox("Chart type", ["Scatter","Bar","Box","Histogram","Line"])
        x_axis = col2.selectbox("X-axis", ['Income','Age','Recency','TotalSpent','Spending_Segment','Education','Marital_Status'])
        y_axis = col3.selectbox("Y-axis (if applicable)", ['Income','TotalSpent','Recency','Age'])

        color_var = st.selectbox("Color by", ['None','Education','Marital_Status','Spending_Segment','Response'])
        size_var = st.selectbox("Size by (scatter only)", ['None','Income','TotalSpent','Recency'])

        outlier_cb = st.checkbox("Remove outliers (IQR) on main axis")

    plot_df = filtered.copy()
    if outlier_cb:
        if x_axis in plot_df.select_dtypes(include=np.number).columns:
            plot_df = remove_outliers_iqr(plot_df, x_axis)
        if y_axis in plot_df.select_dtypes(include=np.number).columns:
            plot_df = remove_outliers_iqr(plot_df, y_axis)

    # Build figure
    fig = None
    color = None if color_var == 'None' else color_var
    size = None if size_var == 'None' else size_var

    try:
        if chart_type == "Scatter":
            fig = px.scatter(plot_df, x=x_axis, y=y_axis, color=color, size=size,
                             hover_data=['Education','Marital_Status'], opacity=0.7)
        elif chart_type == "Bar":
            agg = plot_df.groupby(x_axis)[y_axis].mean().reset_index()
            fig = px.bar(agg, x=x_axis, y=y_axis, color=color, text=y_axis)
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        elif chart_type == "Box":
            fig = px.box(plot_df, x=x_axis, y=y_axis, color=color, points="outliers")
        elif chart_type == "Histogram":
            fig = px.histogram(plot_df, x=x_axis, color=color, marginal="box")
        elif chart_type == "Line":
            agg = plot_df.groupby(x_axis)[y_axis].mean().reset_index()
            fig = px.line(agg, x=x_axis, y=y_axis, color=color, markers=True)
    except:
        st.warning("Could not create chart with this combination. Try different axes.")

    if fig:
        fig.update_layout(template="simple_white")
        st.plotly_chart(fig, use_container_width=True)

    # ---- Additional static chart ----
    st.subheader("Response Rate by Segment")
    resp = filtered.groupby('Spending_Segment')['Response'].mean().reset_index()
    fig2 = px.bar(resp, x='Spending_Segment', y='Response', text='Response',
                  labels={'Response':'Response Rate'}, color='Spending_Segment')
    fig2.update_traces(texttemplate='%{text:.1%}', textposition='outside')
    st.plotly_chart(fig2, use_container_width=True)

    # ---- Export ----
    st.download_button("📥 Download Filtered Data", filtered.to_csv(index=False), "customer_filtered.csv")

# ------------------------------------------------------------
# HOUSE SALES DASHBOARD
# ------------------------------------------------------------
def house_dashboard():
    st.title("🏡 House Sales Analysis")

    @st.cache_data
    def get_default_houses():
        df = pd.read_csv("kc_house_data.csv")
        df['date'] = pd.to_datetime(df['date'])
        df['year_month'] = df['date'].dt.to_period('M').astype(str)
        df['age'] = datetime.now().year - df['yr_built']
        df['price_per_sqft'] = df['price'] / df['sqft_living']
        return df

    # Import custom CSV
    with st.expander("📁 Import custom data (optional)"):
        uploaded = st.file_uploader("Upload CSV with same structure as kc_house_data.csv", type="csv", key="house_upload")
        if uploaded:
            df = pd.read_csv(uploaded)
            st.success("Using uploaded data")
        else:
            df = get_default_houses()

    # Sidebar filters
    with st.sidebar:
        st.header("Global Filters")
        price_r = st.slider("Price ($)", int(df['price'].min()), int(df['price'].max()), (300000,800000), 50000)
        beds = st.multiselect("Bedrooms", sorted(df['bedrooms'].unique()), default=[2,3,4])
        baths = st.slider("Bathrooms", 0.5, float(df['bathrooms'].max()), (1.0,3.0), 0.5)
        sqft_r = st.slider("Living Area (sqft)", int(df['sqft_living'].min()), int(df['sqft_living'].max()), (1000,3000))
        yr_r = st.slider("Year Built", int(df['yr_built'].min()), int(df['yr_built'].max()), (1950,2015))

    filtered = df[(df['price'].between(*price_r)) & (df['bedrooms'].isin(beds)) &
                  (df['bathrooms'].between(*baths)) & (df['sqft_living'].between(*sqft_r)) &
                  (df['yr_built'].between(*yr_r))]

    # KPIs
    st.subheader("Market Overview")
    k1,k2,k3,k4 = st.columns(4)
    k1.metric("Avg Price", f"${filtered['price'].mean():,.0f}")
    k2.metric("Median Price", f"${filtered['price'].median():,.0f}")
    k3.metric("Price / Sqft", f"${filtered['price_per_sqft'].mean():,.0f}")
    k4.metric("Listings", f"{len(filtered):,}")

    # Interactive Chart Builder
    st.subheader("🔧 Build Your Own Chart")
    with st.container():
        col1,col2,col3 = st.columns(3)
        chart_type = col1.selectbox("Chart type", ["Scatter","Bar","Box","Histogram","Line"])
        x_axis = col2.selectbox("X-axis", ['price','sqft_living','bedrooms','bathrooms','floors','waterfront','condition','grade','yr_built','age','price_per_sqft'])
        y_axis = col3.selectbox("Y-axis", ['price','sqft_living','sqft_lot','bedrooms','bathrooms','price_per_sqft','age'])

        color_var = st.selectbox("Color by", ['None','bedrooms','bathrooms','floors','waterfront','condition','grade','view'])
        size_var = st.selectbox("Size by (scatter only)", ['None','sqft_living','sqft_lot','price','bedrooms'])

        outlier_cb = st.checkbox("Remove outliers (IQR) on main axis")

    plot_df = filtered.copy()
    if outlier_cb:
        if x_axis in plot_df.select_dtypes(include=np.number).columns:
            plot_df = remove_outliers_iqr(plot_df, x_axis)
        if y_axis in plot_df.select_dtypes(include=np.number).columns:
            plot_df = remove_outliers_iqr(plot_df, y_axis)

    fig = None
    color = None if color_var == 'None' else color_var
    size = None if size_var == 'None' else size_var

    try:
        if chart_type == "Scatter":
            fig = px.scatter(plot_df, x=x_axis, y=y_axis, color=color, size=size,
                             hover_data=['bedrooms','bathrooms','waterfront'], opacity=0.7)
        elif chart_type == "Bar":
            agg = plot_df.groupby(x_axis)[y_axis].mean().reset_index()
            fig = px.bar(agg, x=x_axis, y=y_axis, color=color, text=y_axis)
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        elif chart_type == "Box":
            fig = px.box(plot_df, x=x_axis, y=y_axis, color=color, points="outliers")
        elif chart_type == "Histogram":
            fig = px.histogram(plot_df, x=x_axis, color=color, marginal="box")
        elif chart_type == "Line":
            agg = plot_df.groupby(x_axis)[y_axis].mean().reset_index()
            fig = px.line(agg, x=x_axis, y=y_axis, color=color, markers=True)
    except:
        st.warning("Could not create chart. Try different axes.")

    if fig:
        fig.update_layout(template="simple_white")
        st.plotly_chart(fig, use_container_width=True)

    # Map (static)
    if 'lat' in filtered.columns and 'long' in filtered.columns:
        st.subheader("🗺️ Property Locations")
        map_data = filtered.dropna(subset=['lat','long']).sample(min(2000, len(filtered)))
        st.map(map_data[['lat','long']])

    # Export
    st.download_button("📥 Download Filtered Data", filtered.to_csv(index=False), "houses_filtered.csv")

# ------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------
def main():
    st.sidebar.title("📊 Analytics Hub")
    page = st.sidebar.radio("Select Dashboard", ["🛍️ Customer Personality", "🏡 House Sales"])
    if page == "🛍️ Customer Personality":
        customer_dashboard()
    else:
        house_dashboard()

if __name__ == "__main__":
    main()
