import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Wczytanie danych cenowych
@st.cache_data
def load_data():
    df = pd.read_csv("lbma_data.csv", parse_dates=True, index_col=0)
    df = df.sort_index()
    df = df.dropna()
    return df

data = load_data()

# SIDEBAR: Parametry użytkownika
st.sidebar.header("Parametry Symulacji")

# KWOTY I DATA STARTU
st.sidebar.subheader("💰 Kwoty i daty startowe")
initial_allocation = st.sidebar.number_input("Kwota początkowej alokacji (EUR)", value=10000.0, step=100.0)
initial_date = st.sidebar.date_input("Data pierwszego zakupu", value=datetime(2000, 1, 1), min_value=data.index.min().date(), max_value=data.index.max().date())

# ALOKACJA METALI Z WALIDACJĄ I RESETEM
st.sidebar.markdown("**Udział metali (%) – suma musi wynosić dokładnie 100%**")

if "default_allocation" not in st.session_state:
    st.session_state.default_allocation = {
        "Gold": 40,
        "Silver": 20,
        "Platinum": 20,
        "Palladium": 20
    }

if st.sidebar.button("🔄 Resetuj do 40/20/20/20"):
    st.session_state.default_allocation = {
        "Gold": 40,
        "Silver": 20,
        "Platinum": 20,
        "Palladium": 20
    }

allocation_gold = st.sidebar.slider("Złoto (Au)", 0, 100, st.session_state.default_allocation["Gold"])
allocation_silver = st.sidebar.slider("Srebro (Ag)", 0, 100, st.session_state.default_allocation["Silver"])
allocation_platinum = st.sidebar.slider("Platyna (Pt)", 0, 100, st.session_state.default_allocation["Platinum"])
allocation_palladium = st.sidebar.slider("Pallad (Pd)", 0, 100, st.session_state.default_allocation["Palladium"])

total = allocation_gold + allocation_silver + allocation_platinum + allocation_palladium
if total != 100:
    st.sidebar.error(f"Suma alokacji: {total}% – musi wynosić dokładnie 100%, aby kontynuować.")
    st.stop()

allocation = {
    "Gold": allocation_gold / 100,
    "Silver": allocation_silver / 100,
    "Platinum": allocation_platinum / 100,
    "Palladium": allocation_palladium / 100
}

# DOKUPY
st.sidebar.subheader("🔁 Zakupy cykliczne")
purchase_freq = st.sidebar.selectbox("Periodyczność zakupów", ["Brak", "Tygodniowo", "Miesięcznie", "Kwartalnie"])
if purchase_freq == "Tygodniowo":
    purchase_day = st.sidebar.selectbox("Dzień tygodnia zakupu (0=pon, 6=niedz)", list(range(7)))
elif purchase_freq == "Miesięcznie":
    purchase_day = st.sidebar.number_input("Dzień miesiąca zakupu", min_value=1, max_value=28, value=15)
elif purchase_freq == "Kwartalnie":
    purchase_day = st.sidebar.number_input("Dzień kwartału zakupu (dzień w pierwszym miesiącu kwartału)", min_value=1, max_value=28, value=15)
else:
    purchase_day = None

purchase_amount = st.sidebar.number_input("Kwota dokupu (EUR)", value=0.0, step=100.0)

# REBALANCING
st.sidebar.subheader("♻️ ReBalancing")
rebalance_1 = st.sidebar.checkbox("ReBalancing 1")
rebalance_1_start = st.sidebar.date_input("Start ReBalancing 1", value=datetime(2005, 1, 1))
rebalance_2 = st.sidebar.checkbox("ReBalancing 2")
rebalance_2_start = st.sidebar.date_input("Start ReBalancing 2", value=datetime(2010, 1, 1))

# KOSZTY
st.sidebar.subheader("📦 Koszty magazynowania")
storage_fee = st.sidebar.number_input("Roczny koszt magazynowania (%)", value=1.5)
vat = st.sidebar.number_input("VAT (%)", value=19.0)
storage_metal = st.sidebar.selectbox("Metal do pokrycia kosztów", ["Gold", "Silver", "Platinum", "Palladium", "Best this year"])

# MARŻe I PROWIZJE
st.sidebar.subheader("📊 Marże i prowizje")
margins = {
    "Gold": st.sidebar.number_input("Marża Gold (%)", value=15.6),
    "Silver": st.sidebar.number_input("Marża Silver (%)", value=18.36),
    "Platinum": st.sidebar.number_input("Marża Platinum (%)", value=24.24),
    "Palladium": st.sidebar.number_input("Marża Palladium (%)", value=22.49)
}
sell_fees = {"Gold": 1.5, "Silver": 3.0, "Platinum": 3.0, "Palladium": 3.0}
rebuy_markup = 6.5

# ... (pozostała część symulacji pozostaje bez zmian)

# Główna sekcja aplikacji
st.title("Symulator ReBalancingu Portfela Metali Szlachetnych")
st.markdown("---")
result = simulate(allocation)
st.line_chart(result[["Portfolio Value", "Invested"]])
st.dataframe(result.tail(20))
