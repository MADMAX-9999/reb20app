import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =========================================
# 1. Wczytanie danych
# =========================================

@st.cache_data
def load_data():
    df = pd.read_csv("lbma_data.csv", parse_dates=True, index_col=0)
    df = df.sort_index()
    df = df.dropna()
    return df

data = load_data()

# =========================================
# 2. Sidebar: Parametry użytkownika
# =========================================

st.sidebar.header("⚙️ Parametry Symulacji")

# Inwestycja: Kwoty i daty
st.sidebar.subheader("💰 Inwestycja: Kwoty i daty")

# Aktualna data
today = datetime.today().date()

# Domyślna data startu: 20 lat temu
default_initial_date = today.replace(year=today.year - 20)

# Kwota początkowej alokacji
initial_allocation = st.sidebar.number_input(
    "Kwota początkowej alokacji (EUR)",
    value=100000.0,
    step=100.0
)

# Data pierwszego zakupu
initial_date = st.sidebar.date_input(
    "Data pierwszego zakupu",
    value=default_initial_date,
    min_value=data.index.min().date(),
    max_value=data.index.max().date()
)

# Maksymalna możliwa data ostatniego zakupu: 7 lat od daty startu lub ostatnia dostępna data historyczna
max_end_date_limit = min(
    (datetime.combine(initial_date, datetime.min.time()) + timedelta(days=365 * 7)).date(),
    data.index.max().date()
)

# Data ostatniego zakupu
end_purchase_date = st.sidebar.date_input(
    "Data ostatniego zakupu",
    value=today,
    min_value=initial_date,
    max_value=max_end_date_limit
)

# Ostrzeżenie, jeśli okres inwestycji krótszy niż 1 rok
investment_duration_days = (end_purchase_date - initial_date).days

if investment_duration_days < 365:
    st.warning(f"⚠️ Uwaga: Okres inwestowania wynosi tylko {investment_duration_days} dni! Zalecamy inwestowanie przez co najmniej 1 rok dla pełnego efektu systematycznego budowania majątku.")

# ⬆️ KONIEC NOWEGO KODU ⬆️

# Alokacja metali
st.sidebar.subheader("⚖️ Alokacja metali szlachetnych (%)")

for metal, default in {"Gold": 40, "Silver": 20, "Platinum": 20, "Palladium": 20}.items():
    if f"alloc_{metal}" not in st.session_state:
        st.session_state[f"alloc_{metal}"] = default

if st.sidebar.button("🔄 Resetuj do 40/20/20/20"):
    st.session_state["alloc_Gold"] = 40
    st.session_state["alloc_Silver"] = 20
    st.session_state["alloc_Platinum"] = 20
    st.session_state["alloc_Palladium"] = 20
    st.rerun()

allocation_gold = st.sidebar.slider("Złoto (Au)", 0, 100, key="alloc_Gold")
allocation_silver = st.sidebar.slider("Srebro (Ag)", 0, 100, key="alloc_Silver")
allocation_platinum = st.sidebar.slider("Platyna (Pt)", 0, 100, key="alloc_Platinum")
allocation_palladium = st.sidebar.slider("Pallad (Pd)", 0, 100, key="alloc_Palladium")

total = allocation_gold + allocation_silver + allocation_platinum + allocation_palladium
if total != 100:
    st.title("Symulator ReBalancingu Portfela Metali Szlachetnych")
    st.error(f"❗ Suma alokacji: {total}% – musi wynosić dokładnie 100%, aby kontynuować.")
    st.stop()

allocation = {
    "Gold": allocation_gold / 100,
    "Silver": allocation_silver / 100,
    "Platinum": allocation_platinum / 100,
    "Palladium": allocation_palladium / 100
}

# Zakupy cykliczne
st.sidebar.subheader("🔁 Zakupy cykliczne")

purchase_freq = st.sidebar.selectbox("Periodyczność zakupów", ["Brak", "Tydzień", "Miesiąc", "Kwartał"], index=1)

if purchase_freq == "Tydzień":
    days_of_week = ["Poniedziałek", "Wtorek", "Środa", "Czwartek", "Piątek"]
    selected_day = st.sidebar.selectbox("Dzień tygodnia zakupu", days_of_week, index=0)
    purchase_day = days_of_week.index(selected_day)
    default_purchase_amount = 250.0
elif purchase_freq == "Miesiąc":
    purchase_day = st.sidebar.number_input("Dzień miesiąca zakupu (1–28)", min_value=1, max_value=28, value=1)
    default_purchase_amount = 1000.0
elif purchase_freq == "Kwartał":
    purchase_day = st.sidebar.number_input("Dzień kwartału zakupu (1–28)", min_value=1, max_value=28, value=1)
    default_purchase_amount = 3250.0
else:
    purchase_day = None
    default_purchase_amount = 0.0

purchase_amount = st.sidebar.number_input("Kwota dokupu (EUR)", value=default_purchase_amount, step=50.0)

# ReBalancing
st.sidebar.subheader("♻️ ReBalancing")

# Domyślne daty ReBalancingu bazujące na dacie pierwszego zakupu
rebalance_base_year = initial_date.year + 1

rebalance_1_default = datetime(rebalance_base_year, 4, 1)
rebalance_2_default = datetime(rebalance_base_year, 10, 1)

# ReBalancing 1
rebalance_1 = st.sidebar.checkbox("ReBalancing 1", value=True)
rebalance_1_condition = st.sidebar.checkbox("Warunek odchylenia wartości dla ReBalancing 1", value=False)
rebalance_1_threshold = st.sidebar.number_input(
    "Próg odchylenia (%) dla ReBalancing 1", min_value=0.0, max_value=100.0, value=12.0, step=0.5
)

rebalance_1_start = st.sidebar.date_input(
    "Start ReBalancing 1",
    value=rebalance_1_default.date(),
    min_value=data.index.min().date(),
    max_value=data.index.max().date()
)


# ReBalancing 2
rebalance_2 = st.sidebar.checkbox("ReBalancing 2", value=False)
rebalance_2_condition = st.sidebar.checkbox("Warunek odchylenia wartości dla ReBalancing 2", value=False)
rebalance_2_threshold = st.sidebar.number_input(
    "Próg odchylenia (%) dla ReBalancing 2", min_value=0.0, max_value=100.0, value=12.0, step=0.5
)

rebalance_2_start = st.sidebar.date_input(
    "Start ReBalancing 2",
    value=rebalance_2_default.date(),
    min_value=data.index.min().date(),
    max_value=data.index.max().date()
)

# Koszty magazynowania
st.sidebar.subheader("📦 Koszty magazynowania")

storage_fee = st.sidebar.number_input("Roczny koszt magazynowania (%)", value=1.5)
vat = st.sidebar.number_input("VAT (%)", value=19.0)
storage_metal = st.sidebar.selectbox(
    "Metal do pokrycia kosztów",
    ["Gold", "Silver", "Platinum", "Palladium", "Best of year", "ALL"]
)

# Marże i prowizje
st.sidebar.subheader("📊 Marże i prowizje")

margins = {
    "Gold": st.sidebar.number_input("Marża Gold (%)", value=15.6),
    "Silver": st.sidebar.number_input("Marża Silver (%)", value=18.36),
    "Platinum": st.sidebar.number_input("Marża Platinum (%)", value=24.24),
    "Palladium": st.sidebar.number_input("Marża Palladium (%)", value=22.49)
}

# Ceny odkupu
st.sidebar.subheader("💵 Ceny odkupu metali od ceny SPOT (-%)")

buyback_discounts = {
    "Gold": st.sidebar.number_input("Złoto odk. od SPOT (%)", value=-1.5, step=0.1),
    "Silver": st.sidebar.number_input("Srebro odk. od SPOT (%)", value=-3.0, step=0.1),
    "Platinum": st.sidebar.number_input("Platyna odk. od SPOT (%)", value=-3.0, step=0.1),
    "Palladium": st.sidebar.number_input("Pallad odk. od SPOT (%)", value=-3.0, step=0.1)
}

# Ceny ReBalancing
st.sidebar.subheader("♻️ Ceny ReBalancing metali (%)")

rebalance_markup = {
    "Gold": st.sidebar.number_input("Złoto ReBalancing (%)", value=6.5, step=0.1),
    "Silver": st.sidebar.number_input("Srebro ReBalancing (%)", value=6.5, step=0.1),
    "Platinum": st.sidebar.number_input("Platyna ReBalancing (%)", value=6.5, step=0.1),
    "Palladium": st.sidebar.number_input("Pallad ReBalancing (%)", value=6.5, step=0.1)
}

# =========================================
# 3. Funkcje pomocnicze (rozbudowane)
# =========================================

def generate_purchase_dates(start_date, freq, day, end_date):
    dates = []
    current = pd.to_datetime(start_date)
    while current <= end_date:
        if freq == "Tydzień":
            while current.weekday() != day:
                current += timedelta(days=1)
            dates.append(current)
            current += timedelta(weeks=1)
        elif freq == "Miesiąc":
            current = current.replace(day=min(day, 28))
            dates.append(current)
            current += pd.DateOffset(months=1)
        elif freq == "Kwartał":
            current = current.replace(day=min(day, 28))
            dates.append(current)
            current += pd.DateOffset(months=3)
        else:
            break
    return [data.index[data.index.get_indexer([d], method="nearest")][0] for d in dates if len(data.index.get_indexer([d], method="nearest")) > 0]

def find_best_metal_of_year(start_date, end_date):
    start_prices = data.loc[start_date]
    end_prices = data.loc[end_date]
    growth = {}
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
        growth[metal] = (end_prices[metal + "_EUR"] / start_prices[metal + "_EUR"]) - 1
    return max(growth, key=growth.get)



def simulate(allocation):
    portfolio = {m: 0.0 for m in allocation}
    history = []
    invested = 0.0
    all_dates = data.loc[initial_date:].index
    purchase_dates = generate_purchase_dates(initial_date, purchase_freq, purchase_day, all_dates[-1])

    last_year = None


    
    def apply_rebalance(d, label, condition_enabled, threshold_percent):
        prices = data.loc[d]
        total_value = sum(prices[m + "_EUR"] * portfolio[m] for m in allocation)

        if total_value == 0:
            return f"rebalancing_skipped_{label}"

        # Aktualne udziały procentowe każdego metalu
        current_shares = {
            m: (prices[m + "_EUR"] * portfolio[m]) / total_value
            for m in allocation
        }

        # Sprawdzenie czy którykolwiek metal przekracza próg odchylenia
        rebalance_trigger = False
        for metal in allocation:
            deviation = abs(current_shares[metal] - allocation[metal]) * 100  # w %
            if deviation >= threshold_percent:
                rebalance_trigger = True
                break  # wystarczy jedno przekroczenie

        if condition_enabled and not rebalance_trigger:
            return f"rebalancing_skipped_{label}"

        # Wykonaj ReBalancing
        target_value = {m: total_value * allocation[m] for m in allocation}

        for metal in allocation:
            current_value = prices[metal + "_EUR"] * portfolio[metal]
            diff = current_value - target_value[metal]

            if diff > 0:
                # Sprzedaj nadwyżkę po cenie odkupu (SPOT minus rabat)
                sell_price = prices[metal + "_EUR"] * (1 + buyback_discounts[metal] / 100)
                grams_to_sell = min(diff / sell_price, portfolio[metal])
                portfolio[metal] -= grams_to_sell
                cash = grams_to_sell * sell_price

                # Kupuj metale poniżej celu po cenach ReBalancingu (SPOT plus narzut)
                for buy_metal in allocation:
                    needed_value = target_value[buy_metal] - prices[buy_metal + "_EUR"] * portfolio[buy_metal]
                    if needed_value > 0:
                        buy_price = prices[buy_metal + "_EUR"] * (1 + rebalance_markup[buy_metal] / 100)
                        buy_grams = min(cash / buy_price, needed_value / buy_price)
                        portfolio[buy_metal] += buy_grams
                        cash -= buy_grams * buy_price
                        if cash <= 0:
                            break  # skończyła się gotówka

        return label

    # Początkowy zakup
    initial_ts = data.index[data.index.get_indexer([pd.to_datetime(initial_date)], method="nearest")][0]
    prices = data.loc[initial_ts]
    for metal, percent in allocation.items():
        price = prices[metal + "_EUR"] * (1 + margins[metal] / 100)
        grams = (initial_allocation * percent) / price
        portfolio[metal] += grams
    invested += initial_allocation
    history.append((initial_ts, invested, dict(portfolio), "initial"))

    for d in all_dates:
        actions = []

        if d in purchase_dates:
            prices = data.loc[d]
            for metal, percent in allocation.items():
                price = prices[metal + "_EUR"] * (1 + margins[metal] / 100)
                grams = (purchase_amount * percent) / price
                portfolio[metal] += grams
            invested += purchase_amount
            actions.append("recurring")

        if rebalance_1 and d >= pd.to_datetime(rebalance_1_start) and d.month == rebalance_1_start.month and d.day == rebalance_1_start.day:
            actions.append(apply_rebalance(d, "rebalance_1", rebalance_1_condition, rebalance_1_threshold))

        if rebalance_2 and d >= pd.to_datetime(rebalance_2_start) and d.month == rebalance_2_start.month and d.day == rebalance_2_start.day:
            actions.append(apply_rebalance(d, "rebalance_2", rebalance_2_condition, rebalance_2_threshold))

        if last_year is None:
            last_year = d.year

        if d.year != last_year:
            last_year_end = data.loc[data.index[data.index.year == last_year]].index[-1]
            storage_cost = invested * (storage_fee / 100) * (1 + vat / 100)
            prices_end = data.loc[last_year_end]

            if storage_metal == "Best of year":
                metal_to_sell = find_best_metal_of_year(
                    data.index[data.index.year == last_year][0],
                    data.index[data.index.year == last_year][-1]
                )
                sell_price = prices_end[metal_to_sell + "_EUR"] * (1 + buyback_discounts[metal_to_sell] / 100)
                grams_needed = storage_cost / sell_price
                grams_needed = min(grams_needed, portfolio[metal_to_sell])
                portfolio[metal_to_sell] -= grams_needed

            elif storage_metal == "ALL":
                total_value = sum(prices_end[m + "_EUR"] * portfolio[m] for m in allocation)
                for metal in allocation:
                    share = (prices_end[metal + "_EUR"] * portfolio[metal]) / total_value
                    cash_needed = storage_cost * share
                    sell_price = prices_end[metal + "_EUR"] * (1 + buyback_discounts[metal] / 100)
                    grams_needed = cash_needed / sell_price
                    grams_needed = min(grams_needed, portfolio[metal])
                    portfolio[metal] -= grams_needed

            else:
                sell_price = prices_end[storage_metal + "_EUR"] * (1 + buyback_discounts[storage_metal] / 100)
                grams_needed = storage_cost / sell_price
                grams_needed = min(grams_needed, portfolio[storage_metal])
                portfolio[storage_metal] -= grams_needed

            history.append((last_year_end, invested, dict(portfolio), "storage_fee"))
            last_year = d.year

        if actions:
            history.append((d, invested, dict(portfolio), ", ".join(actions)))

    df_result = pd.DataFrame([{
    "Date": h[0],
    "Invested": h[1],
    **{m: h[2][m] for m in allocation},
    "Portfolio Value": sum(
        data.loc[h[0]][m + "_EUR"] * (1 + buyback_discounts[m] / 100) * h[2][m]
        for m in allocation
    ),
    "Akcja": h[3]
} for h in history]).set_index("Date")

    return df_result

# =========================================
# 4. Główna sekcja aplikacji
# =========================================

st.title("Symulator ReBalancingu Portfela Metali Szlachetnych")
st.markdown("---")

result = simulate(allocation)

import matplotlib.pyplot as plt

# 📈 Wykres wartości portfela, inwestycji i kosztów magazynowania

# Przygotowanie danych do wykresu
result_plot = result.copy()
result_plot["Storage Cost"] = 0.0

# Oznaczenie kosztu magazynowania w odpowiednich dniach
storage_costs = result_plot[result_plot["Akcja"] == "storage_fee"].index
for d in storage_costs:
    result_plot.at[d, "Storage Cost"] = result_plot.at[d, "Invested"] * (storage_fee / 100) * (1 + vat / 100)

# Wykres
st.line_chart(result_plot[["Portfolio Value", "Invested", "Storage Cost"]])


    
# Podsumowanie wyników

st.subheader("📊 Podsumowanie inwestycji")
start_date = result.index.min()
end_date = result.index.max()
years = (end_date - start_date).days / 365.25

alokacja_kapitalu = result["Invested"].max()
wartosc_metali = result["Portfolio Value"].iloc[-1]

if alokacja_kapitalu > 0 and years > 0:
    roczny_procent = (wartosc_metali / alokacja_kapitalu) ** (1 / years) - 1
else:
    roczny_procent = 0.0


st.subheader("📊 Wzrost cen metali od startu inwestycji")

start_date = result.index.min()
end_date = result.index.max()

start_prices = data.loc[start_date]
end_prices = data.loc[end_date]

metale = ["Gold", "Silver", "Platinum", "Palladium"]
wzrosty = {}

for metal in metale:
    start_price = start_prices[metal + "_EUR"]
    end_price = end_prices[metal + "_EUR"]
    wzrost = (end_price / start_price - 1) * 100
    wzrosty[metal] = wzrost

# Wyświetlenie ładnej tabelki
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Złoto (Au)", f"{wzrosty['Gold']:.2f}%")
with col2:
    st.metric("Srebro (Ag)", f"{wzrosty['Silver']:.2f}%")
with col3:
    st.metric("Platyna (Pt)", f"{wzrosty['Platinum']:.2f}%")
with col4:
    st.metric("Pallad (Pd)", f"{wzrosty['Palladium']:.2f}%")



st.subheader("⚖️ Aktualnie posiadane ilości metali (g)")

# Aktualne ilości gramów z ostatniego dnia
aktualne_ilosci = {
    "Gold": result.iloc[-1]["Gold"],
    "Silver": result.iloc[-1]["Silver"],
    "Platinum": result.iloc[-1]["Platinum"],
    "Palladium": result.iloc[-1]["Palladium"]
}

# Kolory metali: złoto, srebro, platyna, pallad
kolory_metali = {
    "Gold": "#D4AF37",      # złoto – kolor złoty
    "Silver": "#C0C0C0",    # srebro – kolor srebrny
    "Platinum": "#E5E4E2",  # platyna – bardzo jasny, biały odcień
    "Palladium": "#CED0DD"  # pallad – lekko niebieskawo-srebrny
}

# Wyświetlenie w czterech kolumnach z kolorowym napisem
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"<h4 style='color:{kolory_metali['Gold']}; text-align: center;'>Złoto (Au)</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci['Gold']:.2f} g")
with col2:
    st.markdown(f"<h4 style='color:{kolory_metali['Silver']}; text-align: center;'>Srebro (Ag)</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci['Silver']:.2f} g")
with col3:
    st.markdown(f"<h4 style='color:{kolory_metali['Platinum']}; text-align: center;'>Platyna (Pt)</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci['Platinum']:.2f} g")
with col4:
    st.markdown(f"<h4 style='color:{kolory_metali['Palladium']}; text-align: center;'>Pallad (Pd)</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci['Palladium']:.2f} g")

st.metric("💶 Alokacja kapitału", f"{alokacja_kapitalu:,.2f} EUR")
st.metric("📦 Wycena sprzedażowa metali", f"{wartosc_metali:,.2f} EUR")

# 🛒 Wartość zakupu metali dziś (uwzględniając aktualne ceny + marże)
metale = ["Gold", "Silver", "Platinum", "Palladium"]

# Ilość posiadanych gramów na dziś
ilosc_metali = {metal: result.iloc[-1][metal] for metal in metale}

# Aktualne ceny z marżą
aktualne_ceny_z_marza = {
    metal: data.loc[result.index[-1], metal + "_EUR"] * (1 + margins[metal] / 100)
    for metal in metale
}

# Wartość zakupu metali dzisiaj
wartosc_zakupu_metali = sum(
    ilosc_metali[metal] * aktualne_ceny_z_marza[metal]
    for metal in metale
)

# Wyświetlenie
st.metric("🛒 Wartość zakupowa metali", f"{wartosc_zakupu_metali:,.2f} EUR")

# 🧮 Opcjonalnie: różnica procentowa
if wartosc_zakupu_metali > 0:
    roznica_proc = ((wartosc_zakupu_metali / wartosc_metali) - 1) * 100
else:
    roznica_proc = 0.0

st.caption(f"📈 Różnica względem wartości portfela: {roznica_proc:+.2f}%")

st.subheader("📈 Średni roczny rozwój cen wszystkich metali razem (ważony alokacją)")

# Twoja alokacja początkowa w procentach (przypominam: allocation to słownik typu {"Gold": 0.4, "Silver": 0.2, itd.})

# Liczymy ważoną średnią cen startową i końcową
weighted_start_price = sum(
    allocation[metal] * data.loc[result.index.min()][metal + "_EUR"]
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]
)

weighted_end_price = sum(
    allocation[metal] * data.loc[result.index.max()][metal + "_EUR"]
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]
)

# Ilość lat inwestycji
start_date = result.index.min()
end_date = result.index.max()
years = (end_date - start_date).days / 365.25

# Ważony średnioroczny wzrost cen (CAGR)
if weighted_start_price > 0 and years > 0:
    weighted_avg_annual_growth = (weighted_end_price / weighted_start_price) ** (1 / years) - 1
else:
    weighted_avg_annual_growth = 0.0

# Wyświetlenie
st.metric("🌐 Średni roczny wzrost cen (ważony alokacją)", f"{weighted_avg_annual_growth * 100:.2f}%")


# 📅 Wyniki: pierwszy roboczy dzień każdego roku
st.subheader("📅 Wyniki: pierwszy roboczy dzień każdego roku")
result_filtered = result.groupby(result.index.year).first()
st.dataframe(result_filtered)








# 📋 Podsumowanie kosztów magazynowania

# Koszty magazynowania
storage_fees = result[result["Akcja"] == "storage_fee"]

# Całkowity koszt magazynowania
total_storage_cost = storage_fees["Invested"].sum() * (storage_fee / 100) * (1 + vat / 100)

# Okres inwestycyjny w latach
start_date = result.index.min()
end_date = result.index.max()
years = (end_date - start_date).days / 365.25

# Średnioroczny koszt magazynowania
if years > 0:
    avg_annual_storage_cost = total_storage_cost / years
else:
    avg_annual_storage_cost = 0.0

# Koszt magazynowania z ostatniego roku
last_storage_date = storage_fees.index.max()
if pd.notna(last_storage_date):
    last_storage_cost = result.loc[last_storage_date]["Invested"] * (storage_fee / 100) * (1 + vat / 100)
else:
    last_storage_cost = 0.0

# Aktualna wartość portfela
current_portfolio_value = result["Portfolio Value"].iloc[-1]

# Aktualny procentowy koszt magazynowania (za ostatni rok)
if current_portfolio_value > 0:
    storage_cost_percentage = (last_storage_cost / current_portfolio_value) * 100
else:
    storage_cost_percentage = 0.0

st.subheader("📦 Podsumowanie kosztów magazynowania")

col1, col2 = st.columns(2)
with col1:
    st.metric("Średnioroczny koszt magazynowy", f"{avg_annual_storage_cost:,.2f} EUR")
with col2:
    st.metric("Koszt magazynowania (% ostatni rok)", f"{storage_cost_percentage:.2f}%")
