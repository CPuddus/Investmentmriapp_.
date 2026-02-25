import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# =============================
# ESAOTE BRAND STYLE
# =============================


ESAOTE_GREEN = "#6CC24A"

# =============================
# ESAOTE LOGO + HEADER
# =============================

col1, col2 = st.columns([1, 5])

with col1:
    st.image(
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTso1Ip1hX3Ji8xSyaQGMKfVBEuea5_IWuDkw&s",
        width=500
    )

with col2:
    st.markdown(
        "<h1 style='margin-bottom:0;'>Esaote MRI – Return on Investment Simulator</h1>",
        unsafe_allow_html=True
    )

st.markdown("### Investment Parameters")

years = st.slider("Analysis Period (Years)", 1, 15, 10)

# =============================
# COST SECTION
# =============================

st.markdown("#### Capital & Operational Costs")

initial_investment = st.number_input("Initial Investment (€)", min_value=0, value=500000, step=10000)
technology_reporting_cost = st.number_input("Technology & Reporting Cost (Yearly)", min_value=0, value=50000, step=5000)
electricity_cost = st.number_input("Electricity Cost (Yearly)", min_value=0, value=20000, step=2000)
maintenance_cost = st.number_input("Annual Service & Maintenance Cost (€)", min_value=0, value=20000, step=5000)

# =============================
# REVENUE SECTION
# =============================

st.markdown("#### Revenue Assumptions")

exams_per_day = st.slider("Examinations per Day", 1, 25, 12)
working_days = st.slider("Working Days per Year", 1, 365, 200)
average_price = st.slider("Average Exam Price (€)", 1, 1000, 200)

annual_revenue = exams_per_day * average_price * working_days

# =============================
# CALCULATIONS
# =============================

expenses = [initial_investment]
revenues = [0]

tech_cost_cumulative = 0
electricity_cost_cumulative = 0
maintenance_cumulative = 0
income_cumulative = 0

for year in range(1, years + 1):
    tech_cost_cumulative += technology_reporting_cost
    electricity_cost_cumulative += electricity_cost
    maintenance_cumulative += maintenance_cost
    income_cumulative += annual_revenue
    
    total_expenses = (
        initial_investment +
        tech_cost_cumulative +
        electricity_cost_cumulative +
        maintenance_cumulative
    )
    
    expenses.append(total_expenses)
    revenues.append(income_cumulative)

df = pd.DataFrame({
    "Year": range(0, years + 1),
    "Expenses": expenses,
    "Revenues": revenues
})

df["Profit"] = df["Revenues"] - df["Expenses"]

# =============================
# BREAK EVEN CALCULATION
# =============================

break_even_year = None
for i in range(1, len(df)):
    if df["Profit"][i] >= 0:
        break_even_year = df["Year"][i]
        break

st.markdown("## Financial Performance Overview")

# =============================
# CHART
# =============================

df_melted = df.melt(
    id_vars="Year",
    value_vars=["Expenses", "Revenues"],
    var_name="Category",
    value_name="Value"
)

bars = alt.Chart(df_melted).mark_bar(
    opacity=0.3,
    size=40
).encode(
    x=alt.X("Year:O", title="Year"),
    y=alt.Y("Value:Q", title="Euro (€)"),
    color=alt.Color(
        "Category:N",
        scale=alt.Scale(
            domain=["Expenses", "Revenues"],
            range=['red', ESAOTE_GREEN]
        ),
        legend=alt.Legend(title="")
    ),
    xOffset="Category:N"
)

lines = alt.Chart(df_melted).mark_line(strokeWidth=4).encode(
    x="Year:O",
    y="Value:Q",
    color=alt.Color(
        "Category:N",
        scale=alt.Scale(
            domain=["Expenses", "Revenues"],
            range=['red', ESAOTE_GREEN]
        ),
        legend=None
    )
)

)

# =============================
# BREAK EVEN MESSAGE
# =============================

if break_even_year is not None:
    st.success(f"Break-even achieved in Year {break_even_year}")
else:
    st.warning("Break-even not reached within selected period")
