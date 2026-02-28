import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# =============================
# ESAOTE BRAND STYLE
# =============================

ESAOTE_GREEN = "#6CC24A"

# =============================
# HEADER
# =============================

col1, col2 = st.columns([1, 5])

with col1:
    st.image(
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTso1Ip1hX3Ji8xSyaQGMKfVBEuea5_IWuDkw&s",
        width=180
    )

with col2:
    st.markdown(
        "<h1 style='margin-bottom:0;'>Esaote MRI – Return on Investment Simulator</h1>",
        unsafe_allow_html=True
    )

# =============================
# CURRENCY SELECTION
# =============================

st.markdown("### Currency Selection")

currency_options = {
    "EUR (€)": {"rate": 1.0, "symbol": "€"},
    "USD ($)": {"rate": 1.08, "symbol": "$"},
    "GBP (£)": {"rate": 0.85, "symbol": "£"},
    "CHF (CHF)": {"rate": 0.95, "symbol": "CHF"}
}

selected_currency = st.selectbox(
    "Select Currency",
    list(currency_options.keys())
)

exchange_rate = currency_options[selected_currency]["rate"]
currency_symbol = currency_options[selected_currency]["symbol"]

# =============================
# INVESTMENT PARAMETERS
# =============================

st.markdown("### Investment Parameters")
years = st.slider("Analysis Period (Years)", 1, 15, 10)

# =============================
# COST SECTION
# =============================

st.markdown("#### Capital & Operational Costs")

initial_investment = st.number_input("Initial Investment", min_value=0, value=500000, step=10000)
technology_reporting_cost = st.number_input("Technology & Reporting Cost (Yearly)", min_value=0, value=50000, step=5000)
electricity_cost = st.number_input("Electricity Cost (Yearly)", min_value=0, value=20000, step=2000)
maintenance_cost = st.number_input("Annual Service & Maintenance Cost", min_value=0, value=20000, step=5000)

# Conversion to selected currency
initial_investment *= exchange_rate
technology_reporting_cost *= exchange_rate
electricity_cost *= exchange_rate
maintenance_cost *= exchange_rate

# =============================
# REVENUE SECTION
# =============================

st.markdown("#### Revenue Assumptions")

exams_per_day = st.slider("Examinations per Day", 1, 25, 12)
working_days = st.slider("Working Days per Year", 1, 365, 200)
average_price = st.slider("Average Exam Price", 1, 1000, 200)

annual_revenue = exams_per_day * average_price * working_days * exchange_rate

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
# ROI CALCULATION
# =============================

final_profit = df["Profit"].iloc[-1]
roi = (final_profit / initial_investment) * 100 if initial_investment > 0 else 0

# =============================
# BREAK EVEN CALCULATION
# =============================

break_even_year = None
for i in range(1, len(df)):
    if df["Profit"][i] >= 0:
        break_even_year = df["Year"][i]
        break

# =============================
# METRICS DISPLAY
# =============================

st.markdown("## Financial Performance Overview")

colA, colB, colC = st.columns(3)

colA.metric("Total Revenue", f"{currency_symbol}{df['Revenues'].iloc[-1]:,.0f}")
colB.metric("Total Profit", f"{currency_symbol}{final_profit:,.0f}")
colC.metric("ROI (%)", f"{roi:.1f}%")

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
    y=alt.Y("Value:Q", title=f"Value ({currency_symbol})"),
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

break_even_line = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(
    strokeDash=[5,5],
    color="black"
).encode(y="y:Q")

final_chart = bars + lines + break_even_line

st.altair_chart(
    final_chart.properties(
        width=1500,
        height=500,
        title="Esaote MRI Investment Performance"
    ),
    use_container_width=True
)

# =============================
# BREAK EVEN MESSAGE
# =============================

if break_even_year is not None:
    st.success(f"Break-even achieved in Year {break_even_year}")
else:
    st.warning("Break-even not reached within selected period")
