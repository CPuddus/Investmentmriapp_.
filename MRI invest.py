import streamlit as st
import pandas as pd
import altair as alt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile

# =============================
# BRAND STYLE
# =============================

ESAOTE_GREEN = "#6CC24A"

# =============================
# HEADER
# =============================

col1, col2 = st.columns([1,5])

with col1:
    st.image(
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTso1Ip1hX3Ji8xSyaQGMKfVBEuea5_IWuDkw&s",
        width=160
    )

with col2:
    st.markdown(
        "<h1 style='margin-bottom:0;'>Esaote MRI – ROI Simulator</h1>",
        unsafe_allow_html=True
    )

# =============================
# CURRENCY
# =============================

st.markdown("### Currency")

currency_options = {
    "EUR (€)": {"rate":1.0,"symbol":"€"},
    "USD ($)": {"rate":1.08,"symbol":"$"},
    "GBP (£)": {"rate":0.85,"symbol":"£"},
    "CHF (CHF)": {"rate":0.95,"symbol":"CHF"}
}

selected_currency = st.selectbox("Select Currency", list(currency_options.keys()))

exchange_rate = currency_options[selected_currency]["rate"]
currency_symbol = currency_options[selected_currency]["symbol"]

# =============================
# INVESTMENT PARAMETERS
# =============================

st.markdown("### Investment")

years = st.slider("Analysis Period (Years)",1,15,10)

initial_investment = st.number_input("Initial Investment",0,2000000,500000,10000)

leasing_pct = st.slider("Leasing %",0,100,80)
interest_pct = st.slider("Interest %",0,15,5)
reporting_pct = st.slider("Reporting Cost %",0,20,5)

# =============================
# OPERATING COSTS
# =============================

st.markdown("### Operating Costs")

technology_cost = st.number_input("Technology Cost Monthly",0,10000,2500,100)*12
electricity_cost = st.number_input("Electricity Monthly",0,20000,5000,1000)*12
maintenance_cost = st.number_input("Annual Maintenance",0,100000,20000,5000)

# =============================
# REVENUE
# =============================

st.markdown("### Revenue")

exams_per_day = st.slider("Exams per Day",1,30,12)
working_days = st.slider("Working Days per Year",1,365,200)
average_price = st.slider("Average Exam Price",1,1000,200)

annual_revenue = exams_per_day * working_days * average_price
reporting_cost = annual_revenue * reporting_pct/100

# =============================
# CURRENCY CONVERSION
# =============================

initial_investment *= exchange_rate
annual_revenue *= exchange_rate
technology_cost *= exchange_rate
electricity_cost *= exchange_rate
maintenance_cost *= exchange_rate
reporting_cost *= exchange_rate

# =============================
# LEASING CALCULATION
# =============================

leasing_amount = initial_investment * leasing_pct/100
total_interest = leasing_amount * interest_pct/100
annual_interest = total_interest / years

# =============================
# FINANCIAL MODEL
# =============================

def calculate_financials():

    expenses=[initial_investment]
    revenues=[0]

    cumulative_cost=initial_investment
    cumulative_rev=0

    for y in range(1,years+1):

        yearly_cost=(
            technology_cost+
            electricity_cost+
            maintenance_cost+
            annual_interest+
            reporting_cost
        )

        cumulative_cost+=yearly_cost
        cumulative_rev+=annual_revenue

        expenses.append(cumulative_cost)
        revenues.append(cumulative_rev)

    df=pd.DataFrame({
        "Year":range(0,years+1),
        "Expenses":expenses,
        "Revenues":revenues
    })

    df["Profit"]=df["Revenues"]-df["Expenses"]

    return df

df=calculate_financials()

# =============================
# KPI
# =============================

final_profit=df["Profit"].iloc[-1]
roi=(final_profit/initial_investment)*100 if initial_investment>0 else 0

break_even=None

for i in range(len(df)):
    if df["Profit"].iloc[i]>=0:
        break_even=df["Year"].iloc[i]
        break

st.markdown("## Financial Overview")

col1,col2,col3=st.columns(3)

col1.metric("Total Revenue",f"{currency_symbol}{df['Revenues'].iloc[-1]:,.0f}")
col2.metric("Net Profit",f"{currency_symbol}{final_profit:,.0f}")
col3.metric("ROI",f"{roi:.1f}%")

# =============================
# PERFORMANCE CHART
# =============================

st.markdown("### Revenue vs Expenses")

line_chart = alt.Chart(df).transform_fold(
    ["Expenses","Revenues"],
    as_=["Category","Value"]
).mark_line(strokeWidth=4).encode(
    x="Year:O",
    y=alt.Y("Value:Q",title=f"Value ({currency_symbol})"),
    color=alt.Color(
        "Category:N",
        scale=alt.Scale(
            domain=["Expenses","Revenues"],
            range=["red",ESAOTE_GREEN]
        )
    )
)

st.altair_chart(line_chart.properties(height=400),use_container_width=True)

# =============================
# PAYBACK CURVE
# =============================

st.markdown("## Payback Curve")

cf_df=df.copy()
cf_df["CashFlow"]=cf_df["Profit"]

area_chart=alt.Chart(cf_df).mark_area(
    interpolate="monotone",
    opacity=0.6
).encode(
    x="Year:O",
    y="CashFlow:Q",
    color=alt.condition(
        alt.datum.CashFlow>=0,
        alt.value(ESAOTE_GREEN),
        alt.value("#E45756")
    )
)

line_chart=alt.Chart(cf_df).mark_line(
    color="black",
    strokeWidth=3
).encode(
    x="Year:O",
    y="CashFlow:Q"
)

zero_line=alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(
    strokeDash=[6,6],
    color="black"
).encode(y="y:Q")

if break_even:

    be_point=alt.Chart(
        cf_df[cf_df["Year"]==break_even]
    ).mark_point(
        size=300,
        color="gold",
        filled=True
    ).encode(
        x="Year:O",
        y="CashFlow:Q"
    )

    chart=area_chart+line_chart+zero_line+be_point

else:
    chart=area_chart+line_chart+zero_line

st.altair_chart(chart.properties(height=500),use_container_width=True)

# =============================
# BREAK EVEN MESSAGE
# =============================

if break_even:
    st.success(f"Payback achieved in Year {break_even}")
else:
    st.warning("Payback not reached")

# =============================
# PDF EXPORT
# =============================

def create_pdf():

    file=tempfile.NamedTemporaryFile(delete=False,suffix=".pdf")
    c=canvas.Canvas(file.name,pagesize=A4)

    c.setFont("Helvetica-Bold",16)
    c.drawString(50,800,"Esaote MRI ROI Report")

    c.setFont("Helvetica",12)

    c.drawString(50,760,f"Total Revenue: {currency_symbol}{df['Revenues'].iloc[-1]:,.0f}")
    c.drawString(50,740,f"Net Profit: {currency_symbol}{final_profit:,.0f}")
    c.drawString(50,720,f"ROI: {roi:.1f}%")

    if break_even:
        c.drawString(50,700,f"Payback Year: {break_even}")
    else:
        c.drawString(50,700,"Payback not reached")

    c.drawString(50,660,"Operational Assumptions")

    c.drawString(50,640,f"Exams per Day: {exams_per_day}")
    c.drawString(50,620,f"Working Days: {working_days}")
    c.drawString(50,600,f"Average Price: {currency_symbol}{average_price}")

    c.save()

    return file.name

if st.button("Export PDF Report"):

    pdf_file=create_pdf()

    with open(pdf_file,"rb") as f:
        st.download_button(
            "Download Report",
            f,
            file_name="MRI_ROI_Report.pdf"
        )
