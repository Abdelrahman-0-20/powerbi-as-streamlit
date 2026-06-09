import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(layout="wide", page_title="Analytics Dashboard", page_icon="📊", initial_sidebar_state="expanded")

# ------------------------------------------------------------
# CACHED DATA LOADERS
# ------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_customer():
    try:
        df = pd.read_csv("marketing_campaign.csv", sep='\t')
        spending_cols = ['MntWines', 'MntFruits', 'MntMeatProducts',
                        'MntFishProducts', 'MntSweetProducts', 'MntGoldProds']
        df['TotalSpent'] = df[spending_cols].sum(axis=1)
        if 'Year_Birth' in df.columns:
            df['Age'] = datetime.now().year - df['Year_Birth']
        df['CLV_Score'] = df['TotalSpent'] * (df['Recency'].max() - df['Recency']) / df['Recency'].max()
        df['Spending_Segment'] = pd.qcut(df['TotalSpent'], q=4, labels=['Low', 'Medium', 'High', 'Premium'])
        df['Spending_Ratio'] = (df['TotalSpent'] / df['Income'] * 100).clip(0, 100)
        df['Age_Group'] = pd.cut(df['Age'], bins=[18,30,40,50,60,100], labels=['18-30','31-40','41-50','51-60','60+'])
        return df
    except Exception as e:
        st.error(f"Error loading customer data: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def load_houses():
    try:
        df = pd.read_csv("kc_house_data.csv")
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['year_month'] = df['date'].dt.to_period('M').astype(str)
        df['age'] = datetime.now().year - df['yr_built']
        df['renovated'] = df['yr_renovated'] > 0
        df['price_per_sqft'] = df['price'] / df['sqft_living']
        df['price_category'] = pd.qcut(df['price'], q=5, labels=['Budget', 'Economic', 'Mid-Range', 'Premium', 'Luxury'])
        df['total_rooms'] = df['bedrooms'] + df['bathrooms']
        return df
    except Exception as e:
        st.error(f"Error loading house data: {e}")
        return pd.DataFrame()

# ------------------------------------------------------------
# CUSTOMER DASHBOARD
# ------------------------------------------------------------
def customer_dashboard():
    st.title("🛍️ Customer Personality Analysis")
    df = load_customer()
    if df.empty:
        return

    # Filters
    with st.expander("🔍 Filters", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            education = st.multiselect("Education", df['Education'].unique(), default=df['Education'].unique())
        with col2:
            marital = st.multiselect("Marital Status", df['Marital_Status'].unique(), default=df['Marital_Status'].unique())
        with col3:
            income_range = st.slider("Income Range ($)", int(df['Income'].min()), int(df['Income'].max()), (30000, 100000), step=10000)
        with col4:
            spending_segment = st.multiselect("Spending Segment", df['Spending_Segment'].unique(), default=df['Spending_Segment'].unique())
        col1, col2, _ = st.columns(3)
        with col1:
            age_range = st.slider("Age Range", int(df['Age'].min()), int(df['Age'].max()), (25, 65))
        with col2:
            if 'Kidhome' in df.columns:
                kids = st.multiselect("Kids at Home", df['Kidhome'].unique(), default=df['Kidhome'].unique())
            else:
                kids = [0,1,2]

    filtered = df[(df['Education'].isin(education)) & (df['Marital_Status'].isin(marital)) &
                  (df['Income'].between(income_range[0], income_range[1])) & (df['Spending_Segment'].isin(spending_segment))]
    if 'Age' in filtered.columns:
        filtered = filtered[filtered['Age'].between(age_range[0], age_range[1])]
    if 'Kidhome' in filtered.columns:
        filtered = filtered[filtered['Kidhome'].isin(kids)]

    # KPIs
    st.subheader("Key Metrics")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Avg Income", f"${filtered['Income'].mean():,.0f}")
    m2.metric("Avg Total Spending", f"${filtered['TotalSpent'].mean():,.0f}")
    m3.metric("Avg Days Since Purchase", f"{filtered['Recency'].mean():.0f} days")
    m4.metric("Campaign Response Rate", f"{(filtered['Response']==1).mean()*100:.1f}%")
    m5.metric("Active Customers", f"{len(filtered):,}")

    # Charts (at least 8)
    # 1. Income vs Spending scatter
    st.subheader("1. Income vs Total Spending")
    fig1 = px.scatter(filtered, x='Income', y='TotalSpent', color='Education',
                      size='Recency', hover_data=['Age','Marital_Status'],
                      title="Income vs Total Spending", opacity=0.7)
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        # 2. Average spending by product category (horizontal bar)
        st.subheader("2. Spending by Product Category")
        spending_cols = ['MntWines','MntFruits','MntMeatProducts','MntFishProducts','MntSweetProducts','MntGoldProds']
        spend_avg = filtered[spending_cols].mean().sort_values()
        fig2 = px.bar(x=spend_avg.values, y=spend_avg.index, orientation='h',
                      labels={'x':'Avg Amount ($)','y':'Category'}, text=spend_avg.values.round(0))
        fig2.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        # 3. Donut – Marital Status
        st.subheader("3. Marital Status Distribution")
        marital_counts = filtered['Marital_Status'].value_counts()
        fig3 = px.pie(values=marital_counts.values, names=marital_counts.index, hole=0.4,
                      title="Marital Status")
        st.plotly_chart(fig3, use_container_width=True)

    # 4. CLV by Segment (dual axis)
    st.subheader("4. Customer Lifetime Value by Segment")
    clv_seg = filtered.groupby('Spending_Segment').agg(CLV=('CLV_Score','mean'), Count=('ID','count')).reset_index()
    fig4 = make_subplots(specs=[[{"secondary_y": True}]])
    fig4.add_trace(go.Bar(name="Count", x=clv_seg['Spending_Segment'], y=clv_seg['Count']), secondary_y=False)
    fig4.add_trace(go.Scatter(name="Avg CLV", x=clv_seg['Spending_Segment'], y=clv_seg['CLV'],
                              mode='lines+markers+text', text=clv_seg['CLV'].round(0), textposition='top center'), secondary_y=True)
    fig4.update_layout(title="CLV by Spending Segment")
    st.plotly_chart(fig4, use_container_width=True)

    # 5. Income box plot by Education
    st.subheader("5. Income Distribution by Education")
    fig5 = px.box(filtered, y='Income', x='Education', color='Education', points="outliers",
                  title="Income by Education Level")
    st.plotly_chart(fig5, use_container_width=True)

    # 6. Line chart – Average spending by Age Group
    st.subheader("6. Average Spending by Age Group")
    age_spend = filtered.groupby('Age_Group')['TotalSpent'].mean().reset_index()
    fig6 = px.line(age_spend, x='Age_Group', y='TotalSpent', markers=True,
                   title="Spending by Age Group", line_shape='spline')
    st.plotly_chart(fig6, use_container_width=True)

    # 7. Recency vs Total Spending by Response
    st.subheader("7. Recency vs Total Spending (Response)")
    if 'Response' in filtered.columns:
        fig7 = px.scatter(filtered, x='Recency', y='TotalSpent', color='Response',
                          title="Recency vs Total Spending", opacity=0.6,
                          color_discrete_map={0:'grey',1:'green'})
        st.plotly_chart(fig7, use_container_width=True)
    else:
        st.info("No response column available")

    # 8. Stacked bar – Campaign response by segment
    if 'Response' in filtered.columns:
        st.subheader("8. Campaign Response by Spending Segment")
        resp_seg = filtered.groupby(['Spending_Segment','Response']).size().unstack(fill_value=0)
        fig8 = go.Figure(data=[
            go.Bar(name='No Response', x=resp_seg.index, y=resp_seg.get(0,0), marker_color='lightcoral'),
            go.Bar(name='Responded', x=resp_seg.index, y=resp_seg.get(1,0), marker_color='lightgreen')
        ])
        fig8.update_layout(barmode='stack', title="Campaign Response by Segment")
        st.plotly_chart(fig8, use_container_width=True)

    # 9. Correlation Heatmap
    st.subheader("9. Feature Correlations")
    num_cols = filtered.select_dtypes(include=[np.number]).columns[:10]
    if len(num_cols) > 1:
        corr = filtered[num_cols].corr()
        fig_corr = go.Figure(data=go.Heatmap(z=corr.values, x=list(corr.columns), y=list(corr.index),
                                             text=corr.round(2).values, texttemplate='%{text}',
                                             colorscale='RdBu', zmid=0))
        fig_corr.update_layout(title="Correlation Heatmap", height=600)
        st.plotly_chart(fig_corr, use_container_width=True)

    # Download
    st.download_button("Download Filtered Data", filtered.to_csv(index=False), "customer_analysis.csv")

# ------------------------------------------------------------
# HOUSE SALES DASHBOARD
# ------------------------------------------------------------
def house_dashboard():
    st.title("🏡 House Sales Analysis")
    df = load_houses()
    if df.empty:
        return

    # Filters
    with st.expander("🔍 Filters", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            price_range = st.slider("Price Range ($)", int(df['price'].min()), int(df['price'].max()), (300000,800000), step=50000)
        with c2:
            bedrooms = st.multiselect("Bedrooms", sorted(df['bedrooms'].unique()), default=[2,3,4])
        with c3:
            bathrooms = st.slider("Bathrooms", float(df['bathrooms'].min()), float(df['bathrooms'].max()), (1.0,3.0), 0.5)
        c1, c2, c3 = st.columns(3)
        with c1:
            sqft_range = st.slider("Living Area (sqft)", int(df['sqft_living'].min()), int(df['sqft_living'].max()), (1000,3000), 500)
        with c2:
            condition = st.multiselect("Condition", sorted(df['condition'].unique()), default=sorted(df['condition'].unique()))
        with c3:
            year_built = st.slider("Year Built", int(df['yr_built'].min()), int(df['yr_built'].max()), (1950,2015))
        c1, c2, _ = st.columns(3)
        with c1:
            waterfront = st.checkbox("Waterfront Only")
        with c2:
            renovated = st.checkbox("Renovated Only")

    filtered = df[(df['price'].between(*price_range)) & (df['bedrooms'].isin(bedrooms)) &
                  (df['bathrooms'].between(*bathrooms)) & (df['sqft_living'].between(*sqft_range)) &
                  (df['condition'].isin(condition)) & (df['yr_built'].between(*year_built))]
    if waterfront:
        filtered = filtered[filtered['waterfront']==1]
    if renovated:
        filtered = filtered[filtered['renovated']==True]

    # KPIs
    st.subheader("Market Overview")
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Avg Price", f"${filtered['price'].mean():,.0f}")
    k2.metric("Median Price", f"${filtered['price'].median():,.0f}")
    k3.metric("Price per Sqft", f"${filtered['price_per_sqft'].mean():,.0f}")
    k4.metric("Listings", f"{len(filtered):,}")
    k5.metric("Avg Living Area", f"{filtered['sqft_living'].mean():,.0f} sqft")
    k6.metric("Waterfront", f"{filtered['waterfront'].sum():,.0f}")

    # Charts (at least 8 + map)
    # 1. Price distribution
    st.subheader("1. Price Distribution")
    fig1 = px.histogram(filtered, x='price', nbins=50, title="Price Distribution", marginal='box')
    median = filtered['price'].median()
    fig1.add_vline(x=median, line_dash="dash", line_color="red", annotation_text=f"Median: ${median:,.0f}")
    st.plotly_chart(fig1, use_container_width=True)

    # 2. Price by bedrooms
    st.subheader("2. Price by Number of Bedrooms")
    fig2 = px.box(filtered, x='bedrooms', y='price', title="Price by Bedrooms", color='bedrooms', points="outliers")
    st.plotly_chart(fig2, use_container_width=True)

    # 3. Price trends over time (dual-axis)
    st.subheader("3. Price Trends & Sales Volume")
    monthly = filtered.groupby('year_month').agg(avg_price=('price','mean'), count=('price','count')).reset_index()
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(go.Scatter(x=monthly['year_month'], y=monthly['avg_price'], name="Avg Price", line=dict(width=2)), secondary_y=False)
    fig3.add_trace(go.Bar(x=monthly['year_month'], y=monthly['count'], name="Sales Volume", opacity=0.4), secondary_y=True)
    fig3.update_layout(title="Price & Volume Over Time", hovermode='x unified')
    fig3.update_xaxes(title="Month")
    fig3.update_yaxes(title="Price ($)", secondary_y=False)
    fig3.update_yaxes(title="Count", secondary_y=True)
    st.plotly_chart(fig3, use_container_width=True)

    # 4. Price vs Living Area
    st.subheader("4. Price vs Living Area")
    fig4 = px.scatter(filtered, x='sqft_living', y='price', color='condition', size='sqft_lot',
                      hover_data=['bedrooms','bathrooms','waterfront'], title="Price vs Living Area", opacity=0.6)
    st.plotly_chart(fig4, use_container_width=True)

    # 5. Feature correlation bar
    st.subheader("5. Feature Correlation with Price")
    corr_data = df[['price','sqft_living','sqft_lot','bedrooms','bathrooms','floors','waterfront','view','condition','grade','sqft_above','sqft_basement','age']].corr()['price'].drop('price').sort_values()
    fig5 = px.bar(x=corr_data.values, y=corr_data.index, orientation='h',
                  title="Correlation with Price", text=corr_data.values.round(2))
    fig5.update_traces(textposition='outside')
    st.plotly_chart(fig5, use_container_width=True)

    # 6. Donut – Condition
    st.subheader("6. Condition Distribution")
    cond = filtered['condition'].value_counts().sort_index()
    fig6 = px.pie(values=cond.values, names=cond.index, hole=0.4, title="Property Condition")
    st.plotly_chart(fig6, use_container_width=True)

    # 7. Donut – Grade
    st.subheader("7. Grade Distribution")
    grade = filtered['grade'].value_counts().sort_index()
    fig7 = px.pie(values=grade.values, names=grade.index, hole=0.4, title="Property Grade")
    st.plotly_chart(fig7, use_container_width=True)

    # 8. Line – Average price by year built
    st.subheader("8. Average Price by Year Built")
    year_price = filtered.groupby('yr_built')['price'].mean().reset_index()
    fig8 = px.line(year_price, x='yr_built', y='price', title="Price by Year Built", markers=True)
    st.plotly_chart(fig8, use_container_width=True)

    # 9. Price per sqft by floors
    st.subheader("9. Price per Sqft by Number of Floors")
    fig9 = px.box(filtered, x='floors', y='price_per_sqft', title="Price per Sqft by Floors", color='floors', points="outliers")
    st.plotly_chart(fig9, use_container_width=True)

    # Map
    if 'lat' in filtered.columns and 'long' in filtered.columns:
        st.subheader("10. Geographic Distribution")
        map_df = filtered.dropna(subset=['lat','long']).sample(min(2000, len(filtered)))
        st.map(map_df, latitude='lat', longitude='long')

    # Download
    st.download_button("Download Filtered Data", filtered.to_csv(index=False), "house_market_data.csv")

# ------------------------------------------------------------
# MAIN APP WITH TABS
# ------------------------------------------------------------
def main():
    st.sidebar.title("Navigation")
    dashboard = st.sidebar.radio("Select Dashboard", ["🛍️ Customer Analytics", "🏡 House Sales"])
    st.sidebar.markdown("---")
    st.sidebar.info("Interactive dashboards for customer & house data.")
    if dashboard == "🛍️ Customer Analytics":
        customer_dashboard()
    else:
        house_dashboard()

if __name__ == "__main__":
    main()
