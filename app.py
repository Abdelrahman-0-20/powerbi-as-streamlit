import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Interactive Dashboards")
st.title("📊 Interactive Power BI → Streamlit Dashboards")

# ------------------------------------------------------------
# CACHED DATA LOADERS (for speed)
# ------------------------------------------------------------
@st.cache_data
def load_olympics():
    df = pd.read_csv("athlete_events.csv")
    # Convert year to integer if needed
    df['Year'] = df['Year'].astype(int)
    return df

@st.cache_data
def load_customer():
    # marketing_campaign.csv is tab-separated
    df = pd.read_csv("marketing_campaign.csv", sep='\t')
    # Create total spending column if it doesn't exist
    spending_cols = ['MntWines', 'MntFruits', 'MntMeatProducts', 'MntFishProducts', 
                     'MntSweetProducts', 'MntGoldProds']
    df['TotalSpent'] = df[spending_cols].sum(axis=1)
    # Income column might be missing - compute from total spending if needed
    if 'Income' not in df.columns:
        # Many versions have 'Income' already; if not, approximate
        df['Income'] = df['TotalSpent'] * 3  # dummy fallback
    return df

@st.cache_data
def load_houses():
    df = pd.read_csv("kc_house_data.csv")
    # Convert date if needed
    df['date'] = pd.to_datetime(df['date'])
    return df

# ------------------------------------------------------------
# OLYMPICS DASHBOARD
# ------------------------------------------------------------
def olympics_dashboard():
    st.header("🏅 120 Years of Olympic History")
    df = load_olympics()

    # Sidebar filters
    st.sidebar.markdown("## Olympics Filters")
    sports = st.sidebar.multiselect("Sport", df['Sport'].unique(), default=df['Sport'].unique()[:5])
    sexes = st.sidebar.multiselect("Sex", df['Sex'].unique(), default=df['Sex'].unique())
    years = st.sidebar.slider("Year range", int(df['Year'].min()), int(df['Year'].max()), (1960, 2016))
    seasons = st.sidebar.multiselect("Season", df['Season'].unique(), default=df['Season'].unique())

    # Filter data
    filtered = df[
        (df['Sport'].isin(sports)) &
        (df['Sex'].isin(sexes)) &
        (df['Year'].between(years[0], years[1])) &
        (df['Season'].isin(seasons))
    ]

    col1, col2 = st.columns(2)

    with col1:
        medals_country = filtered[filtered['Medal'].notna()].groupby('NOC')['Medal'].count().reset_index(name='Total Medals')
        medals_country = medals_country.sort_values('Total Medals', ascending=False).head(10)
        fig1 = px.bar(medals_country, x='NOC', y='Total Medals', title="Top 10 Countries by Medals")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        athlete_medals = filtered[filtered['Medal'].notna()].groupby('Name')['Medal'].count().reset_index(name='Medals')
        athlete_medals = athlete_medals.sort_values('Medals', ascending=False).head(10)
        fig2 = px.bar(athlete_medals, x='Medals', y='Name', orientation='h', title="Top Athletes by Medals")
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        athletes_per_year = filtered.groupby('Year')['ID'].nunique().reset_index(name='Athletes')
        fig3 = px.line(athletes_per_year, x='Year', y='Athletes', title="Athletes Over Time")
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        sport_medals = filtered[filtered['Medal'].notna()].groupby('Sport')['Medal'].count().reset_index(name='Medals')
        sport_medals = sport_medals.sort_values('Medals', ascending=False).head(10)
        fig4 = px.bar(sport_medals, x='Sport', y='Medals', title="Top 10 Sports by Medals")
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("📏 Height vs Weight Correlation")
    scatter_df = filtered.dropna(subset=['Height', 'Weight'])
    if not scatter_df.empty:
        fig5 = px.scatter(scatter_df, x='Height', y='Weight', color='Sex', opacity=0.6,
                          title="Height vs Weight (colored by Sex)")
        st.plotly_chart(fig5, use_container_width=True)
    else:
        st.info("No data available for height/weight scatter plot with current filters.")

    col5, col6, col7 = st.columns(3)
    with col5:
        age_df = filtered.dropna(subset=['Age'])
        if not age_df.empty:
            fig_age = px.histogram(age_df, x='Age', nbins=30, title="Athletes by Age")
            st.plotly_chart(fig_age, use_container_width=True)
    with col6:
        height_df = filtered.dropna(subset=['Height'])
        if not height_df.empty:
            fig_height = px.histogram(height_df, x='Height', nbins=30, title="Athletes by Height")
            st.plotly_chart(fig_height, use_container_width=True)
    with col7:
        weight_df = filtered.dropna(subset=['Weight'])
        if not weight_df.empty:
            fig_weight = px.histogram(weight_df, x='Weight', nbins=30, title="Athletes by Weight")
            st.plotly_chart(fig_weight, use_container_width=True)

# ------------------------------------------------------------
# CUSTOMER PERSONALITY DASHBOARD
# ------------------------------------------------------------
def customer_dashboard():
    st.header("🛍️ Customer Personality Analysis")
    df = load_customer()

    # Filter by education
    edu_options = st.multiselect("Select Education Level", df['Education'].unique(), default=df['Education'].unique())
    filtered = df[df['Education'].isin(edu_options)]

    # Average Income by Education
    income_edu = filtered.groupby('Education')['Income'].mean().reset_index()
    fig1 = px.bar(income_edu, x='Education', y='Income', title="Average Income by Education Level")
    st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        # Total Spending vs Income
        fig2 = px.scatter(filtered, x='Income', y='TotalSpent', color='Education', 
                          title="Total Spending vs Income", opacity=0.6)
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        # Complaints vs Income (if 'Complain' column exists)
        if 'Complain' in filtered.columns:
            complain_income = filtered.groupby('Complain')['Income'].mean().reset_index()
            fig3 = px.bar(complain_income, x='Complain', y='Income', 
                          title="Average Income by Complaint Status")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Column 'Complain' not found – skipping complaint chart.")

    # Additional: spending by product category
    st.subheader("Spending Breakdown by Education")
    spending_cols = ['MntWines', 'MntFruits', 'MntMeatProducts', 'MntFishProducts', 
                     'MntSweetProducts', 'MntGoldProds']
    # Melt for grouped bar
    melted = filtered.melt(id_vars=['Education'], value_vars=spending_cols, 
                           var_name='Product', value_name='Amount')
    spend_by_edu = melted.groupby(['Education', 'Product'])['Amount'].mean().reset_index()
    fig4 = px.bar(spend_by_edu, x='Education', y='Amount', color='Product', 
                  title="Average Spending by Product Category", barmode='group')
    st.plotly_chart(fig4, use_container_width=True)

# ------------------------------------------------------------
# HOUSE SALES DASHBOARD
# ------------------------------------------------------------
def house_dashboard():
    st.header("🏡 House Sales in USA (King County)")
    df = load_houses()

    # Filters
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        price_range = st.slider("Select Price Range ($)", 
                                int(df['price'].min()), int(df['price'].max()), 
                                (300000, 800000), step=50000)
    with col_filter2:
        bedrooms = st.multiselect("Number of Bedrooms", 
                                  sorted(df['bedrooms'].unique()), 
                                  default=[2,3,4])

    filtered = df[
        (df['price'] >= price_range[0]) & 
        (df['price'] <= price_range[1]) &
        (df['bedrooms'].isin(bedrooms))
    ]

    col1, col2 = st.columns(2)
    with col1:
        # Price distribution histogram
        fig1 = px.histogram(filtered, x='price', nbins=50, title="Distribution of House Prices",
                            labels={'price': 'Price ($)'})
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        # Average price by bedrooms
        avg_price_bed = filtered.groupby('bedrooms')['price'].mean().reset_index()
        fig2 = px.bar(avg_price_bed, x='bedrooms', y='price', 
                      title="Average Price by Number of Bedrooms")
        st.plotly_chart(fig2, use_container_width=True)

    # Price over time (by date)
    if 'date' in filtered.columns:
        st.subheader("Price Trend Over Time")
        filtered['year_month'] = filtered['date'].dt.to_period('M').astype(str)
        price_trend = filtered.groupby('year_month')['price'].mean().reset_index()
        fig3 = px.line(price_trend, x='year_month', y='price', 
                       title="Average House Price Over Time")
        st.plotly_chart(fig3, use_container_width=True)

    # Map view
    if 'lat' in filtered.columns and 'long' in filtered.columns:
        st.subheader("🏠 Geographic Distribution")
        map_df = filtered.dropna(subset=['lat', 'long']).sample(min(1000, len(filtered)))
        st.map(map_df[['lat', 'long']])

    # Additional: price vs sqft living
    st.subheader("Price vs. Living Area (sqft)")
    fig4 = px.scatter(filtered, x='sqft_living', y='price', opacity=0.5,
                      title="Price vs. Square Foot Living Area",
                      labels={'sqft_living': 'Living Area (sqft)', 'price': 'Price ($)'})
    st.plotly_chart(fig4, use_container_width=True)

# ------------------------------------------------------------
# MAIN APP WITH TABS
# ------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🏅 Olympics History", "🛍️ Customer Personality", "🏡 House Sales"])

with tab1:
    olympics_dashboard()
with tab2:
    customer_dashboard()
with tab3:
    house_dashboard()