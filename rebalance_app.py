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

# ALOKACJA METALI – Dynamiczna regulacja
st.sidebar.markdown("**Udział metali (%) – zawsze razem 100%**")

metals = ["Gold", "Silver", "Platinum", "Palladium"]
def_init = {"Gold": 40, "Silver": 20, "Platinum": 20, "Palladium": 20}

# Inicjalizacja stanu
for m in metals:
    if f"alloc_{m}" not in st.session_state:
        st.session_state[f"alloc_{m}"] = def_init[m]

# Identyfikacja zmiany
changed = st.session_state.get("last_changed", None)

# Obsługa suwaków
new_alloc = {}
for m in metals:
    def on_change(metal=m):
        st.session_state["last_changed"] = metal

    new_alloc[m] = st.sidebar.slider(
        f"{m} (%)",
        0, 100,
        st.session_state[f"alloc_{m}"],
        key=f"alloc_{m}",
        on_change=on_change
    )

# Przeskalowanie pozostałych metali
if changed:
    remaining = [m for m in metals if m != changed]
    total_remaining = sum(st.session_state[f"alloc_{m}"] for m in remaining)
    leftover = 100 - st.session_state[f"alloc_{changed}"]
    if total_remaining == 0:
        for m in remaining:
            st.session_state[f"alloc_{m}"] = leftover // len(remaining)
    else:
        for m in remaining:
            share = st.session_state[f"alloc_{m}"] / total_remaining
            st.session_state[f"alloc_{m}"] = int(round(share * leftover))

# Finalna alokacja
allocation = {m: st.session_state[f"alloc_{m}"] / 100 for m in metals}

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
storage_metal = st.sidebar.selectbox("Metal do pokrycia kosztów", metals + ["Best this year"])

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

# ... funkcje generate_purchase_dates, simulate, itd. oraz wynik końcowy

def generate_purchase_dates(start_date, freq, day, end_date):
    dates = []
    current = pd.to_datetime(start_date)
    while current <= end_date:
        if freq == "Tygodniowo":
            while current.weekday() != day:
                current += timedelta(days=1)
            dates.append(current)
            current += timedelta(weeks=1)
        elif freq == "Miesięcznie":
            current = current.replace(day=min(day, 28))
            dates.append(current)
            current += pd.DateOffset(months=1)
        elif freq == "Kwartalnie":
            current = current.replace(day=min(day, 28))
            dates.append(current)
            current += pd.DateOffset(months=3)
        else:
            break
    return [data.index[data.index.get_indexer([d], method="nearest")][0] for d in dates if len(data.index.get_indexer([d], method="nearest")) > 0]

def simulate(allocation):
    portfolio = {m: 0.0 for m in allocation}
    history = []
    invested = 0.0
    extra_purchases = 0.0
    all_dates = data.loc[initial_date:].index
    purchase_dates = generate_purchase_dates(initial_date, purchase_freq, purchase_day, all_dates[-1])

    def apply_rebalance(d, label):
        prices = data.loc[d]
        total_value = sum(prices[m + "_EUR"] * portfolio[m] for m in allocation)
        target_value = {m: total_value * allocation[m] for m in allocation}
        for metal in allocation:
            current_value = prices[metal + "_EUR"] * portfolio[metal]
            diff = current_value - target_value[metal]
            if diff > 0:
                sell_price = prices[metal + "_EUR"] * (1 - sell_fees[metal] / 100)
                grams_to_sell = min(diff / sell_price, portfolio[metal])
                portfolio[metal] -= grams_to_sell
                cash = grams_to_sell * sell_price
                for buy_metal in allocation:
                    needed_value = target_value[buy_metal] - prices[buy_metal + "_EUR"] * portfolio[buy_metal]
                    if needed_value > 0:
                        buy_price = prices[buy_metal + "_EUR"] * (1 + rebuy_markup / 100)
                        buy_grams = min(cash / buy_price, needed_value / buy_price)
                        portfolio[buy_metal] += buy_grams
                        cash -= buy_grams * buy_price
        return label

    initial_ts = data.index[data.index.get_indexer([pd.to_datetime(initial_date)], method="nearest")][0]
    prices = data.loc[initial_ts]
    for metal, percent in allocation.items():
        price = prices[metal + "_EUR"] * (1 + margins[metal] / 100)
        grams = (initial_allocation * percent) / price
        portfolio[metal] += grams
    invested += initial_allocation
    history.append((initial_ts, invested, extra_purchases, dict(portfolio), "initial"))

    for d in all_dates:
        actions = []
        if d in purchase_dates:
            prices = data.loc[d]
            for metal, percent in allocation.items():
                price = prices[metal + "_EUR"] * (1 + margins[metal] / 100)
                grams = (purchase_amount * percent) / price
                portfolio[metal] += grams
            invested += purchase_amount
            extra_purchases += purchase_amount
            actions.append("recurring")

        if rebalance_1 and d >= pd.to_datetime(rebalance_1_start) and d.month == rebalance_1_start.month and d.day == rebalance_1_start.day:
            actions.append(apply_rebalance(d, "rebalance_1"))

        if rebalance_2 and d >= pd.to_datetime(rebalance_2_start) and d.month == rebalance_2_start.month and d.day == rebalance_2_start.day:
            actions.append(apply_rebalance(d, "rebalance_2"))

        if d.month == 12 and d.day == 31:
            cost_eur = invested * (storage_fee / 100) * (1 + vat / 100)
            prices = data.loc[d]
            if storage_metal == "Best this year":
                year_prices = data[str(d.year)]
                growth = {m: (year_prices[m + "_EUR"].iloc[-1] / year_prices[m + "_EUR"].iloc[0]) for m in allocation}
                metal = max(growth, key=growth.get)
            else:
                metal = storage_metal
            metal_price = prices[metal + "_EUR"]
            grams_to_sell = cost_eur / metal_price
            portfolio[metal] = max(0, portfolio[metal] - grams_to_sell)
            actions.append("storage")

        history.append((d, invested, extra_purchases, dict(portfolio), ", ".join(actions)))

    df_result = pd.DataFrame([{
        "Date": h[0],
        "Invested": h[1],
        "Dokupy": h[2],
        **{m: h[3][m] for m in allocation},
        "Portfolio Value": sum(data.loc[h[0]][m + "_EUR"] * h[3][m] for m in allocation),
        "Akcja": h[4]
    } for h in history]).set_index("Date")
    return df_result

# Główna sekcja aplikacji
st.title("Symulator ReBalancingu Portfela Metali Szlachetnych")
st.markdown("---")
result = simulate(allocation)
st.line_chart(result[["Portfolio Value", "Invested"]])
st.dataframe(result.tail(20))
