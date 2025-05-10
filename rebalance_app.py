import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# =========================================
# 0. Konfiguracja strony i wybór języka
# =========================================

st.set_page_config(page_title="Symulator Metali Szlachetnych", layout="wide")

# 🌐 Ustawienie języka w session_state (trwałe!)
if "language" not in st.session_state:
    st.session_state.language = "Polski"  # domyślny język przy starcie

st.sidebar.header("🌐 Wybierz język / Sprache wählen")
language_choice = st.sidebar.selectbox(
    "",
    ("🇵🇱 Polski", "🇩🇪 Deutsch"),
    index=0 if st.session_state.language == "Polski" else 1
)

# Aktualizacja session_state, jeśli użytkownik zmieni wybór
new_language = "Polski" if "Polski" in language_choice else "Deutsch"
if new_language != st.session_state.language:
    st.session_state.language = new_language
    st.experimental_rerun()  # Przeładowanie strony po zmianie języka

language = st.session_state.language

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
# 1.1 Wczytanie danych o inflacji
# =========================================

@st.cache_data
def load_inflation_data():
    df = pd.read_csv(
        "inflacja.csv", 
        sep=";", 
        encoding="cp1250"
    )
    df = df[["Rok", "Wartość"]].copy()
    df["Wartość"] = df["Wartość"].str.replace(",", ".").astype(float)
    df["Inflacja (%)"] = df["Wartość"] - 100
    return df[["Rok", "Inflacja (%)"]]

inflation_real = load_inflation_data()

# =========================================
# 2. Słownik tłumaczeń
# =========================================

translations = {
    "Polski": {
        "portfolio_value": "Wartość portfela",
        "real_portfolio_value": "Wartość portfela (realna, po inflacji)",
        "invested": "Zainwestowane",
        "storage_cost": "Koszty magazynowania",
        "chart_subtitle": "📈 Rozwój wartości portfela: nominalna i realna",
        "summary_title": "📊 Podsumowanie inwestycji",
        "simulation_settings": "⚙️ Parametry Symulacji",
        "investment_amounts": "💰 Inwestycja: Kwoty i daty",
        "metal_allocation": "⚖️ Alokacja metali szlachetnych (%)",
        "recurring_purchases": "🔁 Zakupy cykliczne",
        "rebalancing": "♻️ ReBalancing",
        "storage_costs": "📦 Koszty magazynowania",
        "margins_fees": "📊 Marże i prowizje",
        "buyback_prices": "💵 Ceny odkupu metali",
        "rebalance_prices": "♻️ Ceny ReBalancingu metali",
        "initial_allocation": "Kwota początkowej alokacji (EUR)",
        "first_purchase_date": "Data pierwszego zakupu",
        "last_purchase_date": "Data ostatniego zakupu",
        "purchase_frequency": "Periodyczność zakupów",
        "none": "Brak",
        "week": "Tydzień",
        "month": "Miesiąc",
        "quarter": "Kwartał",
        "purchase_day_of_week": "Dzień tygodnia zakupu",
        "purchase_day_of_month": "Dzień miesiąca zakupu (1–28)",
        "purchase_day_of_quarter": "Dzień kwartału zakupu (1–28)",
        "purchase_amount": "Kwota dokupu (EUR)",
        "rebalance_1": "ReBalancing 1",
        "rebalance_2": "ReBalancing 2",
        "deviation_condition": "Warunek odchylenia wartości",
        "deviation_threshold": "Próg odchylenia (%)",
        "start_rebalance": "Start ReBalancing",
        "monday": "Poniedziałek",
        "tuesday": "Wtorek",
        "wednesday": "Środa",
        "thursday": "Czwartek",
        "friday": "Piątek",
    },
    "Deutsch": {
        "portfolio_value": "Portfoliowert",
        "real_portfolio_value": "Portfoliowert (real, inflationsbereinigt)",
        "invested": "Investiertes Kapital",
        "storage_cost": "Lagerkosten",
        "chart_subtitle": "📈 Entwicklung des Portfoliowerts: nominal und real",
        "summary_title": "📊 Investitionszusammenfassung",
        "simulation_settings": "⚙️ Simulationseinstellungen",
        "investment_amounts": "💰 Investition: Beträge und Daten",
        "metal_allocation": "⚖️ Aufteilung der Edelmetalle (%)",
        "recurring_purchases": "🔁 Regelmäßige Käufe",
        "rebalancing": "♻️ ReBalancing",
        "storage_costs": "📦 Lagerkosten",
        "margins_fees": "📊 Margen und Gebühren",
        "buyback_prices": "💵 Rückkaufpreise der Metalle",
        "rebalance_prices": "♻️ Preise für ReBalancing der Metalle",
        "initial_allocation": "Anfangsinvestition (EUR)",
        "first_purchase_date": "Kaufstartdatum",
        "last_purchase_date": "Letzter Kauftag",
        "purchase_frequency": "Kaufhäufigkeit",
        "none": "Keine",
        "week": "Woche",
        "month": "Monat",
        "quarter": "Quartal",
        "purchase_day_of_week": "Wochentag für Kauf",
        "purchase_day_of_month": "Kauftag im Monat (1–28)",
        "purchase_day_of_quarter": "Kauftag im Quartal (1–28)",
        "purchase_amount": "Kaufbetrag (EUR)",
        "rebalance_1": "ReBalancing 1",
        "rebalance_2": "ReBalancing 2",
        "deviation_condition": "Abweichungsbedingung",
        "deviation_threshold": "Abweichungsschwelle (%)",
        "start_rebalance": "Start des ReBalancing",
        "monday": "Montag",
        "tuesday": "Dienstag",
        "wednesday": "Mittwoch",
        "thursday": "Donnerstag",
        "friday": "Freitag",
    }
}

# =========================================
# 3. Sidebar: Parametry użytkownika (DALSZA CZĘŚĆ)
# =========================================

st.sidebar.header(translations[language]["simulation_settings"])





# Inwestycja: Kwoty i daty
st.sidebar.subheader("💰 Inwestycja: Kwoty i daty")

today = datetime.today()
default_initial_date = today.replace(year=today.year - 20)

initial_allocation = st.sidebar.number_input(
    "Kwota początkowej alokacji (EUR)", 
    value=100000.0, 
    step=100.0
)

initial_date = st.sidebar.date_input(
    "Data pierwszego zakupu", 
    value=default_initial_date.date(), 
    min_value=data.index.min().date(), 
    max_value=data.index.max().date()
)

# Wyznacz minimalną datę końca (initial_date + 7 lat)
min_end_date = (pd.to_datetime(initial_date) + pd.DateOffset(years=7)).date()

if min_end_date > data.index.max().date():
    min_end_date = data.index.max().date()

end_purchase_date = st.sidebar.date_input(
    "Data ostatniego zakupu",
    value=data.index.max().date(), 
    min_value=min_end_date, 
    max_value=data.index.max().date()
)

# Obliczenie liczby lat zakupów
days_difference = (pd.to_datetime(end_purchase_date) - pd.to_datetime(initial_date)).days
years_difference = days_difference / 365.25  # uwzględnia przestępne lata

# ✅ / ⚠️ Dynamiczny komunikat
if years_difference >= 7:
    st.sidebar.success(f"✅ Zakres zakupów: {years_difference:.1f} lat.")
    dates_valid = True
else:
    st.sidebar.error(f"⚠️ Zakres zakupów: tylko {years_difference:.1f} lat. (minimum 7 lat wymagane!)")
    dates_valid = False

# Opcjonalnie: przycisk Start Symulacji
if dates_valid:
    start_simulation = st.sidebar.button("🚀 Uruchom symulację")
else:
    st.sidebar.button("🚀 Uruchom symulację", disabled=True)
    

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
    end_date = pd.to_datetime(end_date)  # upewniamy się, że end_date jest typu datetime

    if freq == "Tydzień":
        while current <= end_date:
            while current.weekday() != day:
                current += timedelta(days=1)
                if current > end_date:
                    break
            if current <= end_date:
                dates.append(current)
            current += timedelta(weeks=1)

    elif freq == "Miesiąc":
        while current <= end_date:
            current = current.replace(day=min(day, 28))
            if current <= end_date:
                dates.append(current)
            current += pd.DateOffset(months=1)

    elif freq == "Kwartał":
        while current <= end_date:
            current = current.replace(day=min(day, 28))
            if current <= end_date:
                dates.append(current)
            current += pd.DateOffset(months=3)

    # Brak zakupów jeśli "Brak"
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

    # 👉 Poprawiamy zakres czasu do initial_date → end_purchase_date
    all_dates = data.loc[initial_date:end_purchase_date].index

    # 👉 Poprawiamy też generowanie dat zakupów
    purchase_dates = generate_purchase_dates(initial_date, purchase_freq, purchase_day, end_purchase_date)

    last_year = None

    

    # 🔵 Dodajemy tutaj inicjalizację pamięci ReBalancingu:
    last_rebalance_dates = {
        "rebalance_1": None,
        "rebalance_2": None
    }

    # 🔵 Tu wstawiamy poprawioną funkcję apply_rebalance:
    def apply_rebalance(d, label, condition_enabled, threshold_percent):
        nonlocal last_rebalance_dates   # zamiast global → poprawne dla funkcji zagnieżdżonych!

        min_days_between_rebalances = 30  # minimalny odstęp w dniach (możesz zmienić)

        last_date = last_rebalance_dates.get(label)
        if last_date is not None and (d - last_date).days < min_days_between_rebalances:
            return f"rebalancing_skipped_{label}_too_soon"

        prices = data.loc[d]
        total_value = sum(prices[m + "_EUR"] * portfolio[m] for m in allocation)

        if total_value == 0:
            return f"rebalancing_skipped_{label}_no_value"

        current_shares = {
            m: (prices[m + "_EUR"] * portfolio[m]) / total_value
            for m in allocation
        }

        rebalance_trigger = False
        for metal in allocation:
            deviation = abs(current_shares[metal] - allocation[metal]) * 100
            if deviation >= threshold_percent:
                rebalance_trigger = True
                break

        if condition_enabled and not rebalance_trigger:
            return f"rebalancing_skipped_{label}_no_deviation"

        target_value = {m: total_value * allocation[m] for m in allocation}

        for metal in allocation:
            current_value = prices[metal + "_EUR"] * portfolio[metal]
            diff = current_value - target_value[metal]

            if diff > 0:
                sell_price = prices[metal + "_EUR"] * (1 + buyback_discounts[metal] / 100)
                grams_to_sell = min(diff / sell_price, portfolio[metal])
                portfolio[metal] -= grams_to_sell
                cash = grams_to_sell * sell_price

                for buy_metal in allocation:
                    needed_value = target_value[buy_metal] - prices[buy_metal + "_EUR"] * portfolio[buy_metal]
                    if needed_value > 0:
                        buy_price = prices[buy_metal + "_EUR"] * (1 + rebalance_markup[buy_metal] / 100)
                        buy_grams = min(cash / buy_price, needed_value / buy_price)
                        portfolio[buy_metal] += buy_grams
                        cash -= buy_grams * buy_price
                        if cash <= 0:
                            break

        last_rebalance_dates[label] = d
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

# === Korekta wartości portfela o realną inflację ===

# Słownik: Rok -> Inflacja
inflation_dict = dict(zip(inflation_real["Rok"], inflation_real["Inflacja (%)"]))

# Funkcja: obliczenie skumulowanej inflacji od startu
def calculate_cumulative_inflation(start_year, current_year):
    cumulative_factor = 1.0
    for year in range(start_year, current_year + 1):
        inflation = inflation_dict.get(year, 0.0) / 100  # Brak danych = 0% inflacji
        cumulative_factor *= (1 + inflation)
    return cumulative_factor

# Rok początkowy inwestycji
start_year = result.index.min().year

# Dodanie nowej kolumny z wartością realną portfela
real_values = []

for date in result.index:
    nominal_value = result.loc[date, "Portfolio Value"]
    current_year = date.year
    cumulative_inflation = calculate_cumulative_inflation(start_year, current_year)
    real_value = nominal_value / cumulative_inflation if cumulative_inflation != 0 else nominal_value
    real_values.append(real_value)

result["Portfolio Value Real"] = real_values

import matplotlib.pyplot as plt





# 📈 Wykres wartości portfela: nominalna vs realna vs inwestycje vs koszty magazynowania (Streamlit interaktywny)

# Przygotowanie danych do wykresu
result_plot = result.copy()
result_plot["Storage Cost"] = 0.0

# Oznaczenie kosztu magazynowania w odpowiednich dniach
storage_costs = result_plot[result_plot["Akcja"] == "storage_fee"].index
for d in storage_costs:
    result_plot.at[d, "Storage Cost"] = result_plot.at[d, "Invested"] * (storage_fee / 100) * (1 + vat / 100)

# ❗ Naprawiamy typ danych: wymuszamy float
for col in ["Portfolio Value", "Portfolio Value Real", "Invested", "Storage Cost"]:
    result_plot[col] = pd.to_numeric(result_plot[col], errors="coerce").fillna(0)

# Stworzenie DataFrame tylko z potrzebnymi seriami
chart_data = result_plot[["Portfolio Value", "Portfolio Value Real", "Invested", "Storage Cost"]]

# Nagłówki bardziej czytelne (opcjonalnie)
chart_data.rename(columns={
    "Portfolio Value": f"💰 {translations[language]['portfolio_value']}",
    "Portfolio Value Real": f"🏛️ {translations[language]['real_portfolio_value']}",
    "Invested": f"💵 {translations[language]['invested']}",
    "Storage Cost": f"📦 {translations[language]['storage_cost']}"
}, inplace=True)

# 📈 Ładny interaktywny wykres w Streamlit
st.subheader(translations[language]["chart_subtitle"])
st.line_chart(chart_data)


    
# Podsumowanie wyników

st.subheader(translations[language]["summary_title"])
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



st.subheader("📅 Mały uproszczony podgląd: Pierwszy dzień każdego roku")

# Grupujemy po roku i bierzemy pierwszy dzień roboczy
result_filtered = result.groupby(result.index.year).first()

# Tworzymy prostą tabelę z wybranymi kolumnami
simple_table = pd.DataFrame({
    "Zainwestowane (EUR)": result_filtered["Invested"].round(0),
    "Wartość portfela (EUR)": result_filtered["Portfolio Value"].round(0),
    "Złoto (g)": result_filtered["Gold"].round(2),
    "Srebro (g)": result_filtered["Silver"].round(2),
    "Platyna (g)": result_filtered["Platinum"].round(2),
    "Pallad (g)": result_filtered["Palladium"].round(2),
    "Akcja": result_filtered["Akcja"]
})

# Formatowanie EUR bez miejsc po przecinku
simple_table["Zainwestowane (EUR)"] = simple_table["Zainwestowane (EUR)"].map(lambda x: f"{x:,.0f} EUR")
simple_table["Wartość portfela (EUR)"] = simple_table["Wartość portfela (EUR)"].map(lambda x: f"{x:,.0f} EUR")

# Mniejszy font - używamy st.markdown z HTML
st.markdown(
    simple_table.to_html(index=True, escape=False), 
    unsafe_allow_html=True
)
st.markdown(
    """<style>
    table {
        font-size: 14px; /* mniejszy font w tabeli */
    }
    </style>""",
    unsafe_allow_html=True
)








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
