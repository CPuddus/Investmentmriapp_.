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
# FORMAT FUNCTION
# =============================
def format_currency(value, symbol, currency_key):
    abs_val = abs(value)

    if "INR" in currency_key:
        if abs_val >= 1e7:
            return f"{symbol}{value/1e7:.2f} Cr"
        elif abs_val >= 1e5:
            return f"{symbol}{value/1e5:.2f} L"
        else:
            return f"{symbol}{value:,.0f}"

    if any(x in currency_key for x in ["JPY","KRW","VND","IDR"]):
        return f"{symbol}{value:,.0f}"

    return f"{symbol}{value:,.2f}"

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
    st.markdown("<h1>Esaote MRI – ROI Simulator</h1>", unsafe_allow_html=True)

# =============================
# CURRENCY
# =============================
st.markdown("### Currency")

currency_options = {
    "EUR (€)": {"rate":1.0,"symbol":"€"},
    "USD ($)": {"rate":1.08,"symbol":"$"},
    "GBP (£)": {"rate":0.85,"symbol":"£"},
    "CHF (CHF)": {"rate":0.95,"symbol":"CHF"},

    "JPY (¥ - Japan)": {"rate":160.0,"symbol":"¥"},
    "KRW (₩ - South Korea)": {"rate":1450.0,"symbol":"₩"},
    "INR (₹ - India)": {"rate":90.0,"symbol":"₹"},
    "AUD (A$ - Australia)": {"rate":1.65,"symbol":"A$"},
    "PHP (₱ - Philippines)": {"rate":60.0,"symbol":"₱"},
    "MYR (RM - Malaysia)": {"rate":5.1,"symbol":"RM"},
    "IDR (Rp - Indonesia)": {"rate":17000.0,"symbol":"Rp"},
    "PKR (₨ - Pakistan)": {"rate":300.0,"symbol":"₨"},
    "BDT (৳ - Bangladesh)": {"rate":120.0,"symbol":"৳"},
    "THB (฿ - Thailand)": {"rate":39.0,"symbol":"฿"},
    "VND (₫ - Vietnam)": {"rate":27000.0,"symbol":"₫"}
}

selected_currency = st.selectbox("Select Currency", list(currency_options.keys()))
exchange_rate = currency_options[selected_currency]["rate"]
currency_symbol = currency_options[selected_currency]["symbol"]

# =============================
# INPUTS
# =============================
st.markdown("### Investment")

years = st.slider("Analysis Period (Years)",1,15,10)
initial_investment = st.number_input("Initial Investment",0,20000000000,500000,10000)

leasing_pct = st.slider("Leasing %",0,100,80)
leas_month = st.slider("Leasing Period (Months)", 12, 120, 60)
interest_pct = st.slider("Interest %",0,15,5)

st.markdown("### Recurring costs")

technology_cost = st.number_input("Human Resouces Monthly",0,1000000000,2500,100)*12
electricity_cost = st.number_input("Electricity Monthly",0,2000000000,5000,1000)*12
maintenance_cost = st.number_input("Maintenance Annual",0,10000000000,20000,5000)

reporting_pct = st.slider("Reporting Cost %",0,20,5)

st.markdown("### Income")

exams_per_day = st.slider("Exams per Day",1,30,12)
working_days = st.slider("Working Days",1,365,200)
average_price = st.number_input("Average Exam price",0,1500000,5)

annual_revenue = exams_per_day * working_days * average_price
reporting_cost = annual_revenue * reporting_pct/100

# currency conversion
initial_investment *= exchange_rate
annual_revenue *= exchange_rate
technology_cost *= exchange_rate
electricity_cost *= exchange_rate
maintenance_cost *= exchange_rate
reporting_cost *= exchange_rate

# =============================
# LEASING
# =============================
leasing_amount = initial_investment * leasing_pct / 100
r_month = (interest_pct / 100) / 12
n_months = leas_month

if r_month > 0:
    monthly_payment = leasing_amount * (
        r_month * (1 + r_month)**n_months
    ) / ((1 + r_month)**n_months - 1)
else:
    monthly_payment = leasing_amount / n_months

annual_leasing_payment = monthly_payment * 12
leasing_years = leas_month / 12

# =============================
# MODEL
# =============================
def calculate_financials():
    expenses=[initial_investment]
    revenues=[0]

    cumulative_cost=initial_investment
    cumulative_rev=0

    for y in range(1,years+1):

        leasing_cost = annual_leasing_payment if y <= leasing_years else 0

        yearly_cost=(technology_cost+electricity_cost+maintenance_cost+leasing_cost+reporting_cost)

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

c1.metric("Revenue", format_currency(df['Revenues'].iloc[-1], currency_symbol, selected_currency))
c2.metric("Profit", format_currency(final_profit, currency_symbol, selected_currency))
c3.metric("ROI", f"{roi:.1f}%")

# =============================
# CHARTS
# =============================
line_chart = alt.Chart(df).transform_fold(
    ["Expenses","Revenues"]
).mark_line().encode(
    x="Year:O",
    y=alt.Y("value:Q", axis=alt.Axis(format="~s")),
    color="key:N"
)

st.altair_chart(line_chart, use_container_width=True)

profit_chart = alt.Chart(df).mark_bar().encode(
    x="Year:O",
    y=alt.Y("Profit:Q", axis=alt.Axis(format="~s")),
    color=alt.condition(alt.datum.Profit>=0, alt.value(ESAOTE_GREEN), alt.value("red"))
)

st.altair_chart(profit_chart, use_container_width=True)
# =============================
#  Create PDF
# =============================
def create_pdf_client_ready():
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    from io import BytesIO

    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader

    # =========================================================
    # CONFIG (visual style)
    # =========================================================
    PRIMARY = "#1F4E79"   # deep corporate blue
    GREEN = "#2E7D32"
    RED = "#C62828"
    GREY = "#6B6B6B"

    # =========================================================
    # HELPERS
    # =========================================================
    def fig_to_img(fig):
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)
        return buf

    def format_num(x):
        return f"{x:,.0f}"

    # =========================================================
    # INSIGHTS ENGINE (business layer)
    # =========================================================
    def generate_insights():
        insights = []

        roi_level = (
            "strong" if roi > 50 else
            "moderate" if roi > 10 else
            "weak"
        )

        insights.append(f"ROI performance is classified as {roi_level} ({roi:.1f}%).")

        if break_even:
            insights.append(f"Break-even achieved in year {break_even}.")
        else:
            insights.append("Break-even not reached in projected period.")

        trend = df["Profit"].iloc[-3:].mean()
        if trend > 0:
            insights.append("Recent profitability trend is positive.")
        else:
            insights.append("Recent profitability shows downward pressure.")

        return insights

    insights = generate_insights()

    # =========================================================
    # CHART 1 — PROFIT TREND
    # =========================================================
    fig1, ax1 = plt.subplots(figsize=(7, 3))

    colors = [GREEN if v >= 0 else RED for v in df["Profit"]]
    ax1.bar(df["Year"], df["Profit"], color=colors)

    ax1.axhline(0, color="black", linewidth=0.8)
    if break_even:
        ax1.axvline(break_even, linestyle="--", color=PRIMARY)

    ax1.set_title("Profit Evolution", fontsize=12, color=PRIMARY)
    ax1.set_ylabel(f"Profit ({currency_symbol})")

    ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, _: format_num(x)))

    chart1 = fig_to_img(fig1)

    # =========================================================
    # CHART 2 — REVENUE VS COST
    # =========================================================
    fig2, ax2 = plt.subplots(figsize=(7, 3))

    ax2.plot(df["Year"], df["Revenues"], label="Revenue", linewidth=2, color=PRIMARY)
    ax2.plot(df["Year"], df["Expenses"], label="Costs", linewidth=2, color=RED)

    ax2.set_title("Revenue vs Costs", fontsize=12, color=PRIMARY)
    ax2.set_ylabel(f"Value ({currency_symbol})")
    ax2.legend()

    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: format_num(x)))

    chart2 = fig_to_img(fig2)

    # =========================================================
    # PDF
    # =========================================================
    pdf_path = BytesIO()
    c = canvas.Canvas(pdf_path, pagesize=A4)

    # -----------------------------
    # HEADER
    # -----------------------------
    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(50, 800, "MRI Investment ROI Report")

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(50, 785, "Executive Financial Analysis")

    # LOGO (safe)
    try:
        response = requests.get(
            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTso1Ip1hX3Ji8xSyaQGMKfVBEuea5_IWuDkw&s",
            timeout=5
        )
        response.raise_for_status()
        img = ImageReader(BytesIO(response.content))
        c.drawImage(img, 480, 785, width=70, height=18)
    except Exception:
        pass  # don't crash if logo fails


    # divider
    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.line(50, 775, 550, 775)

    # -----------------------------
    # KPI SECTION (McKinsey style cards)
    # -----------------------------
    def kpi(x, y, title, value):
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(x, y, title)

        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x, y - 14, value)

    kpi(50, 740, "Revenue", format_currency(df["Revenues"].iloc[-1], currency_symbol, selected_currency))
    kpi(220, 740, "Profit", format_currency(final_profit, currency_symbol, selected_currency))
    kpi(360, 740, "ROI", f"{roi:.1f}%")

    if break_even:
        kpi(470, 740, "Break-even", str(break_even))

    # -----------------------------
    # EXECUTIVE INSIGHTS
    # -----------------------------
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(50, 690, "Summary")

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.35, 0.35, 0.35)

    y = 670
    for ins in insights:
        c.drawString(55, y, f"• {ins}")
        y -= 15

    # -----------------------------
    # CHARTS SECTION
    # -----------------------------
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(50, 600, "Financial Performance")

    c.drawImage(ImageReader(chart1), 50, 380, width=500, height=200)
    c.drawImage(ImageReader(chart2), 50, 150, width=500, height=200)

    # -----------------------------
    # FOOTER
    # -----------------------------
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 30, "Confidential — Generated MRI ROI Analysis")

    c.save()
    pdf_path.seek(0)

    return pdf_path
     
    
# =============================
# DOWNLOAD BUTTON (FUORI dalla funzione)
# =============================
if st.button("Export Report"):
    pdf = create_pdf_client_ready()

    st.download_button(
        "Download  Report",
        data=pdf,
        file_name="MRI_ROI_Report.pdf",
        mime="application/pdf"
    )
