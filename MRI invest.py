v
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

    # logo
    logo = load_logo()
    if logo:
        try:
            c.drawImage(ImageReader(logo), 470, height - 60, width=70, height=18)
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

    kpi_box(50, height - 130, "Revenue",
            format_currency(df["Revenues"].iloc[-1], currency_symbol, selected_currency))

    kpi_box(200, height - 120, "Profit",
            format_currency(final_profit, currency_symbol, selected_currency))

    kpi_box(350, height - 120, "ROI",
            f"{roi:.1f}%")

    kpi_box(470, height - 120, "Break-even",
            f"Y{break_even}" if break_even else "Not reached")

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

if st.button("Generate Report"):

    with st.spinner("Building report..."):
        st.session_state.pdf_report = create_pdf_enterprise()

if st.session_state.pdf_report:

    st.download_button(
        "Download  PDF",
        data=st.session_state.pdf_report,
        file_name="MRI_ROI_Report.pdf",
        mime="application/pdf"
    )
