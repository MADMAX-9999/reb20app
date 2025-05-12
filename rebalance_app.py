# rebalance_app.py

import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta

# Stała konwersji uncji trojańskiej na gramy
TROY_OUNCE_TO_GRAM = 31.1034768

# Konfiguracja strony
st.set_page_config(page_title="Symulator Metali Szlachetnych", layout="wide")

# ====== FUNKCJE ŁADOWANIA DANYCH ======
@st.cache_data
def load_data():
    df = pd.read_csv("lbma_data.csv", parse_dates=True, index_col=0)
    df = df.sort_index()
    df = df.dropna()
    return df

@st.cache_data
def load_inflation_data():
    df = pd.read_csv("inflacja.csv", sep=";", encoding="cp1250")
    df["Wartosc"] = df["Wartosc"].str.replace(",", ".").astype(float)
    df["Inflacja (%)"] = df["Wartosc"] - 100
    return df[["Rok", "Inflacja (%)"]]

data = load_data()
inflation_real = load_inflation_data()

# ====== PRESETY - KONFIGURACJA ======
PRESET_FOLDER = "presets"
os.makedirs(PRESET_FOLDER, exist_ok=True)

# ====== PRESETY - ALTERNATYWNE PRZECHOWYWANIE W SESSION STATE ======
if "saved_presets" not in st.session_state:
    st.session_state.saved_presets = {}

# Wczytaj presety z plików (jeśli istnieją) przy pierwszym uruchomieniu
if "presets_loaded" not in st.session_state:
    if os.path.exists(PRESET_FOLDER):
        try:
            for filename in os.listdir(PRESET_FOLDER):
                if filename.endswith(".json"):
                    preset_name = filename.replace(".json", "")
                    try:
                        with open(os.path.join(PRESET_FOLDER, filename), "r", encoding="utf-8") as f:
                            content = f.read()
                            if content.strip():
                                st.session_state.saved_presets[preset_name] = json.loads(content)
                    except (json.JSONDecodeError, IOError) as e:
                        print(f"Błąd wczytywania presetu {filename}: {e}")
                        continue
        except Exception as e:
            print(f"Błąd dostępu do folderu presetów: {e}")
    st.session_state.presets_loaded = True

# Wczytaj preset jeśli jest zdefiniowany
if "preset_to_load" in st.session_state:
    preset_name = st.session_state["preset_to_load"]
    preset = None
    
    # Sprawdź najpierw w session_state
    if preset_name in st.session_state.saved_presets:
        preset = st.session_state.saved_presets[preset_name]
    else:
        # Fallback do plików
        preset_path = os.path.join(PRESET_FOLDER, f"{preset_name}.json")
        if os.path.exists(preset_path):
            try:
                with open(preset_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        preset = json.loads(content)
            except (json.JSONDecodeError, IOError) as e:
                st.error(f"Błąd wczytywania presetu: {e}")
    
    if preset:
        # Ustaw wszystkie wartości w session_state
        st.session_state["initial_allocation"] = preset.get("initial_allocation", 100000.0)
        st.session_state["initial_date"] = pd.to_datetime(preset.get("initial_date")).date()
        st.session_state["end_purchase_date"] = pd.to_datetime(preset.get("end_purchase_date")).date()
        
        # Alokacja
        st.session_state["alloc_Gold"] = preset["allocation"]["Gold"]
        st.session_state["alloc_Silver"] = preset["allocation"]["Silver"]
        st.session_state["alloc_Platinum"] = preset["allocation"]["Platinum"]
        st.session_state["alloc_Palladium"] = preset["allocation"]["Palladium"]
        
        # Zakupy cykliczne
        st.session_state["purchase_freq"] = preset["purchase"]["frequency"]
        st.session_state["purchase_day"] = preset["purchase"]["day"]
        st.session_state["purchase_amount"] = preset["purchase"]["amount"]
        
        # ReBalancing - poprawna konwersja dat
        for k, v in preset["rebalance"].items():
            if "start" in k and isinstance(v, str):
                st.session_state[k] = pd.to_datetime(v).date()
            else:
                st.session_state[k] = v
                
        # Koszty magazynowania
        st.session_state["storage_fee"] = preset["storage"]["fee"]
        st.session_state["vat"] = preset["storage"]["vat"]
        st.session_state["storage_metal"] = preset["storage"]["metal"]
        
        # Marże
        for metal, value in preset["margins"].items():
            st.session_state[f"margin_{metal}"] = value
            
        # Odkup
        for metal, value in preset["buyback"].items():
            st.session_state[f"buyback_{metal}"] = value
            
        # ReBalance markup
        for metal, value in preset["rebalance_markup"].items():
            st.session_state[f"rebalance_markup_{metal}"] = value
    
    del st.session_state["preset_to_load"]

# ====== JĘZYK ======
if "language" not in st.session_state:
    st.session_state.language = "Polski"

# ====== SŁOWNIK TŁUMACZEŃ ======
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
        "page_title": "Symulator Metali Szlachetnych",
        "app_title": "Symulator ReBalancingu Portfela Metali Szlachetnych",
        "reset_allocation": "🔄 Resetuj do 40/20/20/20",
        "gold": "Złoto (Au)",
        "silver": "Srebro (Ag)",
        "platinum": "Platyna (Pt)",
        "palladium": "Pallad (Pd)",
        "allocation_error": "❗ Suma alokacji: {}% – musi wynosić dokładnie 100%, aby kontynuować.",
        "purchase_days_range": "✅ Zakres zakupów: {:.1f} lat.",
        "short_period_warning": "⚠️ UWAGA! Okres krótszy niż 7 lat ({:.1f} lat)",
        "start_simulation": "🚀 Uruchom symulację",
        "deviation_condition_1": "Warunek odchylenia wartości dla ReBalancing 1",
        "deviation_condition_2": "Warunek odchylenia wartości dla ReBalancing 2",
        "deviation_threshold_1": "Próg odchylenia (%) dla ReBalancing 1",
        "deviation_threshold_2": "Próg odchylenia (%) dla ReBalancing 2",
        "annual_storage_fee": "Roczny koszt magazynowania (%)",
        "metal_for_costs": "Metal do pokrycia kosztów",
        "best_of_year": "Best of year",
        "all_metals": "ALL",
        "gold_margin": "Marża Gold (%)",
        "silver_margin": "Marża Silver (%)",
        "platinum_margin": "Marża Platinum (%)",
        "palladium_margin": "Marża Palladium (%)",
        "gold_buyback": "Złoto odk. od SPOT (%)",
        "silver_buyback": "Srebro odk. od SPOT (%)",
        "platinum_buyback": "Platyna odk. od SPOT (%)",
        "palladium_buyback": "Pallad odk. od SPOT (%)",
        "gold_rebalance": "Złoto ReBalancing (%)",
        "silver_rebalance": "Srebro ReBalancing (%)",
        "platinum_rebalance": "Platyna ReBalancing (%)",
        "palladium_rebalance": "Pallad ReBalancing (%)",
        "metal_price_growth": "📊 Wzrost cen metali od startu inwestycji",
        "current_metal_amounts": "⚖️ Aktualnie posiadane ilości metali (oz)",
        "current_metal_amounts_g": "⚖️ Aktualnie posiadane ilości metali (g)",
        "gram": "g",
        "capital_allocation": "💶 Alokacja kapitału",
        "metals_sale_value": "📦 Wycena sprzedażowa metali",
        "metals_purchase_value": "🛒 Wartość zakupowa metali",
        "difference_vs_portfolio": "📈 Różnica względem wartości portfela: {:+.2f}%",
        "avg_annual_growth": "📈 Średni roczny rozwój cen wszystkich metali razem (ważony alokacją)",
        "weighted_avg_growth": "🌐 Średni roczny wzrost cen (ważony alokacją)",
        "simplified_view": "📅 Mały uproszczony podgląd: Pierwszy dzień każdego roku",
        "invested_eur": "Zainwestowane (EUR)",
        "portfolio_value_eur": "Wartość portfela (EUR)",
        "gold_g": "Złoto (g)",
        "silver_g": "Srebro (g)",
        "platinum_g": "Platyna (g)",
        "palladium_g": "Pallad (g)",
        "action": "Akcja",
        "storage_costs_summary": "📦 Podsumowanie kosztów magazynowania",
        "avg_annual_storage_cost": "Średnioroczny koszt magazynowy",
        "storage_cost_percentage": "Koszt magazynowania (% ostatni rok)",
        "vat": "VAT (%)"
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
        "page_title": "Edelmetalle-Simulator",
        "app_title": "Edelmetall-Portfolio ReBalancing-Simulator",
        "reset_allocation": "🔄 Zurücksetzen auf 40/20/20/20",
        "gold": "Gold (Au)",
        "silver": "Silber (Ag)",
        "platinum": "Platin (Pt)",
        "palladium": "Palladium (Pd)",
        "allocation_error": "❗ Summe der Zuteilung: {}% – muss genau 100% betragen, um fortzufahren.",
        "purchase_days_range": "✅ Kaufzeitraum: {:.1f} Jahre.",
        "short_period_warning": "⚠️ ACHTUNG! Zeitraum kürzer als 7 Jahre ({:.1f} Jahre)",
        "start_simulation": "🚀 Simulation starten",
        "deviation_condition_1": "Abweichungsbedingung für ReBalancing 1",
        "deviation_condition_2": "Abweichungsbedingung für ReBalancing 2",
        "deviation_threshold_1": "Abweichungsschwelle (%) für ReBalancing 1",
        "deviation_threshold_2": "Abweichungsschwelle (%) für ReBalancing 2",
        "annual_storage_fee": "Jährliche Lagerkosten (%)",
        "metal_for_costs": "Metall zur Kostendeckung",
        "best_of_year": "Bestes des Jahres",
        "all_metals": "ALLE",
        "gold_margin": "Gold Marge (%)",
        "silver_margin": "Silber Marge (%)",
        "platinum_margin": "Platin Marge (%)",
        "palladium_margin": "Palladium Marge (%)",
        "gold_buyback": "Gold Rückkauf von SPOT (%)",
        "silver_buyback": "Silber Rückkauf von SPOT (%)",
        "platinum_buyback": "Platin Rückkauf von SPOT (%)",
        "palladium_buyback": "Palladium Rückkauf von SPOT (%)",
        "gold_rebalance": "Gold ReBalancing (%)",
        "silver_rebalance": "Silber ReBalancing (%)",
        "platinum_rebalance": "Platin ReBalancing (%)",
        "palladium_rebalance": "Palladium ReBalancing (%)",
        "metal_price_growth": "📊 Preissteigerung der Metalle seit Investitionsbeginn",
        "current_metal_amounts": "⚖️ Aktuell gehaltene Metallmengen (oz)",
        "current_metal_amounts_g": "⚖️ Aktuell gehaltene Metallmengen (g)",
        "gram": "g",
        "capital_allocation": "💶 Kapitalallokation",
        "metals_sale_value": "📦 Metallverkaufswert",
        "metals_purchase_value": "🛒 Metallkaufwert",
        "difference_vs_portfolio": "📈 Unterschied zum Portfoliowert: {:+.2f}%",
        "avg_annual_growth": "📈 Durchschnittliche jährliche Preisentwicklung aller Metalle (gewichtet nach Allokation)",
        "weighted_avg_growth": "🌐 Durchschnittliche jährliche Preissteigerung (gewichtete Allokation)",
        "simplified_view": "📅 Vereinfachte Übersicht: Erster Tag jedes Jahres",
        "invested_eur": "Investiert (EUR)",
        "portfolio_value_eur": "Portfoliowert (EUR)",
        "gold_g": "Gold (g)",
        "silver_g": "Silber (g)",
        "platinum_g": "Platin (g)",
        "palladium_g": "Palladium (g)",
        "action": "Aktion",
        "storage_costs_summary": "📦 Zusammenfassung der Lagerkosten",
        "avg_annual_storage_cost": "Durchschnittliche jährliche Lagerkosten",
        "storage_cost_percentage": "Lagerkosten (% letztes Jahr)",
        "vat": "MwSt (%)"
    }
}

# Tłumaczenia dla akcji
action_translations = {
    "Polski": {
        "initial": "początkowy",
        "recurring": "cykliczny",
        "storage_fee": "opłata magazynowa",
        "rebalance_1": "ReBalancing 1",
        "rebalance_2": "ReBalancing 2",
        "rebalancing_skipped_rebalance_1_too_soon": "pominięto ReBalancing 1 (za wcześnie)",
        "rebalancing_skipped_rebalance_2_too_soon": "pominięto ReBalancing 2 (za wcześnie)",
        "rebalancing_skipped_rebalance_1_no_value": "pominięto ReBalancing 1 (brak wartości)",
        "rebalancing_skipped_rebalance_2_no_value": "pominięto ReBalancing 2 (brak wartości)",
        "rebalancing_skipped_rebalance_1_no_deviation": "pominięto ReBalancing 1 (brak odchylenia)",
        "rebalancing_skipped_rebalance_2_no_deviation": "pominięto ReBalancing 2 (brak odchylenia)"
    },
    "Deutsch": {
        "initial": "Anfänglich",
        "recurring": "Regelmäßig",
        "storage_fee": "Lagergebühr",
        "rebalance_1": "ReBalancing 1",
        "rebalance_2": "ReBalancing 2",
        "rebalancing_skipped_rebalance_1_too_soon": "ReBalancing 1 übersprungen (zu früh)",
        "rebalancing_skipped_rebalance_2_too_soon": "ReBalancing 2 übersprungen (zu früh)",
        "rebalancing_skipped_rebalance_1_no_value": "ReBalancing 1 übersprungen (kein Wert)",
        "rebalancing_skipped_rebalance_2_no_value": "ReBalancing 2 übersprungen (kein Wert)",
        "rebalancing_skipped_rebalance_1_no_deviation": "ReBalancing 1 übersprungen (keine Abweichung)",
        "rebalancing_skipped_rebalance_2_no_deviation": "ReBalancing 2 übersprungen (keine Abweichung)"
    }
}

def translate_action(action_str):
    if language not in action_translations:
        return action_str
    
    actions = action_str.split(", ")
    translated = []
    for action in actions:
        translated.append(action_translations[language].get(action, action))
    return ", ".join(translated)



# ====== GŁÓWNA APLIKACJA ======
st.sidebar.header("🌐 Wybierz język / Sprache wählen")
language_choice = st.sidebar.selectbox(
    "",
    ("🇵🇱 Polski", "🇩🇪 Deutsch"),
    index=0 if st.session_state.language == "Polski" else 1
)

new_language = "Polski" if "Polski" in language_choice else "Deutsch"
if new_language != st.session_state.language:
    st.session_state.language = new_language
    st.rerun()

language = st.session_state.language

# Parametry symulacji
st.sidebar.header(translations[language]["simulation_settings"])

# Inwestycja: Kwoty i daty
st.sidebar.subheader(translations[language]["investment_amounts"])

today = datetime.today()
default_initial_date = today.replace(year=today.year - 20)

# Alokacja początkowa
initial_allocation = st.sidebar.number_input(
    translations[language]["initial_allocation"],
    value=st.session_state.get("initial_allocation", 100000.0),
    step=100.0,
    key="initial_allocation"
)

# Data początkowa
initial_date = st.sidebar.date_input(
    translations[language]["first_purchase_date"],
    value=st.session_state.get("initial_date", default_initial_date.date()),
    min_value=data.index.min().date(),
    max_value=data.index.max().date(),
    key="initial_date"
)

# Data końcowa - bez ograniczeń minimalnych
end_purchase_date = st.sidebar.date_input(
    translations[language]["last_purchase_date"],
    value=st.session_state.get("end_purchase_date", data.index.max().date()),
    min_value=initial_date,  # Zmienione - teraz minimum to data początkowa
    max_value=data.index.max().date(),
    key="end_purchase_date"
)

# Obliczenie liczby lat zakupów
days_difference = (pd.to_datetime(end_purchase_date) - pd.to_datetime(initial_date)).days
years_difference = days_difference / 365.25

# Informacja o zakresie dat
if years_difference >= 7:
    st.sidebar.success(translations[language]["purchase_days_range"].format(years_difference))
else:
    st.sidebar.warning(translations[language]["short_period_warning"].format(years_difference))

# Alokacja metali
st.sidebar.subheader(translations[language]["metal_allocation"])

# Domyślne wartości alokacji
for metal, default in {"Gold": 40, "Silver": 20, "Platinum": 20, "Palladium": 20}.items():
    if f"alloc_{metal}" not in st.session_state:
        st.session_state[f"alloc_{metal}"] = default

if st.sidebar.button(translations[language]["reset_allocation"]):
    st.session_state["alloc_Gold"] = 40
    st.session_state["alloc_Silver"] = 20
    st.session_state["alloc_Platinum"] = 20
    st.session_state["alloc_Palladium"] = 20
    st.rerun()

allocation_gold = st.sidebar.slider(translations[language]["gold"], 0, 100, key="alloc_Gold")
allocation_silver = st.sidebar.slider(translations[language]["silver"], 0, 100, key="alloc_Silver")
allocation_platinum = st.sidebar.slider(translations[language]["platinum"], 0, 100, key="alloc_Platinum")
allocation_palladium = st.sidebar.slider(translations[language]["palladium"], 0, 100, key="alloc_Palladium")

total = allocation_gold + allocation_silver + allocation_platinum + allocation_palladium
if total != 100:
    st.title(translations[language]["app_title"])
    st.error(translations[language]["allocation_error"].format(total))
    st.stop()

allocation = {
    "Gold": allocation_gold / 100,
    "Silver": allocation_silver / 100,
    "Platinum": allocation_platinum / 100,
    "Palladium": allocation_palladium / 100
}

# Zakupy cykliczne
st.sidebar.subheader(translations[language]["recurring_purchases"])

purchase_freq_options = [
    translations[language]["none"],
    translations[language]["week"],
    translations[language]["month"],
    translations[language]["quarter"]
]

# Znajdź indeks dla zapisanej częstotliwości
saved_freq = st.session_state.get("purchase_freq", translations[language]["month"])
freq_index = 1  # domyślnie miesiąc
if saved_freq in purchase_freq_options:
    freq_index = purchase_freq_options.index(saved_freq)

purchase_freq = st.sidebar.selectbox(
    translations[language]["purchase_frequency"],
    purchase_freq_options,
    index=freq_index,
    key="purchase_freq"
)

# Dzień zakupu w zależności od częstotliwości
if purchase_freq == translations[language]["week"]:
    days_of_week = [
        translations[language]["monday"],
        translations[language]["tuesday"],
        translations[language]["wednesday"],
        translations[language]["thursday"],
        translations[language]["friday"]
    ]
    
    saved_day = st.session_state.get("purchase_day", 0)
    selected_day = st.sidebar.selectbox(
        translations[language]["purchase_day_of_week"],
        days_of_week,
        index=saved_day if saved_day < len(days_of_week) else 0
    )
    purchase_day = days_of_week.index(selected_day)
    default_purchase_amount = 250.0
    
elif purchase_freq == translations[language]["month"]:
    purchase_day = st.sidebar.number_input(
        translations[language]["purchase_day_of_month"],
        min_value=1,
        max_value=28,
        value=st.session_state.get("purchase_day", 1),
        key="purchase_day"
    )
    default_purchase_amount = 1000.0
    
elif purchase_freq == translations[language]["quarter"]:
    purchase_day = st.sidebar.number_input(
        translations[language]["purchase_day_of_quarter"],
        min_value=1,
        max_value=28,
        value=st.session_state.get("purchase_day", 1),
        key="purchase_day"
    )
    default_purchase_amount = 3250.0
    
else:
    purchase_day = None
    default_purchase_amount = 0.0

purchase_amount = st.sidebar.number_input(
    translations[language]["purchase_amount"],
    value=st.session_state.get("purchase_amount", default_purchase_amount),
    step=50.0,
    key="purchase_amount"
)

# ReBalancing
rebalance_base_year = initial_date.year + 1
rebalance_1_default = datetime(rebalance_base_year, 4, 1)
rebalance_2_default = datetime(rebalance_base_year, 10, 1)

with st.sidebar.expander(translations[language]["rebalancing"], expanded=False):
    rebalance_1 = st.checkbox(
        translations[language]["rebalance_1"],
        value=st.session_state.get("rebalance_1", True),
        key="rebalance_1"
    )
    rebalance_1_condition = st.checkbox(
        translations[language]["deviation_condition_1"],
        value=st.session_state.get("rebalance_1_condition", False),
        key="rebalance_1_condition"
    )
    rebalance_1_threshold = st.number_input(
        translations[language]["deviation_threshold_1"],
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.get("rebalance_1_threshold", 12.0),
        step=0.5,
        key="rebalance_1_threshold"
    )
    rebalance_1_start = st.date_input(
        translations[language]["start_rebalance"] + " 1",
        value=st.session_state.get("rebalance_1_start", rebalance_1_default.date()),
        min_value=data.index.min().date(),
        max_value=data.index.max().date(),
        key="rebalance_1_start"
    )
    
    rebalance_2 = st.checkbox(
        translations[language]["rebalance_2"],
        value=st.session_state.get("rebalance_2", False),
        key="rebalance_2"
    )
    rebalance_2_condition = st.checkbox(
        translations[language]["deviation_condition_2"],
        value=st.session_state.get("rebalance_2_condition", False),
        key="rebalance_2_condition"
    )
    rebalance_2_threshold = st.number_input(
        translations[language]["deviation_threshold_2"],
        min_value=0.0,
        max_value=100.0,
        value=st.session_state.get("rebalance_2_threshold", 12.0),
        step=0.5,
        key="rebalance_2_threshold"
    )
    rebalance_2_start = st.date_input(
        translations[language]["start_rebalance"] + " 2",
        value=st.session_state.get("rebalance_2_start", rebalance_2_default.date()),
        min_value=data.index.min().date(),
        max_value=data.index.max().date(),
        key="rebalance_2_start"
    )

# Koszty magazynowania
storage_metal_options = [
    "Gold", "Silver", "Platinum", "Palladium",
    translations[language]["best_of_year"],
    translations[language]["all_metals"]
]

with st.sidebar.expander(translations[language]["storage_costs"], expanded=False):
    storage_fee = st.number_input(
        translations[language]["annual_storage_fee"],
        value=st.session_state.get("storage_fee", 1.5),
        key="storage_fee"
    )
    vat = st.number_input(
        translations[language]["vat"],
        value=st.session_state.get("vat", 0.0),
        key="vat"
    )
    
    # Znajdź indeks dla zapisanego metalu
    saved_metal = st.session_state.get("storage_metal", "Gold")
    metal_index = 0
    if saved_metal in storage_metal_options:
        metal_index = storage_metal_options.index(saved_metal)
    
    storage_metal = st.selectbox(
        translations[language]["metal_for_costs"],
        storage_metal_options,
        index=metal_index,
        key="storage_metal"
    )

# Marże i prowizje
with st.sidebar.expander(translations[language]["margins_fees"], expanded=False):
    margins = {
        "Gold": st.number_input(
            translations[language]["gold_margin"],
            value=st.session_state.get("margin_Gold", 15.6),
            key="margin_Gold"
        ),
        "Silver": st.number_input(
            translations[language]["silver_margin"],
            value=st.session_state.get("margin_Silver", 18.36),
            key="margin_Silver"
        ),
        "Platinum": st.number_input(
            translations[language]["platinum_margin"],
            value=st.session_state.get("margin_Platinum", 24.24),
            key="margin_Platinum"
        ),
        "Palladium": st.number_input(
            translations[language]["palladium_margin"],
            value=st.session_state.get("margin_Palladium", 22.49),
            key="margin_Palladium"
        )
    }

# Ceny odkupu
with st.sidebar.expander(translations[language]["buyback_prices"], expanded=False):
    buyback_discounts = {
        "Gold": st.number_input(
            translations[language]["gold_buyback"],
            value=st.session_state.get("buyback_Gold", -1.5),
            step=0.1,
            key="buyback_Gold"
        ),
        "Silver": st.number_input(
            translations[language]["silver_buyback"],
            value=st.session_state.get("buyback_Silver", -3.0),
            step=0.1,
            key="buyback_Silver"
        ),
        "Platinum": st.number_input(
            translations[language]["platinum_buyback"],
            value=st.session_state.get("buyback_Platinum", -3.0),
            step=0.1,
            key="buyback_Platinum"
        ),
        "Palladium": st.number_input(
            translations[language]["palladium_buyback"],
            value=st.session_state.get("buyback_Palladium", -3.0),
            step=0.1,
            key="buyback_Palladium"
        )
    }

# Ceny ReBalancingu
with st.sidebar.expander(translations[language]["rebalance_prices"], expanded=False):
    rebalance_markup = {
        "Gold": st.number_input(
            translations[language]["gold_rebalance"],
            value=st.session_state.get("rebalance_markup_Gold", 6.5),
            step=0.1,
            key="rebalance_markup_Gold"
        ),
        "Silver": st.number_input(
            translations[language]["silver_rebalance"],
            value=st.session_state.get("rebalance_markup_Silver", 6.5),
            step=0.1,
            key="rebalance_markup_Silver"
        ),
        "Platinum": st.number_input(
            translations[language]["platinum_rebalance"],
            value=st.session_state.get("rebalance_markup_Platinum", 6.5),
            step=0.1,
            key="rebalance_markup_Platinum"
        ),
        "Palladium": st.number_input(
            translations[language]["palladium_rebalance"],
            value=st.session_state.get("rebalance_markup_Palladium", 6.5),
            step=0.1,
            key="rebalance_markup_Palladium"
        )
    }

# Presety
with st.sidebar.expander("💾 Presety", expanded=False):
    preset_name = st.text_input("Nazwa presetu")
    
    # Zapisywanie presetu
    if st.button("Zapisz preset"):
        preset_data = {
            "initial_allocation": st.session_state.get("initial_allocation", 100000.0),
            "initial_date": str(st.session_state.get("initial_date", initial_date)),
            "end_purchase_date": str(st.session_state.get("end_purchase_date", end_purchase_date)),
            "allocation": {
                "Gold": st.session_state.get("alloc_Gold", 40),
                "Silver": st.session_state.get("alloc_Silver", 20),
                "Platinum": st.session_state.get("alloc_Platinum", 20),
                "Palladium": st.session_state.get("alloc_Palladium", 20)
            },
            "purchase": {
                "frequency": st.session_state.get("purchase_freq", translations[language]["month"]),
                "day": st.session_state.get("purchase_day", 1),
                "amount": st.session_state.get("purchase_amount", 1000.0)
            },
            "rebalance": {
                "rebalance_1": st.session_state.get("rebalance_1", True),
                "rebalance_1_condition": st.session_state.get("rebalance_1_condition", False),
                "rebalance_1_threshold": st.session_state.get("rebalance_1_threshold", 12.0),
                "rebalance_1_start": str(st.session_state.get("rebalance_1_start", rebalance_1_default.date())),
                "rebalance_2": st.session_state.get("rebalance_2", False),
                "rebalance_2_condition": st.session_state.get("rebalance_2_condition", False),
                "rebalance_2_threshold": st.session_state.get("rebalance_2_threshold", 12.0),
                "rebalance_2_start": str(st.session_state.get("rebalance_2_start", rebalance_2_default.date()))
            },
            "storage": {
                "fee": st.session_state.get("storage_fee", 1.5),
                "vat": st.session_state.get("vat", 0.0),
                "metal": st.session_state.get("storage_metal", "Gold")
            },
            "margins": {
                metal: st.session_state.get(f"margin_{metal}", margin)
                for metal, margin in margins.items()
            },
            "buyback": {
                metal: st.session_state.get(f"buyback_{metal}", discount)
                for metal, discount in buyback_discounts.items()
            },
            "rebalance_markup": {
                metal: st.session_state.get(f"rebalance_markup_{metal}", markup)
                for metal, markup in rebalance_markup.items()
            }
        }
        
        # Zapisz w session_state
        st.session_state.saved_presets[preset_name] = preset_data
        
        # Próba zapisu do pliku (może nie działać na Streamlit Cloud)
        try:
            os.makedirs(PRESET_FOLDER, exist_ok=True)  # Upewnij się że folder istnieje
            file_path = os.path.join(PRESET_FOLDER, f"{preset_name}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Na Streamlit Cloud może nie działać
            print(f"Nie udało się zapisać presetu do pliku: {e}")
        
        st.success(f"Preset '{preset_name}' został zapisany")
        
        # Przycisk pobrania pliku
        json_str = json.dumps(preset_data, indent=2, ensure_ascii=False)
        st.download_button("📥 Pobierz preset jako plik JSON", json_str, file_name=f"{preset_name}.json", mime="application/json")
    
    # Lista presetów (z session_state i plików)
    presets_from_files = []
    if os.path.exists(PRESET_FOLDER):
        presets_from_files = [f.replace(".json", "") for f in os.listdir(PRESET_FOLDER) if f.endswith(".json")]
    
    all_presets = list(set(list(st.session_state.saved_presets.keys()) + presets_from_files))
    all_presets.sort()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_preset = st.selectbox("📂 Wczytaj/Usuń preset", options=[""] + all_presets)
    
    with col1:
        if selected_preset and st.button("Wczytaj preset", type="primary"):
            st.session_state["preset_to_load"] = selected_preset
            st.rerun()
    
    with col2:
        if selected_preset and st.button("🗑️ Usuń", type="secondary"):
            # Usuń z session_state
            if selected_preset in st.session_state.saved_presets:
                del st.session_state.saved_presets[selected_preset]
            
            # Próba usunięcia pliku
            try:
                preset_path = os.path.join(PRESET_FOLDER, f"{selected_preset}.json")
                if os.path.exists(preset_path):
                    os.remove(preset_path)
            except:
                pass  # Ignoruj błędy na Streamlit Cloud
            
            st.success(f"Preset '{selected_preset}' został usunięty")
            st.rerun()
    
    # Eksport wszystkich presetów
    if all_presets:
        st.markdown("---")
        if st.button("📦 Pobierz wszystkie presety jako ZIP"):
            import zipfile
            import io
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                # Dodaj presety z session_state
                for preset_name, preset_data in st.session_state.saved_presets.items():
                    json_str = json.dumps(preset_data, indent=2, ensure_ascii=False)
                    zip_file.writestr(f"{preset_name}.json", json_str)
                
                # Dodaj presety z plików (jeśli istnieją)
                if os.path.exists(PRESET_FOLDER):
                    for preset_file in os.listdir(PRESET_FOLDER):
                        if preset_file.endswith(".json"):
                            file_path = os.path.join(PRESET_FOLDER, preset_file)
                            try:
                                zip_file.write(file_path, preset_file)
                            except:
                                pass
            
            zip_buffer.seek(0)
            st.download_button(
                label="⬇️ Pobierz archiwum ZIP",
                data=zip_buffer,
                file_name="presety_metale.zip",
                mime="application/zip"
            )
    
    # Informacja o przechowywaniu
    st.info("💡 Presety są przechowywane w sesji. Na Streamlit Cloud znikną po restarcie aplikacji. Pobierz je jako plik, aby zachować na stałe.")
    
    # Import presetów
    uploaded_file = st.file_uploader("📤 Wczytaj preset z pliku", type=['json'])
    if uploaded_file is not None:
        try:
            preset_data = json.load(uploaded_file)
            preset_name = uploaded_file.name.replace('.json', '')
            st.session_state.saved_presets[preset_name] = preset_data
            st.success(f"Preset '{preset_name}' został wczytany")
            st.rerun()
        except Exception as e:
            st.error(f"Błąd wczytywania presetu: {e}")

# ====== FUNKCJE POMOCNICZE ======
def generate_purchase_dates(start_date, freq, day, end_date):
    dates = []
    current = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    if freq == translations[language]["week"]:
        while current <= end_date:
            while current.weekday() != day:
                current += timedelta(days=1)
                if current > end_date:
                    break
            if current <= end_date:
                dates.append(current)
            current += timedelta(weeks=1)
    
    elif freq == translations[language]["month"]:
        while current <= end_date:
            current = current.replace(day=min(day, 28))
            if current <= end_date:
                dates.append(current)
            current += pd.DateOffset(months=1)
    
    elif freq == translations[language]["quarter"]:
        while current <= end_date:
            current = current.replace(day=min(day, 28))
            if current <= end_date:
                dates.append(current)
            current += pd.DateOffset(months=3)
    
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
    
    all_dates = data.loc[initial_date:end_purchase_date].index
    purchase_dates = generate_purchase_dates(initial_date, purchase_freq, purchase_day, end_purchase_date)
    
    last_year = None
    last_rebalance_dates = {
        "rebalance_1": None,
        "rebalance_2": None
    }
    
    def apply_rebalance(d, label, condition_enabled, threshold_percent):
        nonlocal last_rebalance_dates
        
        min_days_between_rebalances = 30
        
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
            
            if storage_metal == translations[language]["best_of_year"]:
                metal_to_sell = find_best_metal_of_year(
                    data.index[data.index.year == last_year][0],
                    data.index[data.index.year == last_year][-1]
                )
                sell_price = prices_end[metal_to_sell + "_EUR"] * (1 + buyback_discounts[metal_to_sell] / 100)
                grams_needed = storage_cost / sell_price
                grams_needed = min(grams_needed, portfolio[metal_to_sell])
                portfolio[metal_to_sell] -= grams_needed
            
            elif storage_metal == translations[language]["all_metals"]:
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
    
    # Tworzenie DataFrame z wynikami
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

# ====== GŁÓWNA CZĘŚĆ APLIKACJI ======
st.title(translations[language]["app_title"])
st.markdown("---")

# Zawsze uruchamiaj symulację
result = simulate(allocation)

# Korekta wartości portfela o realną inflację
inflation_dict = dict(zip(inflation_real["Rok"], inflation_real["Inflacja (%)"]))

def calculate_cumulative_inflation(start_year, current_year):
    cumulative_factor = 1.0
    for year in range(start_year, current_year + 1):
        inflation = inflation_dict.get(year, 0.0) / 100
        cumulative_factor *= (1 + inflation)
    return cumulative_factor

start_year = result.index.min().year
real_values = []

for date in result.index:
    nominal_value = result.loc[date, "Portfolio Value"]
    current_year = date.year
    cumulative_inflation = calculate_cumulative_inflation(start_year, current_year)
    real_value = nominal_value / cumulative_inflation if cumulative_inflation != 0 else nominal_value
    real_values.append(real_value)

result["Portfolio Value Real"] = real_values

# Wykres
result_plot = result.copy()
result_plot["Storage Cost"] = 0.0

storage_costs = result_plot[result_plot["Akcja"] == "storage_fee"].index
for d in storage_costs:
    result_plot.at[d, "Storage Cost"] = result_plot.at[d, "Invested"] * (storage_fee / 100) * (1 + vat / 100)

for col in ["Portfolio Value", "Portfolio Value Real", "Invested", "Storage Cost"]:
    result_plot[col] = pd.to_numeric(result_plot[col], errors="coerce").fillna(0)

chart_data = result_plot[["Portfolio Value", "Portfolio Value Real", "Invested", "Storage Cost"]]

chart_data.rename(columns={
    "Portfolio Value": f"💰 {translations[language]['portfolio_value']}",
    "Portfolio Value Real": f"🏛️ {translations[language]['real_portfolio_value']}",
    "Invested": f"💵 {translations[language]['invested']}",
    "Storage Cost": f"📦 {translations[language]['storage_cost']}"
}, inplace=True)

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

# Wzrost cen metali
st.subheader(translations[language]["metal_price_growth"])

start_prices = data.loc[start_date]
end_prices = data.loc[end_date]

metale = ["Gold", "Silver", "Platinum", "Palladium"]
wzrosty = {}

for metal in metale:
    start_price = start_prices[metal + "_EUR"]
    end_price = end_prices[metal + "_EUR"]
    wzrost = (end_price / start_price - 1) * 100
    wzrosty[metal] = wzrost

# Wyświetlenie
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(translations[language]["gold"], f"{wzrosty['Gold']:.2f}%")
with col2:
    st.metric(translations[language]["silver"], f"{wzrosty['Silver']:.2f}%")
with col3:
    st.metric(translations[language]["platinum"], f"{wzrosty['Platinum']:.2f}%")
with col4:
    st.metric(translations[language]["palladium"], f"{wzrosty['Palladium']:.2f}%")

# Ilości metali w gramach
st.subheader(translations[language]["current_metal_amounts_g"])

aktualne_ilosci_uncje = {
    "Gold": result.iloc[-1]["Gold"],
    "Silver": result.iloc[-1]["Silver"],
    "Platinum": result.iloc[-1]["Platinum"],
    "Palladium": result.iloc[-1]["Palladium"]
}

aktualne_ilosci_gramy = {
    metal: ilosc * TROY_OUNCE_TO_GRAM
    for metal, ilosc in aktualne_ilosci_uncje.items()
}

kolory_metali = {
    "Gold": "#D4AF37",
    "Silver": "#C0C0C0",
    "Platinum": "#E5E4E2",
    "Palladium": "#CED0DD"
}

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"<h4 style='color:{kolory_metali['Gold']}; text-align: center;'>{translations[language]['gold']}</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci_gramy['Gold']:.2f} {translations[language]['gram']}")
with col2:
    st.markdown(f"<h4 style='color:{kolory_metali['Silver']}; text-align: center;'>{translations[language]['silver']}</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci_gramy['Silver']:.2f} {translations[language]['gram']}")
with col3:
    st.markdown(f"<h4 style='color:{kolory_metali['Platinum']}; text-align: center;'>{translations[language]['platinum']}</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci_gramy['Platinum']:.2f} {translations[language]['gram']}")
with col4:
    st.markdown(f"<h4 style='color:{kolory_metali['Palladium']}; text-align: center;'>{translations[language]['palladium']}</h4>", unsafe_allow_html=True)
    st.metric(label="", value=f"{aktualne_ilosci_gramy['Palladium']:.2f} {translations[language]['gram']}")

# Podsumowanie finansowe
st.metric(translations[language]["capital_allocation"], f"{alokacja_kapitalu:,.2f} EUR")
st.metric(translations[language]["metals_sale_value"], f"{wartosc_metali:,.2f} EUR")

# Wartość zakupu metali dzisiaj
metale = ["Gold", "Silver", "Platinum", "Palladium"]
ilosc_metali = {metal: result.iloc[-1][metal] for metal in metale}

aktualne_ceny_z_marza = {
    metal: data.loc[result.index[-1], metal + "_EUR"] * (1 + margins[metal] / 100)
    for metal in metale
}

wartosc_zakupu_metali = sum(
    ilosc_metali[metal] * aktualne_ceny_z_marza[metal]
    for metal in metale
)

st.metric(translations[language]["metals_purchase_value"], f"{wartosc_zakupu_metali:,.2f} EUR")

if wartosc_zakupu_metali > 0:
    roznica_proc = ((wartosc_zakupu_metali / wartosc_metali) - 1) * 100
else:
    roznica_proc = 0.0

st.caption(translations[language]["difference_vs_portfolio"].format(roznica_proc))

# Średni wzrost
st.subheader(translations[language]["avg_annual_growth"])

weighted_start_price = sum(
    allocation[metal] * data.loc[result.index.min()][metal + "_EUR"]
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]
)

weighted_end_price = sum(
    allocation[metal] * data.loc[result.index.max()][metal + "_EUR"]
    for metal in ["Gold", "Silver", "Platinum", "Palladium"]
)

if weighted_start_price > 0 and years > 0:
    weighted_avg_annual_growth = (weighted_end_price / weighted_start_price) ** (1 / years) - 1
else:
    weighted_avg_annual_growth = 0.0

st.metric(translations[language]["weighted_avg_growth"], f"{weighted_avg_annual_growth * 100:.2f}%")

# Tabela uproszczona
st.subheader(translations[language]["simplified_view"])

result_filtered = result.groupby(result.index.year).first()
result_with_grams = result_filtered.copy()

for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
    result_with_grams[metal] = result_with_grams[metal] * TROY_OUNCE_TO_GRAM

simple_table = pd.DataFrame({
    translations[language]["invested_eur"]: result_with_grams["Invested"].round(0),
    translations[language]["portfolio_value_eur"]: result_with_grams["Portfolio Value"].round(0),
    translations[language]["gold_g"]: result_with_grams["Gold"].round(2),
    translations[language]["silver_g"]: result_with_grams["Silver"].round(2),
    translations[language]["platinum_g"]: result_with_grams["Platinum"].round(2),
    translations[language]["palladium_g"]: result_with_grams["Palladium"].round(2),
    translations[language]["action"]: result_with_grams["Akcja"].apply(translate_action)
})

simple_table[translations[language]["invested_eur"]] = simple_table[translations[language]["invested_eur"]].map(lambda x: f"{x:,.0f} EUR")
simple_table[translations[language]["portfolio_value_eur"]] = simple_table[translations[language]["portfolio_value_eur"]].map(lambda x: f"{x:,.0f} EUR")

st.markdown(
    simple_table.to_html(index=True, escape=False),
    unsafe_allow_html=True
)
st.markdown(
    """<style>
    table {
        font-size: 14px;
    }
    </style>""",
    unsafe_allow_html=True
)

# Podsumowanie kosztów magazynowania
storage_fees = result[result["Akcja"] == "storage_fee"]

# Sprawdź czy są jakiekolwiek koszty magazynowania
if not storage_fees.empty:
    # Upewnij się, że pobieramy wartość, a nie Series
    total_cost_series = storage_fees["Invested"] * (storage_fee / 100) * (1 + vat / 100)
    total_storage_cost = total_cost_series.sum()
else:
    total_storage_cost = 0.0

if years > 0:
    avg_annual_storage_cost = total_storage_cost / years
else:
    avg_annual_storage_cost = 0.0

# Sprawdź czy jest ostatnia data kosztów magazynowania
if not storage_fees.empty:
    last_storage_date = storage_fees.index.max()
    if pd.notna(last_storage_date):
        last_invested = result.loc[last_storage_date, "Invested"]
        last_storage_cost = float(last_invested * (storage_fee / 100) * (1 + vat / 100))
    else:
        last_storage_cost = 0.0
else:
    last_storage_cost = 0.0

current_portfolio_value = float(result["Portfolio Value"].iloc[-1])

if current_portfolio_value > 0 and last_storage_cost > 0:
    storage_cost_percentage = (last_storage_cost / current_portfolio_value) * 100
else:
    storage_cost_percentage = 0.0

st.subheader(translations[language]["storage_costs_summary"])

col1, col2 = st.columns(2)
with col1:
    st.metric(translations[language]["avg_annual_storage_cost"], f"{avg_annual_storage_cost:,.2f} EUR")
with col2:
    st.metric(translations[language]["storage_cost_percentage"], f"{storage_cost_percentage:.2f}%")
