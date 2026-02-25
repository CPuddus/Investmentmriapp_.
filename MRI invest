import streamlit as st
import pandas as pd
import numpy as np
import altair as alt


st.title("Calcolatore ROI Interattivo")

anni = st.slider("Numero di anni", 1, 15, 5)

# Costi
investimento = st.number_input("Investimento iniziale (€)", min_value=0.0, value=500000.0, step=10000.0)
radio = st.number_input("Costo tech and reporting (1y)", min_value=0.0, value=50000.0, step=5000.0)
electrical_cost = st.number_input("Costo elettricità (1y)", min_value=0.0, value=20000.0, step=2000.0)
maintenance = st.number_input("yearly average Service cost (1y)", min_value=0.0, value=20000.0, step=5000.0)

# Guadagni
Num_esami = st.slider("Numero di esami al giorno", 1, 25, 5)
Giorni= st.slider("Numero giorni lavorativi per anno", 1, 20, 365)
Price = st.slider("Prezzo_esame (al giorno)", 1, 20, 1000)
Guadagno = Num_esami*Price*Giorni;

# Calcolo costo anno per anno
spese = [0]
ricavi = [0]
rad=0
serv=0
power_cost=0
Income=0
for anno in range(1, anni + 1):
    rad = (rad + radio)
    power_cost = (power_cost + electrical_cost)
    service= (maintenance + serv)
    Income= (Income+Guadagno)
    spese.append(investimento+(rad+ power_cost))
    ricavi.append(Income)


st.subheader(f" Costi in {anni} anni: ")
st.write("Costi anno per anno (€):")
st.write(spese)
st.subheader(f" Ricavo in {anni} anni: ")
st.write("Ricavo anno per anno (€):")
st.write(ricavi)


df = pd.DataFrame({
    "Anno": range(0, anni + 1),
    "Spese": spese,
    "Ricavi": ricavi
})

# =============================
# CALCOLI AGGIUNTIVI
# =============================

df["Profitto"] = df["Ricavi"] - df["Spese"]

# Calcolo anno di break-even, escludendo anno 0
breakeven_year = None
for i in range(1, len(df)):
    if df["Profitto"][i] >= 0:
        breakeven_year = df["Anno"][i]
        break

st.subheader("Dashboard ROI Completa con Break-even e Tooltip Unico")

# =============================
# BARRE AFFIANCATE
# =============================

df_melted = df.melt(
    id_vars="Anno",
    value_vars=["Spese", "Ricavi"],
    var_name="Categoria",
    value_name="Valore"
)

bars = alt.Chart(df_melted).mark_bar(
    opacity=0.4,
    size=35
).encode(
    x=alt.X("Anno:O", title="Anno"),
    y=alt.Y("Valore:Q", title="Euro (€)"),
    color=alt.Color(
        "Categoria:N",
        scale=alt.Scale(
            domain=["Spese", "Ricavi"],
            range=["#d62728", "#2ca02c"]
        ),
        legend=alt.Legend(title="Barre")
    ),
    xOffset="Categoria:N"
)

# =============================
# LINEE
# =============================

df_lines = df.melt(
    id_vars="Anno",
    value_vars=["Spese", "Ricavi", "Profitto"],
    var_name="Linea",
    value_name="Valore"
)

lines = alt.Chart(df_lines).mark_line(strokeWidth=3).encode(
    x="Anno:O",
    y="Valore:Q",
    color=alt.Color(
        "Linea:N",
        scale=alt.Scale(
            domain=["Spese", "Ricavi", "Profitto"],
            range=["#b2182b", "#1b7837", "#2166ac"]
        ),
        legend=alt.Legend(title="Linee")
    )
)

# =============================
# TOOLTIP UNICO PER OGNI ANNO
# =============================

tooltip = alt.Chart(df).mark_point(opacity=0).encode(
    x="Anno:O",
    y="Profitto:Q",
    tooltip=[
        alt.Tooltip("Anno:O", title="Anno"),
        alt.Tooltip("Ricavi:Q", title="Ricavi (€)"),
        alt.Tooltip("Spese:Q", title="Spese (€)"),
        alt.Tooltip("Profitto:Q", title="Profitto (€)")
    ]
)

# Punto break-even
breakeven_point = None
if breakeven_year is not None:
    breakeven_point = alt.Chart(df[df["Anno"]==breakeven_year]).mark_circle(
        size=250,
        color="gold"
    ).encode(
        x="Anno:O",
        y="Profitto:Q",
        tooltip=[
            alt.Tooltip("Anno:O", title="Anno"),
            alt.Tooltip("Profitto:Q", title="Profitto (€)"),
            alt.Tooltip("Ricavi:Q", title="Ricavi (€)"),
            alt.Tooltip("Spese:Q", title="Spese (€)")
        ]
    )

# =============================
# LINEA BREAK-EVEN ORIZZONTALE
# =============================

break_even_line = alt.Chart(pd.DataFrame({"y":[0]})).mark_rule(
    strokeDash=[6,6],
    color="black"
).encode(y="y:Q")

# =============================
# GRAFICO FINALE
# =============================

if breakeven_point is not None:
    final_chart = bars + lines + break_even_line + breakeven_point + tooltip
else:
    final_chart = bars + lines + break_even_line + tooltip

st.altair_chart(
    final_chart.properties(
        width=900,
        height=500,
        title="Analisi Completa ROI con Break-even e Tooltip Unico"
    ),
    use_container_width=True
)

# =============================
# MESSAGGIO BREAK EVEN
# =============================

if breakeven_year is not None:
    st.success(f"✅ Break-even raggiunto nell'anno {breakeven_year}")
else:
    st.warning("⚠️ Break-even non raggiunto nel periodo selezionato")
