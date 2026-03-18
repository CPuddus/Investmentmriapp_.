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

leasing_pct = st.slider("Leasing %",0,100,80)
leas_month = st.slider("Leasing Period (Months)",0,60,120)
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
leasing_amount = initial_investment * leasing_pct/100
total_interest = leasing_amount * interest_pct* leas_month/100
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
def create_pdf():
    # =============================
    # CREATE PROFIT CHART
    # =============================
    chart_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name

    plt.figure(figsize=(9,5))
    years_plot = df["Year"].values
    profit_plot = df["Profit"].values

    plt.fill_between(
        years_plot,
        profit_plot,
        0,
        where=(profit_plot <= 0),
        color="red",
        alpha=0.3
    )

    plt.fill_between(
        years_plot,
        profit_plot,
        0,
        where=(profit_plot >= 0),
        color="green",
        alpha=0.3
    )

    plt.plot(years_plot, profit_plot, linewidth=3, color=ESAOTE_GREEN)
    plt.axhline(0, color="black")

    if break_even:
        plt.scatter(break_even, 0, color="blue", s=120)
        plt.axvline(break_even, linestyle="--", color="blue")
        plt.text(break_even, 0, f" Break-even Y{break_even}", fontsize=11, fontweight="bold")

    plt.xlabel("Year")
    plt.ylabel(f"Profit ({currency_symbol})")
    plt.title("MRI Annual Profit")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()

    # =============================
    # DOWNLOAD LOGO
    # =============================
    logo_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTso1Ip1hX3Ji8xSyaQGMKfVBEuea5_IWuDkw&s"
    response = requests.get(logo_url)
    img = Image.open(BytesIO(response.content))
    logo_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
    img.save(logo_path)

    # =============================
    # CREATE PDF
    # =============================
    pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(pdf_file.name, pagesize=A4)

    c.drawImage(logo_path, 40, 770, width=120, height=40)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(180, 780, "MRI ROI Financial Report")
    c.setFont("Helvetica", 11)

    c.drawString(50,720, f"Total Revenue: {currency_symbol}{df['Revenues'].iloc[-1]:,.0f}")
    c.drawString(50,700, f"Net Profit: {currency_symbol}{final_profit:,.0f}")
    c.drawString(50,680, f"ROI: {roi:.1f}%")
    if break_even:
        c.drawString(50,660, f"Payback Year: {break_even}")

    # Chart
    c.drawImage(chart_path, 40, 380, width=520, height=260)

    # Table
    table_data = [["Year","Revenue","Expenses","Profit"]]
    for _, row in df.iterrows():
        table_data.append([
            int(row["Year"]),
            f"{currency_symbol}{row['Revenues']:,.0f}",
            f"{currency_symbol}{row['Expenses']:,.0f}",
            f"{currency_symbol}{row['Profit']:,.0f}"
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),HexColor(ESAOTE_GREEN)),
        ("TEXTCOLOR",(0,0),(-1,0),"white"),
        ("GRID",(0,0),(-1,-1),0.5,"grey"),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold")
    ]))
    table.wrapOn(c,400,200)
    table.drawOn(c,60,150)

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
