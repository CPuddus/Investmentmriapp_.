SALES INTERNATIONAL – ANNUAL PROFIT HISTOGRAM
# =============================

st.markdown("## Annual Profit Overview")

# Calcolo profitto anno per anno
profits = []
for y in range(1, years + 1):
    annual_profit = (annual_revenue) - (
        technology_reporting_cost +
        electricity_cost +
        maintenance_cost
    )
    profits.append(annual_profit)

profit_df = pd.DataFrame({
    "Year": range(1, years + 1),
    "Profit": profits
})

# Colori dinamici
def bar_color(val):
    if val < 0:
        return "#C44E52"  # rosso
    return ESAOTE_GREEN  # verde

profit_df["Color"] = profit_df["Profit"].apply(bar_color)

# Evidenzia break-even
break_even_year = None
cumulative = -initial_investment
for i, val in enumerate(profits):
    cumulative += val
    if cumulative >= 0 and break_even_year is None:
        break_even_year = i + 1

profit_df["BreakEven"] = profit_df["Year"].apply(
    lambda x: "gold" if break_even_year and x == break_even_year else None
)

bars = alt.Chart(profit_df).mark_bar().encode(
    x=alt.X("Year:O", title="Year"),
    y=alt.Y("Profit:Q", title=f"Annual Profit ({currency_symbol})"),
    color=alt.condition(
        alt.datum.Year == break_even_year,
        alt.value("gold"),
        alt.Color("Color:N", scale=None)
    ),
    tooltip=[
        alt.Tooltip("Year:O", title="Year"),
        alt.Tooltip("Profit:Q", title="Profit", format=",")
    ]
)

zero_line = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(
    color="black"
).encode(y="y:Q")

st.altair_chart((bars + zero_line).properties(
    height=450,
    title="Esaote MRI – Annual Profit per Year"
), use_container_width=True)

# Executive message
if break_even_year:
    st.success(f"Payback achieved in Year {break_even_year}")
else:
    st.warning("Payback not reached within selected horizon")
