
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
initial_allocation = st.sidebar.number_input("Kwota początkowej alokacji (EUR)", value=10000.0, step=100.0)
initial_date = st.sidebar.date_input("Data pierwszego zakupu", value=datetime(2000, 1, 1), min_value=data.index.min().date(), max_value=data.index.max().date())

purchase_freq = st.sidebar.selectbox("Periodyczność zakupów", ["Brak", "Tygodniowo", "Miesięcznie", "Kwartalnie"])
purchase_day = st.sidebar.number_input("Dzień zakupów (dzień tygodnia/miesiąca/kwartału)", min_value=1, max_value=31, value=15)
purchase_amount = st.sidebar.number_input("Kwota dokupu miesięcznego (EUR)", value=0.0, step=100.0)

rebalance_1 = st.sidebar.checkbox("ReBalancing 1")
rebalance_1_start = st.sidebar.date_input("Start ReBalancing 1", value=datetime(2005, 1, 1))
rebalance_2 = st.sidebar.checkbox("ReBalancing 2")
rebalance_2_start = st.sidebar.date_input("Start ReBalancing 2", value=datetime(2010, 1, 1))

storage_fee = st.sidebar.number_input("Roczny koszt magazynowania (%)", value=1.5)
vat = st.sidebar.number_input("VAT (%)", value=19.0)
storage_metal = st.sidebar.selectbox("Metal do pokrycia kosztów", ["Gold", "Silver", "Platinum", "Palladium", "Best this year"])

# Marże
st.sidebar.markdown("---")
st.sidebar.subheader("Marże i prowizje")
margins = {
    "Gold": st.sidebar.number_input("Marża Gold (%)", value=15.6),
    "Silver": st.sidebar.number_input("Marża Silver (%)", value=18.36),
    "Platinum": st.sidebar.number_input("Marża Platinum (%)", value=24.24),
    "Palladium": st.sidebar.number_input("Marża Palladium (%)", value=22.49)
}
sell_fees = {"Gold": 1.5, "Silver": 3.0, "Platinum": 3.0, "Palladium": 3.0}
rebuy_markup = 6.5

# Główna sekcja
st.title("Symulator ReBalancingu Portfela Metali Szlachetnych")
st.markdown("""
Aplikacja symuluje rozwój portfela metali szlachetnych (Au/Ag/Pt/Pd) w oparciu o zakupy, ReBalancing i koszty magazynowania.
---
""")

# Placeholder na wykres i tabelę
st.info("Symulacja i wizualizacja będą dostępne w kolejnych krokach implementacji.")
