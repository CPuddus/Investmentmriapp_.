import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import plotly.graph_objects as go

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
# ANIMATED WATERFALL
# =============================

st.markdown("## Investment Evolution – Animated Waterfall")

records = []

tech_cum = 0
elec_cum = 0
maint_cum = 0
rev_cum = 0

for year in range(1, years + 1):

    tech_cum += technology_reporting_cost
    elec_cum += electricity_cost
    maint_cum += maintenance_cost
    rev_cum += annual_revenue

    net_profit = rev_cum - (
        initial_investment + tech_cum + elec_cum + maint_cum
    )

    records.append({
        "Year": year,
        "Initial Investment": -initial_investment,
        "Revenue": rev_cum,
        "Technology Cost": -tech_cum,
        "Electricity Cost": -elec_cum,
        "Maintenance Cost": -maint_cum,
        "Net Profit": net_profit
    })

df_w = pd.DataFrame(records)

fig = go.Figure()

for year in df_w["Year"]:

    row = df_w[df_w["Year"] == year].iloc[0]

    fig.add_trace(go.Waterfall(
        name=f"Year {year}",
        orientation="v",
        measure=["relative","relative","relative","relative","relative","total"],
        x=[
            "Initial Investment",
            "Revenue",
            "Technology Cost",
            "Electricity Cost",
            "Maintenance Cost",
            "Net Profit"
        ],
        y=[
            row["Initial Investment"],
            row["Revenue"],
            row["Technology Cost"],
            row["Electricity Cost"],
            row["Maintenance Cost"],
            row["Net Profit"]
        ],
        increasing={"marker":{"color":ESAOTE_GREEN}},
        decreasing={"marker":{"color":"red"}},
        totals={"marker":{
            "color":"gold" if break_even_year and year >= break_even_year else "#1f77b4"
        }},
        visible=(year == 1)
    ))

steps = []

for i, year in enumerate(df_w["Year"]):
    step = dict(
        method="update",
        args=[{"visible":[False]*len(fig.data)},
              {"title":f"Esaote MRI Investment – Year {year}" +
                       (" ✅ BREAK EVEN" if break_even_year and year >= break_even_year else "")}]
    )
    step["args"][0]["visible"][i] = True
    steps.append(step)

fig.update_layout(
    sliders=[dict(
        active=0,
        currentvalue={"prefix":"Year: "},
        steps=steps
    )],
    height=650,
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

# =============================
# BREAK EVEN MESSAGE
# =============================

if break_even_year:
    st.success(f"🎯 Break-even achieved in Year {break_even_year}")
else:
    st.warning("Break-even not reached within selected period")
