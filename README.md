# 📊 Power BI Style Dashboards in Streamlit

A practice project building interactive dashboards with **Streamlit** and **Plotly** that mimic Power BI functionality. No Power BI license required!

Currently features two analytical views:
- 🛍️ **Customer Personality Analysis** – explore customer demographics, spending habits, and campaign response.
- 🏡 **House Sales Analysis** – investigate real estate trends, pricing, and property characteristics.

## ✨ Features

- **Interactive Chart Builder** – choose chart type (scatter, bar, box, histogram, line), X/Y axes, color, and size.
- **Dynamic Filters** – slice data by education, income, age, bedrooms, price range, etc.
- **Outlier Removal** – toggle IQR‑based outlier filtering for cleaner visuals.
- **Import/Export** – upload your own CSV or download filtered data as CSV.
- **KPI Metrics** – quick summary statistics at the top of each dashboard.
- **Minimalist Design** – clean, straightforward UI focused on data exploration.

## 📁 Data Sources

The app expects two CSV files in the same directory. You can also import your own files with the same column structure.

1. `marketing_campaign.csv` – tab‑separated customer data (from [Kaggle](https://www.kaggle.com/datasets/rodsaldanha/arketing-campaign))
2. `kc_house_data.csv` – King County house sales (from [Kaggle](https://www.kaggle.com/datasets/harlfoxem/housesalesprediction))


- pip

### Installation
