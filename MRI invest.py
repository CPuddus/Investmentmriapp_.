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

selected_currency = st.selectbox("Select Currency", list(currency_options.keys()))

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

# Conversione valuta
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

tech_cum = 0
elec_cum = 0
maint_cum = 0
rev_cum = 0

for year in range(1, years + 1):
    tech_cum += technology_reporting_cost
    elec_cum += electricity_cost
    maint_cum += maintenance_cost
    rev_cum += annual_revenue

    total_exp = initial_investment + tech_cum + elec_cum + maint_cum

    expenses.append(total_exp)
    revenues.append(rev_cum)

df = pd.DataFrame({
    "Year": range(0, years + 1),
    "Expenses": expenses,
    "Revenues": revenues
})

df["Profit"] = df["Revenues"] - df["Expenses"]

final_profit = df["Profit"].iloc[-1]
roi = (final_profit / initial_investment) * 100 if initial_investment > 0 else 0

# Break-even
break_even_year = None
for i in range(1, len(df)):
    if df["Profit"].iloc[i] >= 0:
        break_even_year = df["Year"].iloc[i]
        break

# =============================
# METRICS
# =============================

st.markdown("## Financial Overview")

colA, colB, colC = st.columns(3)
colA.metric("Total Revenue", f"{currency_symbol}{df['Revenues'].iloc[-1]:,.0f}")
colB.metric("Net Profit", f"{currency_symbol}{final_profit:,.0f}")
colC.metric("ROI (%)", f"{roi:.1f}%")

# =============================
# LINE CHART (CUMULATIVE)
# =============================

st.markdown("### Cumulative Performance")

line_chart = alt.Chart(df).transform_fold(
    ["Expenses", "Revenues"],
    as_=["Category", "Value"]
).mark_line(strokeWidth=4).encode(
    x="Year:O",
    y=alt.Y("Value:Q", title=f"Value ({currency_symbol})"),
    color=alt.Color(
        "Category:N",
        scale=alt.Scale(
            domain=["Expenses", "Revenues"],
            range=["red", ESAOTE_GREEN]
        )
    )
)

st.altair_chart(line_chart.properties(height=400), use_container_width=True)

# =============================
# SALES INTERNATIONAL – CASH FLOW CURVE
# =============================
st.markdown("## Investment Performance Overview")

# Cumulative cash flow (già calcolato)
cashflow = []
for y in range(0, years + 1):
    if y == 0:
        cashflow.append(-initial_investment)
    else:
        cumulative_profit = (annual_revenue * y) - (
            initial_investment +
            technology_reporting_cost * y +
            electricity_cost * y +
            maintenance_cost * y
        )
        cashflow.append(cumulative_profit)

cf_df = pd.DataFrame({
    "Year": range(0, years + 1),
    "CashFlow": cashflow
})

# Break-even
break_even_year = None
for i in range(len(cf_df)):
    if cf_df["CashFlow"].iloc[i] >= 0:
        break_even_year = cf_df["Year"].iloc[i]
        break

# Colore positivo/negativo
cf_df["Color"] = cf_df["CashFlow"].apply(lambda x: ESAOTE_GREEN if x >= 0 else "#C44E52")

# Istogramma cumulativo
bar_chart = alt.Chart(cf_df).mark_bar().encode(
    x=alt.X("Year:O", title="Year"),
    y=alt.Y("CashFlow:Q", title=f"Cumulative Cash Flow ({currency_symbol})"),
    color=alt.Color("Color:N", scale=None)
)

# Linea zero
zero_line = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(
    strokeDash=[5,5],
    color="black"
).encode(y="y:Q")

# Marker break-even
if break_even_year is not None:
    be_point = alt.Chart(cf_df[cf_df["Year"] == break_even_year]).mark_circle(
        size=200,
        color="gold"
    ).encode(
        x="Year:O",
        y="CashFlow:Q"
    )
    chart = bar_chart + zero_line + be_point
else:
    chart = bar_chart + zero_line

st.altair_chart(
    chart.properties(
        height=500,
        title="Esaote MRI – Time to Value"
    ),
    use_container_width=True
)

# Executive message
if break_even_year:
    st.success(f"Payback achieved in Year {break_even_year}")
else:
    st.warning("Payback not reached within selected horizon")
# =============================
# BREAK EVEN MESSAGE
# =============================

if break_even_year:
    st.success(f"🎯 Break-even achieved in Year {break_even_year}")
else:
    st.warning("Break-even not reached within selected period")
