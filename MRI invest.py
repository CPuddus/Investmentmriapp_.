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
# ANIMATED WATERFALL
# =============================
# =============================
# WATERFALL ALTAIR – YEAR BY YEAR
# =============================

st.markdown("## Investment Evolution – Waterfall (Altair)")

# Slider anno per simulare animazione
selected_year = st.slider("Select Year", 1, years, 1)

# Calcoli cumulativi fino all'anno selezionato
tech_cum = technology_reporting_cost * selected_year
elec_cum = electricity_cost * selected_year
maint_cum = maintenance_cost * selected_year
rev_cum = annual_revenue * selected_year

net_profit = rev_cum - (
    initial_investment + tech_cum + elec_cum + maint_cum
)

# Break-even check
break_even_year = None
for y in range(1, years + 1):
    test_profit = (annual_revenue * y) - (
        initial_investment +
        technology_reporting_cost * y +
        electricity_cost * y +
        maintenance_cost * y
    )
    if test_profit >= 0:
        break_even_year = y
        break

# Costruiamo dataframe waterfall
categories = [
    "Initial Investment",
    "Revenue",
    "Technology Cost",
    "Electricity Cost",
    "Maintenance Cost",
    "Net Profit"
]

values = [
    -initial_investment,
    rev_cum,
    -tech_cum,
    -elec_cum,
    -maint_cum,
    net_profit
]

wf_df = pd.DataFrame({
    "Category": categories,
    "Value": values
})

# Calcolo cumulative per effetto waterfall
wf_df["Cumulative"] = wf_df["Value"].cumsum()
wf_df["Previous"] = wf_df["Cumulative"] - wf_df["Value"]

# Colori dinamici
def get_color(row):
    if row["Category"] == "Net Profit":
        if break_even_year and selected_year >= break_even_year:
            return "gold"
        return "#1f77b4"
    elif row["Value"] >= 0:
        return ESAOTE_GREEN
    else:
        return "red"

wf_df["Color"] = wf_df.apply(get_color, axis=1)

# Grafico waterfall
waterfall_chart = alt.Chart(wf_df).mark_bar().encode(
    x=alt.X("Category:N", sort=None),
    y=alt.Y("Previous:Q", title=f"Value ({currency_symbol})"),
    y2="Cumulative:Q",
    color=alt.Color("Color:N", scale=None)
)

text = alt.Chart(wf_df).mark_text(
    align='center',
    baseline='middle',
    dy=-10,
    fontSize=12
).encode(
    x=alt.X("Category:N", sort=None),
    y="Cumulative:Q",
    text=alt.Text("Value:Q", format=",.0f")
)

final_chart = waterfall_chart + text

st.altair_chart(
    final_chart.properties(
        height=500,
        title=f"Esaote MRI – Year {selected_year}" +
              (" ✅ BREAK EVEN REACHED" if break_even_year and selected_year >= break_even_year else "")
    ),
    use_container_width=True
)

# Messaggio Break-even
if break_even_year:
    st.success(f"🎯 Break-even achieved in Year {break_even_year}")
else:
    st.warning("Break-even not reached within selected period")

# =============================
# BREAK EVEN MESSAGE
# =============================

if break_even_year:
    st.success(f"🎯 Break-even achieved in Year {break_even_year}")
else:
    st.warning("Break-even not reached within selected period")
