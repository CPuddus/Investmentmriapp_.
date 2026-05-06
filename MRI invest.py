import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

ESAOTE_GREEN = "#6CC24A"
LOGO_URL = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTso1Ip1hX3Ji8xSyaQGMKfVBEuea5_IWuDkw&s"


# =============================
# CURRENCY FORMAT
# =============================
def format_currency(value, symbol, currency_key):
    abs_val = abs(value)

    if "INR" in currency_key:
        if abs_val >= 1e7:
            return f"{symbol}{value/1e7:.2f} Cr"
        elif abs_val >= 1e5:
            return f"{symbol}{value/1e5:.2f} L"
        return f"{symbol}{value:,.0f}"

    if any(x in currency_key for x in ["JPY", "KRW", "VND", "IDR"]):
        return f"{symbol}{value:,.0f}"

    return f"{symbol}{value:,.2f}"


# =============================
# HEADER
# =============================
col1, col2 = st.columns([1, 5])

with col1:
    st.image(LOGO_URL, width=140)

with col2:
    st.markdown("<h1>Esaote MRI – ROI Simulator</h1>", unsafe_allow_html=True)


# =============================
# CURRENCY
# =============================
currency_options = {
    "EUR (€)": {"rate": 1.0, "symbol": "€"},
    "USD ($)": {"rate": 1.08, "symbol": "$"},
    "GBP (£)": {"rate": 0.85, "symbol": "£"},
    "JPY (¥)": {"rate": 160.0, "symbol": "¥"},
    "INR (₹)": {"rate": 90.0, "symbol": "₹"},
    "KRW (₩)": {"rate": 1450.0, "symbol": "₩"},
    "VND (₫)": {"rate": 27000.0, "symbol": "₫"},
    "IDR (Rp)": {"rate": 17000.0, "symbol": "Rp"}
}

selected_currency = st.selectbox("Select Currency", list(currency_options.keys()))
exchange_rate = currency_options[selected_currency]["rate"]
currency_symbol = currency_options[selected_currency]["symbol"]


# =============================
# INPUTS
# =============================
years = st.slider("Analysis Period (Years)", 1, 15, 10)
initial_investment = st.number_input("Initial Investment", 0, 20000000000, 500000)

leasing_pct = st.slider("Leasing %", 0, 100, 80)
leas_month = st.slider("Leasing Period (Months)", 12, 120, 60)
interest_pct = st.slider("Interest %", 0, 15, 5)

technology_cost = st.number_input("HR Monthly", 0, 1000000000, 2500) * 12
electricity_cost = st.number_input("Electricity Monthly", 0, 2000000000, 5000) * 12
maintenance_cost = st.number_input("Maintenance Annual", 0, 10000000000, 20000)

reporting_pct = st.slider("Reporting Cost %", 0, 20, 5)

exams_per_day = st.slider("Exams per Day", 1, 30, 12)
working_days = st.slider("Working Days", 1, 365, 200)
average_price = st.number_input("Average Exam Price", 0, 1500000, 500)

annual_revenue = exams_per_day * working_days * average_price
reporting_cost = annual_revenue * reporting_pct / 100


# =============================
# LEASING MODEL
# =============================
leasing_amount = initial_investment * leasing_pct / 100
r_month = (interest_pct / 100) / 12

if r_month > 0 and leas_month > 0:
    monthly_payment = leasing_amount * (
        r_month * (1 + r_month) ** leas_month
    ) / ((1 + r_month) ** leas_month - 1)
else:
    monthly_payment = leasing_amount / max(leas_month, 1)


# =============================
# MODEL
# =============================
@st.cache_data
def calculate_financials(
    years,
    initial_investment,
    annual_revenue,
    technology_cost,
    electricity_cost,
    maintenance_cost,
    reporting_cost,
    monthly_payment,
    leas_month
):

    expenses = [initial_investment]
    revenues = [0]

    cumulative_cost = initial_investment
    cumulative_rev = 0

    for y in range(1, years + 1):

        months_used = min(12, max(0, leas_month - (y - 1) * 12))
        leasing_cost = months_used * monthly_payment

        yearly_cost = (
            technology_cost +
            electricity_cost +
            maintenance_cost +
            leasing_cost +
            reporting_cost
        )

        cumulative_cost += yearly_cost
        cumulative_rev += annual_revenue

        expenses.append(cumulative_cost)
        revenues.append(cumulative_rev)

    df = pd.DataFrame({
        "Year": range(0, years + 1),
        "Expenses": expenses,
        "Revenues": revenues
    })

    df["Profit"] = df["Revenues"] - df["Expenses"]
    return df


df = calculate_financials(
    years,
    initial_investment,
    annual_revenue,
    technology_cost,
    electricity_cost,
    maintenance_cost,
    reporting_cost,
    monthly_payment,
    leas_month
)


# =============================
# KPI
# =============================
final_profit = df["Profit"].iloc[-1]
roi = (final_profit / initial_investment) * 100 if initial_investment else 0


# BREAK-EVEN (SAFE)
break_even = None
for i in range(1, len(df)):
    if df["Profit"].iloc[i] >= 0:
        prev = df["Profit"].iloc[i - 1]
        curr = df["Profit"].iloc[i]

        if curr != prev:
            break_even = df["Year"].iloc[i - 1] + abs(prev) / (abs(curr - prev) + 1e-9)
        else:
            break_even = df["Year"].iloc[i]
        break


# =============================
# DISPLAY
# =============================
st.markdown("## Financial Overview")

display_profit = final_profit * exchange_rate
display_rev = df["Revenues"].iloc[-1] * exchange_rate

c1, c2, c3 = st.columns(3)

c1.metric("Revenue", format_currency(display_rev, currency_symbol, selected_currency))
c2.metric("Profit", format_currency(display_profit, currency_symbol, selected_currency))
c3.metric("ROI", f"{roi:.1f}%")


# =============================
# CHARTS
# =============================
label_expr = f"'{currency_symbol}' + format(datum.value, ',.0f')"

line_chart = alt.Chart(df).transform_fold(
    ["Expenses", "Revenues"],
    as_=["Type", "Value"]
).mark_line().encode(
    x=alt.X("Year:O", title="Year"),
    y=alt.Y(
        "Value:Q",
        axis=alt.Axis(labelExpr=label_expr)
    ),
    color=alt.Color(
        "Type:N",
        scale=alt.Scale(
            domain=["Expenses", "Revenues"],
            range=["red", "green"]
        ),
        legend=alt.Legend(
            orient="none",              # ❗ disattiva posizione standard
            legendX=10,                 # posizione interna
            legendY=10,
            direction="vertical",
            title="Cashflow",
            fillColor="white",          # sfondo leggibile
            strokeColor="lightgray"
        )
    ),
    tooltip=[
        alt.Tooltip("Year:O"),
        alt.Tooltip("Type:N"),
        alt.Tooltip("Value:Q", format=",.0f", title=f"Value ({currency_symbol})")
    ]
)

st.altair_chart(line_chart, use_container_width=True)


profit_chart = alt.Chart(df).mark_bar().encode(
    x="Year:O",
    y="Profit:Q",
    color=alt.condition(
        "datum.Profit >= 0",
        alt.value(ESAOTE_GREEN),
        alt.value("red")
    )
)

st.altair_chart(profit_chart, use_container_width=True)


# =============================
# INSIGHTS
# =============================
trend = df["Profit"].diff().iloc[-3:].mean()

insights = [
    f"ROI: {roi:.1f}%",
    f"Break-even: {'Year ' + str(round(break_even, 1)) if break_even else 'Not reached'}",
    "Trend: " + ("Positive" if trend > 0 else "Negative")
]

st.markdown("## Insights")
for i in insights:
    st.write("•", i)
# =========================================================
# PDF FUNCTION (FIXED + COMPLETE)
# =========================================================
def create_pdf_enterprise():

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

  
    # =====================================================
    # STYLING
    # =====================================================
    title_color = (0.12, 0.12, 0.12)
    grey = (0.4, 0.4, 0.4)
    light_grey = (0.6, 0.6, 0.6)

    # =====================================================
    # HEADER
    # =====================================================
    c.setFont("Helvetica-Bold", 20)
    c.setFillColorRGB(*title_color)
    c.drawString(50, height - 60, "MRI Investment ROI Analysis")

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(*grey)
    c.drawString(150, height - 80, f"Currency: {selected_currency}")

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(*grey)
    c.drawString(50, height - 80, "Financial Report")

# =========================
# DRAW LOGO
# =========================

    # logo
    try:
        r = requests.get(LOGO_URL, timeout=5)
        logo = BytesIO(r.content)
    except:
        logo = None


# =========================
# DRAW LOGO
# =========================
    if logo:
        try:
            c.drawImage(
                ImageReader(logo),
                470,
                height - 60,
                width=70,
                height=18
            )
        except:
            pass

    c.setStrokeColorRGB(0.85, 0.85, 0.85)
    c.line(50, height - 90, 550, height - 90)

    # =====================================================
    # KPI STRIP
    # =====================================================
    def kpi_box(x, y, label, value):
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(*light_grey)
        c.drawString(x, y, label)
    
        c.setFont("Helvetica-Bold", 12)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(x, y - 15, value)
    
    
        # KPI BOXES
        kpi_box(50, height - 130,"Revenue", format_currency(df["Revenues"].iloc[-1], currency_symbol, selected_currency))
        
        kpi_box(200,height - 120,"Profit",format_currency(final_profit, currency_symbol, selected_currency))
        
        kpi_box(350,height - 120,"ROI",f"{roi:.1f}%")
        
        # ✅ FIXED BREAK-EVEN (1 decimal)
        break_even_value = (
            f"Y{break_even:.1f}"
            if break_even is not None
            else "Not reached"
        )
        
        kpi_box(470,height - 120,"Break-even",break_even_value)

    # =====================================================
    # SUMMARY
    # =====================================================
    c.setFont("Helvetica-Bold", 13)
    c.setFillColorRGB(*title_color)
    c.drawString(50, height - 180, "Summary")

    summary_text = [
        f"The MRI investment generates a total ROI of {roi:.1f}%.",
        f"{'Break-even achieved in year ' + str(break_even) if break_even else 'Break-even not achieved within analysis period.'}",
    ]

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(*grey)

    y = height - 200
    for line in summary_text:
        c.drawString(55, y, "• " + line)
        y -= 14

    # =====================================================
    # ASSUMPTIONS
    # =====================================================
    c.setFont("Helvetica-Bold", 13)
    c.setFillColorRGB(*title_color)
    c.drawString(320, height - 180, "Key Assumptions")

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(*grey)

    assumptions = [
        f"Initial Investment: {format_currency(initial_investment, currency_symbol, selected_currency)}",
        f"Exams per Day: {exams_per_day}",
        f"Working Days: {working_days}",
        f"Avg Price: {format_currency(average_price * exchange_rate, currency_symbol, selected_currency)}",
        f"Leasing: {leasing_pct}% over {leas_month} months at {interest_pct}%",
        f"HR Cost: {format_currency(technology_cost, currency_symbol, selected_currency)}",
        f"Electricity: {format_currency(electricity_cost, currency_symbol, selected_currency)}",
        f"Maintenance: {format_currency(maintenance_cost, currency_symbol, selected_currency)}",
    ]

    y = height - 200
    for a in assumptions:
        c.drawString(320, y, "• " + a)
        y -= 14

    # =====================================================
    # PERFORMANCE SECTION
    # =====================================================

    from matplotlib.ticker import FuncFormatter

    def currency_formatter(x, pos):
        return format_currency(x, currency_symbol, selected_currency)

    formatter = FuncFormatter(currency_formatter)

    def fig_to_img(fig):
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        plt.close(fig)
        return buf

    # =============================
    # CHART 1: REVENUE vs COSTS
    # =============================
    fig1, ax1 = plt.subplots(figsize=(6, 2.5))

    ax1.plot(df["Year"], df["Revenues"], label="Revenue", linewidth=2, color="#4daf4a")
    ax1.plot(df["Year"], df["Expenses"], label="Costs", linewidth=2, color="#e41a1c")

    ax1.set_title(f"Revenue vs Costs ({currency_symbol})")

    ax1.yaxis.set_major_formatter(formatter)

    ax1.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)
    ax1.spines[['top', 'right']].set_visible(False)
    ax1.legend(loc="upper left")

    chart1 = fig_to_img(fig1)
    c.drawImage(ImageReader(chart1), 80, 320, width=430, height=200)

    # =============================
    # CHART 2: PROFIT
    # =============================
    fig2, ax2 = plt.subplots(figsize=(6, 2.5))

    colors = ["#2E7D32" if v >= 0 else "#C62828" for v in df["Profit"]]
    ax2.bar(df["Year"], df["Profit"], color=colors)

    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_title(f"Profit Evolution ({currency_symbol})")

    ax2.yaxis.set_major_formatter(formatter)

    ax2.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)
    ax2.spines[['top', 'right']].set_visible(False)

    chart2 = fig_to_img(fig2)
    c.drawImage(ImageReader(chart2), 80, 70, width=430, height=200)

    # =====================================================
    # FOOTER
    # =====================================================
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(*light_grey)
    c.drawString(50, 40, "Confidential – Internal Use Only | Generated MRI ROI Model")

    c.save()
    buffer.seek(0)

    return buffer

# =========================================================
# DOWNLOAD
# =========================================================

if "pdf_report" not in st.session_state:
    st.session_state.pdf_report = None


# =============================
# GENERATE REPORT
# =============================
if st.button("Generate Report"):

    with st.spinner("Building report..."):
        try:
            st.session_state.pdf_report = create_pdf_enterprise()
        except Exception as e:
            st.error(f"Report generation failed: {e}")
            st.session_state.pdf_report = None


# =============================
# DOWNLOAD BUTTON
# =============================
if st.download_button(
    "Download PDF",
    data=create_pdf_enterprise(),
    file_name="MRI_ROI_Report.pdf",
    mime="application/pdf"
):
    pass
