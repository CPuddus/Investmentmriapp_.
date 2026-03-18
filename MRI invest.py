import streamlit as st
import pandas as pd
import altair as alt
import tempfile
import requests
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Table, TableStyle

ESAOTE_GREEN = "#6CC24A"

# =============================
# HEADER
# =============================
col1, col2 = st.columns([1,5])

with col1:
    st.image(
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTso1Ip1hX3Ji8xSyaQGMKfVBEuea5_IWuDkw&s",
        width=150
    )

with col2:
    st.markdown(
        "<h1>Esaote MRI – ROI Simulator</h1>",
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
# INVESTMENT
# =============================
st.markdown("### Investment")

years = st.slider("Analysis Period (Years)",1,15,10)

initial_investment = st.number_input(
    "Initial Investment",
    0,2000000,500000,10000
)

st.markdown("### Leasing")

leasing_pct = st.slider("Leasing % of initial investiemnts",0,100,80)
leas_month = st.slider("Leasing Period (Months)", 12, 120, 60)
interest_pct = st.slider("Interest %",0,15,5)

# =============================
# OPERATING COSTS
# =============================
st.markdown("### Operating Costs")

technology_cost = st.number_input(
    "Human Resources Cost Monthly",
    0,10000,2500,100
)*12

electricity_cost = st.number_input(
    "Electricity Monthly",
    0,20000,5000,1000
)*12

maintenance_cost = st.number_input(
    "Annual Maintenance",
    0,100000,20000,5000
)

reporting_pct = st.slider("Reporting Cost %",0,20,5)

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
# LEASING
# =============================
# =============================
# LEASING (REALISTICO MENSILE)
# =============================
leasing_amount = initial_investment * leasing_pct / 100

r_month = (interest_pct / 100) / 12
n_months = leas_month

if n_months > 0:
    if r_month > 0:
        monthly_payment = leasing_amount * (
            r_month * (1 + r_month)**n_months
        ) / ((1 + r_month)**n_months - 1)
    else:
        monthly_payment = leasing_amount / n_months
else:
    monthly_payment = 0

annual_leasing_payment = monthly_payment * 12
leasing_years = leas_month / 12

# =============================
# FINANCIAL MODEL
# =============================
def calculate_financials():
    expenses=[initial_investment]
    revenues=[0]

    cumulative_cost=initial_investment
    cumulative_rev=0

    for y in range(1,years+1):

        if y <= int(leasing_years):
           leasing_cost = annual_leasing_payment
        else:
           leasing_cost = 0
        yearly_cost=(
            technology_cost+
            electricity_cost+
            maintenance_cost+
            leasing_cost+
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

    df["Profit"] = df["Revenues"] - df["Expenses"]
    return df

df = calculate_financials()

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
c1,c2,c3=st.columns(3)
c1.metric("Total Revenue", f"{currency_symbol}{df['Revenues'].iloc[-1]:,.0f}")
c2.metric("Net Profit", f"{currency_symbol}{final_profit:,.0f}")
c3.metric("ROI", f"{roi:.1f}%")

# =============================
# ALTAIR CHART: Revenue vs Expenses
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
st.altair_chart(line_chart,use_container_width=True)

# =============================
# ALTAIR CHART: Profit Annuale
# =============================
st.markdown("### Annual Profit Histogram")

profit_chart = alt.Chart(df).mark_bar().encode(
    x=alt.X("Year:O", title="Year"),
    y=alt.Y("Profit:Q", title=f"Profit ({currency_symbol})"),
    color=alt.condition(
        alt.datum.Profit >= 0,
        alt.value(ESAOTE_GREEN),
        alt.value("red")
    ),
    tooltip=["Year","Profit"]
)

zero_line = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(
    color="black"
).encode(y="y:Q")

chart = profit_chart + zero_line

if break_even:
    breakeven_line = alt.Chart(pd.DataFrame({"Year":[break_even]})).mark_rule(
        color="blue", strokeDash=[6,4]
    ).encode(x="Year:O")
    chart = chart + breakeven_line

st.altair_chart(chart, use_container_width=True)

# =============================
# PDF EXPORT
# =============================
def format_number(value):
    if abs(value) >= 1_000_000:
        return f"{currency_symbol}{value/1_000_000:.1f}M"
    elif abs(value) >= 1_000:
        return f"{currency_symbol}{value/1_000:.0f}K"
    else:
        return f"{currency_symbol}{value:,.0f}"


def create_pdf():

    # =============================
    # CREATE PROFIT CHART
    # =============================
    chart_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name

    plt.figure(figsize=(9,5))
    years_plot = df["Year"].values
    profit_plot = df["Profit"].values

    plt.bar(years_plot, profit_plot)

    plt.axhline(0)

# evidenzia positivo/negativo (senza colori espliciti forti)
for i, v in enumerate(profit_plot):
    if v < 0:
        plt.bar(years_plot[i], v)

if break_even:
    plt.axvline(break_even, linestyle="--")
    plt.text(break_even, 0, f" BE Y{break_even}")

    if break_even:
        plt.axvline(break_even, linestyle="--")
        plt.text(break_even, 0, f"Break-even Y{break_even}")

    plt.title("Profit Evolution")
    plt.xlabel("Year")
    plt.ylabel("Profit")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()

    # =============================
    # LOGO
    # =============================
    logo_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTso1Ip1hX3Ji8xSyaQGMKfVBEuea5_IWuDkw&s"
    response = requests.get(logo_url)
    img = Image.open(BytesIO(response.content))
    logo_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    img.save(logo_path)

    # =============================
    # PDF INIT
    # =============================
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(pdf_file.name, pagesize=A4)

    # =============================
    # HEADER
    # =============================
    c.drawImage(logo_path, 40, 770, width=120, height=40)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(180, 780, "MRI ROI Financial Report")

    # =============================
    # KPI BOX
    # =============================
    c.setFillColor(HexColor(ESAOTE_GREEN))
    c.rect(40, 690, 520, 60, fill=1)

    c.setFillColor("white")
    c.setFont("Helvetica-Bold", 13)
    c.drawString(60, 720, f"Revenue: {format_number(df['Revenues'].iloc[-1])}")
    c.drawString(240, 720, f"Profit: {format_number(final_profit)}")
    c.drawString(420, 720, f"ROI: {roi:.1f}%")

    # =============================
    # LEASING INFO
    # =============================
    c.setFillColor("black")
    c.setFont("Helvetica", 11)

    c.drawString(50, 660, f"Monthly Leasing: {format_number(monthly_payment)}")
    c.drawString(50, 640, f"Leasing Duration: {leas_month} months")
    c.drawString(50, 620, f"Total Leasing Paid: {format_number(monthly_payment * leas_month)}")

    # =============================
    # BREAK EVEN HIGHLIGHT
    # =============================
    if break_even:
        c.setFillColor(HexColor("#E8F5E9"))
        c.rect(40, 590, 520, 25, fill=1)
        c.setFillColor("black")
        c.drawString(50, 598, f"Break-even reached in Year {break_even}")

    # =============================
    # CHART
    # =============================
    c.drawImage(chart_path, 40, 320, width=520, height=250)

    # =============================
    # TABLE
    # =============================
    table_data = [["Year","Revenue","Expenses","Profit"]]

    for _, row in df.iterrows():
        table_data.append([
            int(row["Year"]),
            format_number(row["Revenues"]),
            format_number(row["Expenses"]),
            format_number(row["Profit"])
        ])

    table = Table(table_data)

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),HexColor(ESAOTE_GREEN)),
        ("TEXTCOLOR",(0,0),(-1,0),"white"),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("GRID",(0,0),(-1,-1),0.25,"grey"),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("BOTTOMPADDING",(0,0),(-1,0),10),
    ]))

    table.wrapOn(c,400,200)
    table.drawOn(c,60,120)

    # =============================
    # FOOTER
    # =============================
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor("grey")
    c.drawString(40, 30, "Confidential – MRI ROI Simulation")
    c.drawRightString(550, 30, "Generated by ROI Simulator")

    # =============================
    # PAGE 2 – SCENARIOS
    # =============================
    c.showPage()

    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, 780, "Scenario Analysis")

    # simple scenarios
    best_revenue = annual_revenue * 1.2
    worst_revenue = annual_revenue * 0.8

    c.setFont("Helvetica", 12)

    c.drawString(50, 720, f"Base Revenue: {format_number(annual_revenue)}")
    c.drawString(50, 700, f"Best Case (+20%): {format_number(best_revenue)}")
    c.drawString(50, 680, f"Worst Case (-20%): {format_number(worst_revenue)}")

    # footer page 2
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColor("grey")
    c.drawString(40, 30, "Confidential – MRI ROI Simulation")
    c.drawRightString(550, 30, "Page 2")

    c.save()

    return pdf_file.name

# =============================
# DOWNLOAD
# =============================
if st.button("Export PDF Report"):
    pdf_file=create_pdf()
    with open(pdf_file,"rb") as f:
        st.download_button(
            "Download Report",
            data=f,
            file_name="MRI_ROI_Report.pdf",
            mime="application/pdf"
        )
