# symulator_metali.py

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

# Język w session_state
if "language" not in st.session_state:
    st.session_state.language = "Polski"

language_choice = st.sidebar.selectbox(
    "\U0001F310 Wybierz język / Sprache wählen",
    ("\ud83c\uddf5\ud83c\uddf1 Polski", "\ud83c\udde9\ud83c\uddea Deutsch"),
    index=0 if st.session_state.language == "Polski" else 1
)

new_language = "Polski" if "Polski" in language_choice else "Deutsch"
if new_language != st.session_state.language:
    st.session_state.language = new_language
    st.rerun()

language = st.session_state.language

# Wczytanie danych LBMA i inflacji
@st.cache_data
def load_data():
    df = pd.read_csv("lbma_data.csv", parse_dates=True, index_col=0).sort_index().dropna()
    return df

@st.cache_data
def load_inflation_data():
    df = pd.read_csv("inflacja.csv", sep=";", encoding="cp1250")
    df["Wartosc"] = df["Wartosc"].str.replace(",", ".").astype(float)
    df["Inflacja (%)"] = df["Wartosc"] - 100
    return df[["Rok", "Inflacja (%)"]]

data = load_data()
inflation_real = load_inflation_data()

# ====== WCZESNE WCZYTYWANIE PRESETU ======
PRESET_FOLDER = "presets"
os.makedirs(PRESET_FOLDER, exist_ok=True)

if "preset_loaded" not in st.session_state and "preset_to_load" in st.session_state:
    preset_path = os.path.join(PRESET_FOLDER, f"{st.session_state['preset_to_load']}.json")
    if os.path.exists(preset_path):
        with open(preset_path, "r", encoding="utf-8") as f:
            preset = json.load(f)

        # Alokacja
        st.session_state["alloc_Gold"] = preset["allocation"]["Gold"]
        st.session_state["alloc_Silver"] = preset["allocation"]["Silver"]
        st.session_state["alloc_Platinum"] = preset["allocation"]["Platinum"]
        st.session_state["alloc_Palladium"] = preset["allocation"]["Palladium"]

        # Daty
        st.session_state["initial_date_override"] = preset["initial_date"]
        st.session_state["end_purchase_date_override"] = preset["end_purchase_date"]

        # Zakupy cykliczne
        st.session_state["purchase_freq"] = preset["purchase"]["frequency"]
        st.session_state["purchase_day"] = preset["purchase"]["day"]
        st.session_state["purchase_amount"] = preset["purchase"]["amount"]

        # ReBalancing
        for k, v in preset["rebalance"].items():
            st.session_state[k] = v

        # Koszty magazynowania
        st.session_state["storage_fee"] = preset["storage"]["fee"]
        st.session_state["vat"] = preset["storage"]["vat"]
        st.session_state["storage_metal"] = preset["storage"]["metal"]

        # Marże
        for k, v in preset["margins"].items():
            st.session_state[f"margin_{k}"] = v

        # Odkup
        for k, v in preset["buyback"].items():
            st.session_state[f"buyback_{k}"] = v

        # ReBalance markup
        for k, v in preset["rebalance_markup"].items():
            st.session_state[f"rebalance_markup_{k}"] = v

        st.session_state["preset_loaded"] = True
    del st.session_state["preset_to_load"]

# ====== BLOK ZAPISU I WCZYTANIA PRESETU ======
with st.sidebar.expander("\ud83d\udcc2 Presety", expanded=False):
    preset_name = st.text_input("Nazwa presetu")

    if st.button("Zapisz preset"):
        preset_data = {
            "initial_allocation": st.session_state.get("initial_allocation", 100000.0),
            "initial_date": str(st.session_state.get("initial_date", datetime.today().date())),
            "end_purchase_date": str(st.session_state.get("end_purchase_date", datetime.today().date())),
            "allocation": {
                "Gold": st.session_state["alloc_Gold"],
                "Silver": st.session_state["alloc_Silver"],
                "Platinum": st.session_state["alloc_Platinum"],
                "Palladium": st.session_state["alloc_Palladium"]
            },
            "purchase": {
                "frequency": st.session_state.get("purchase_freq", "Miesiąc"),
                "day": st.session_state.get("purchase_day", 1),
                "amount": st.session_state.get("purchase_amount", 1000.0)
            },
            "rebalance": {
                k: st.session_state.get(k) for k in [
                    "rebalance_1", "rebalance_1_condition", "rebalance_1_threshold", "rebalance_1_start",
                    "rebalance_2", "rebalance_2_condition", "rebalance_2_threshold", "rebalance_2_start"
                ]
            },
            "storage": {
                "fee": st.session_state.get("storage_fee", 1.5),
                "vat": st.session_state.get("vat", 0.0),
                "metal": st.session_state.get("storage_metal", "Gold")
            },
            "margins": {
                k: st.session_state.get(f"margin_{k}", 0.0) for k in ["Gold", "Silver", "Platinum", "Palladium"]
            },
            "buyback": {
                k: st.session_state.get(f"buyback_{k}", 0.0) for k in ["Gold", "Silver", "Platinum", "Palladium"]
            },
            "rebalance_markup": {
                k: st.session_state.get(f"rebalance_markup_{k}", 0.0) for k in ["Gold", "Silver", "Platinum", "Palladium"]
            }
        }

        file_path = os.path.join(PRESET_FOLDER, f"{preset_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(preset_data, f, indent=2, ensure_ascii=False)

        st.success(f"Preset zapisany jako {preset_name}.json")

        json_str = json.dumps(preset_data, indent=2, ensure_ascii=False)
        st.download_button("\ud83d\udcc5 Pobierz preset jako plik JSON", json_str, file_name=f"{preset_name}.json", mime="application/json")

    # Lista presetów do wczytania
    preset_files = [f.replace(".json", "") for f in os.listdir(PRESET_FOLDER) if f.endswith(".json")]
    selected_preset = st.selectbox("\ud83d\udcc4 Wczytaj preset", options=[""] + preset_files)

    if selected_preset and st.button("Wczytaj preset"):
        st.session_state["preset_to_load"] = selected_preset
        st.rerun()

# Dalej kontynuuj kod aplikacji...
# Tutaj podłącz `initial_date`, `allocation`, `purchase_freq`, itp. z session_state,
# tak jak wcześniej – teraz już będą poprawnie nadpisywane po wczytaniu presetów.


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
    st.rerun()  # Przeładowanie strony po zmianie języka

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
    df = df[["Rok", "Wartosc"]].copy()
    df["Wartosc"] = df["Wartosc"].str.replace(",", ".").astype(float)
    df["Inflacja (%)"] = df["Wartosc"] - 100
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
        
        # Nowe tłumaczenia
        "page_title": "Symulator Metali Szlachetnych",
        "app_title": "Symulator ReBalancingu Portfela Metali Szlachetnych",
        "reset_allocation": "🔄 Resetuj do 40/20/20/20",
        "gold": "Złoto (Au)",
        "silver": "Srebro (Ag)",
        "platinum": "Platyna (Pt)",
        "palladium": "Pallad (Pd)",
        "allocation_error": "❗ Suma alokacji: {}% – musi wynosić dokładnie 100%, aby kontynuować.",
        "purchase_days_range": "✅ Zakres zakupów: {:.1f} lat.",
        "purchase_days_range_error": "⚠️ Zakres zakupów: tylko {:.1f} lat. (minimum 7 lat wymagane!)",
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
        # Istniejące tłumaczenia
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
        
        # Nowe tłumaczenia
        "page_title": "Edelmetalle-Simulator",
        "app_title": "Edelmetall-Portfolio ReBalancing-Simulator",
        "reset_allocation": "🔄 Zurücksetzen auf 40/20/20/20",
        "gold": "Gold (Au)",
        "silver": "Silber (Ag)",
        "platinum": "Platin (Pt)",
        "palladium": "Palladium (Pd)",
        "allocation_error": "❗ Summe der Zuteilung: {}% – muss genau 100% betragen, um fortzufahren.",
        "purchase_days_range": "✅ Kaufzeitraum: {:.1f} Jahre.",
        "purchase_days_range_error": "⚠️ Kaufzeitraum: nur {:.1f} Jahre. (mindestens 7 Jahre erforderlich!)",
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
        "metals_purchase_value": "🛒 Metallkaufswert",
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

# Funkcja do tłumaczenia akcji
def translate_action(action_str):
    if language not in action_translations:
        return action_str
        
    actions = action_str.split(", ")
    translated = []
    for action in actions:
        translated.append(action_translations[language].get(action, action))
    return ", ".join(translated)

# =========================================
# 3. Sidebar: Parametry użytkownika
# =========================================

# jeśli preset ustawił datę – nadpisz
if "initial_date_override" in st.session_state:
    initial_date = pd.to_datetime(st.session_state["initial_date_override"]).date()
    del st.session_state["initial_date_override"]



st.sidebar.header(translations[language]["simulation_settings"])

# Inwestycja: Kwoty i daty
st.sidebar.subheader(translations[language]["investment_amounts"])

today = datetime.today()
default_initial_date = today.replace(year=today.year - 20)

initial_allocation = st.sidebar.number_input(
    translations[language]["initial_allocation"], 
    value=100000.0, 
    step=100.0
)

initial_date = st.sidebar.date_input(
    translations[language]["first_purchase_date"], 
    value=default_initial_date.date(), 
    min_value=data.index.min().date(), 
    max_value=data.index.max().date()
)

# Wyznacz minimalną datę końca (initial_date + 7 lat)
min_end_date = (pd.to_datetime(initial_date) + pd.DateOffset(years=7)).date()

if min_end_date > data.index.max().date():
    min_end_date = data.index.max().date()

end_purchase_date = st.sidebar.date_input(
    translations[language]["last_purchase_date"],
    value=data.index.max().date(), 
    min_value=min_end_date, 
    max_value=data.index.max().date()
)

# Obliczenie liczby lat zakupów
days_difference = (pd.to_datetime(end_purchase_date) - pd.to_datetime(initial_date)).days
years_difference = days_difference / 365.25  # uwzględnia przestępne lata

# ✅ / ⚠️ Dynamiczny komunikat
if years_difference >= 7:
    st.sidebar.success(translations[language]["purchase_days_range"].format(years_difference))
    dates_valid = True
else:
    st.sidebar.error(translations[language]["purchase_days_range_error"].format(years_difference))
    dates_valid = False

# Opcjonalnie: przycisk Start Symulacji
if dates_valid:
    start_simulation = st.sidebar.button(translations[language]["start_simulation"])
else:
    st.sidebar.button(translations[language]["start_simulation"], disabled=True)
    
# Alokacja metali
st.sidebar.subheader(translations[language]["metal_allocation"])

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

purchase_freq = st.sidebar.selectbox(
    translations[language]["purchase_frequency"], 
    purchase_freq_options, index=1
)

if purchase_freq == translations[language]["week"]:
    days_of_week = [
        translations[language]["monday"], 
        translations[language]["tuesday"], 
        translations[language]["wednesday"], 
        translations[language]["thursday"], 
        translations[language]["friday"]
    ]
    selected_day = st.sidebar.selectbox(translations[language]["purchase_day_of_week"], days_of_week, index=0)
    # Mapowanie na indeksy dni tygodnia (0-4 dla poniedziałek-piątek)
    purchase_day = days_of_week.index(selected_day)
    default_purchase_amount = 250.0
elif purchase_freq == translations[language]["month"]:
    purchase_day = st.sidebar.number_input(translations[language]["purchase_day_of_month"], min_value=1, max_value=28, value=1)
    default_purchase_amount = 1000.0
elif purchase_freq == translations[language]["quarter"]:
    purchase_day = st.sidebar.number_input(translations[language]["purchase_day_of_quarter"], min_value=1, max_value=28, value=1)
    default_purchase_amount = 3250.0
else:
    purchase_day = None
    default_purchase_amount = 0.0

purchase_amount = st.sidebar.number_input(translations[language]["purchase_amount"], value=default_purchase_amount, step=50.0)

# ========================
# ReBalancing
# ========================

# Domyślne daty ReBalancingu bazujące na dacie pierwszego zakupu
rebalance_base_year = initial_date.year + 1

rebalance_1_default = datetime(rebalance_base_year, 4, 1)
rebalance_2_default = datetime(rebalance_base_year, 10, 1)

with st.sidebar.expander(translations[language]["rebalancing"], expanded=False):
    rebalance_1 = st.checkbox(translations[language]["rebalance_1"], value=True)
    rebalance_1_condition = st.checkbox(translations[language]["deviation_condition_1"], value=False)
    rebalance_1_threshold = st.number_input(
        translations[language]["deviation_threshold_1"], 
        min_value=0.0, max_value=100.0, value=12.0, step=0.5
    )
    rebalance_1_start = st.date_input(
        translations[language]["start_rebalance"] + " 1",
        value=rebalance_1_default.date(),
        min_value=data.index.min().date(),
        max_value=data.index.max().date()
    )

    rebalance_2 = st.checkbox(translations[language]["rebalance_2"], value=False)
    rebalance_2_condition = st.checkbox(translations[language]["deviation_condition_2"], value=False)
    rebalance_2_threshold = st.number_input(
        translations[language]["deviation_threshold_2"], 
        min_value=0.0, max_value=100.0, value=12.0, step=0.5
    )
    rebalance_2_start = st.date_input(
        translations[language]["start_rebalance"] + " 2",
        value=rebalance_2_default.date(),
        min_value=data.index.min().date(),
        max_value=data.index.max().date()
    )

# ========================
# Koszty magazynowania
# ========================

storage_metal_options = [
    "Gold", "Silver", "Platinum", "Palladium", 
    translations[language]["best_of_year"], 
    translations[language]["all_metals"]
]


with st.sidebar.expander(translations[language]["storage_costs"], expanded=False):
    storage_fee = st.number_input(translations[language]["annual_storage_fee"], value=1.5)
    vat = st.number_input(translations[language]["vat"], value=0.0)
    storage_metal = st.selectbox(
        translations[language]["metal_for_costs"],
        storage_metal_options
    )

# ========================
# Marże i prowizje
# ========================
with st.sidebar.expander(translations[language]["margins_fees"], expanded=False):
    margins = {
        "Gold": st.number_input(translations[language]["gold_margin"], value=15.6),
        "Silver": st.number_input(translations[language]["silver_margin"], value=18.36),
        "Platinum": st.number_input(translations[language]["platinum_margin"], value=24.24),
        "Palladium": st.number_input(translations[language]["palladium_margin"], value=22.49)
    }

# ========================
# Ceny odkupu
# ========================
with st.sidebar.expander(translations[language]["buyback_prices"], expanded=False):
    buyback_discounts = {
        "Gold": st.number_input(translations[language]["gold_buyback"], value=-1.5, step=0.1),
        "Silver": st.number_input(translations[language]["silver_buyback"], value=-3.0, step=0.1),
        "Platinum": st.number_input(translations[language]["platinum_buyback"], value=-3.0, step=0.1),
        "Palladium": st.number_input(translations[language]["palladium_buyback"], value=-3.0, step=0.1)
    }

# ========================
# Ceny ReBalancingu
# ========================
with st.sidebar.expander(translations[language]["rebalance_prices"], expanded=False):
    rebalance_markup = {
        "Gold": st.number_input(translations[language]["gold_rebalance"], value=6.5, step=0.1),
        "Silver": st.number_input(translations[language]["silver_rebalance"], value=6.5, step=0.1),
        "Platinum": st.number_input(translations[language]["platinum_rebalance"], value=6.5, step=0.1),
        "Palladium": st.number_input(translations[language]["palladium_rebalance"], value=6.5, step=0.1)
    }

# ========================
# Presets
# ========================


with st.sidebar.expander("💾 Presety", expanded=False):
    import json
    import os

    PRESET_FOLDER = "presets"
    os.makedirs(PRESET_FOLDER, exist_ok=True)

    preset_name = st.text_input("Nazwa presetu")

    if st.button("Zapisz preset"):
        preset_data = {
            "initial_allocation": initial_allocation,
            "initial_date": str(initial_date),
            "end_purchase_date": str(end_purchase_date),
            "allocation": {
                "Gold": st.session_state["alloc_Gold"],
                "Silver": st.session_state["alloc_Silver"],
                "Platinum": st.session_state["alloc_Platinum"],
                "Palladium": st.session_state["alloc_Palladium"],
            },
            "purchase": {
                "frequency": purchase_freq,
                "day": purchase_day,
                "amount": purchase_amount,
            },
            "rebalance": {
                "rebalance_1": rebalance_1,
                "rebalance_1_condition": rebalance_1_condition,
                "rebalance_1_threshold": rebalance_1_threshold,
                "rebalance_1_start": str(rebalance_1_start),
                "rebalance_2": rebalance_2,
                "rebalance_2_condition": rebalance_2_condition,
                "rebalance_2_threshold": rebalance_2_threshold,
                "rebalance_2_start": str(rebalance_2_start),
            },
            "storage": {
                "fee": storage_fee,
                "vat": vat,
                "metal": storage_metal
            },
            "margins": margins,
            "buyback": buyback_discounts,
            "rebalance_markup": rebalance_markup
        }

        # Zapis do folderu
        file_path = os.path.join(PRESET_FOLDER, f"{preset_name}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(preset_data, f, indent=2, ensure_ascii=False)

        st.success(f"Preset zapisany jako {preset_name}.json")

        # Przycisk pobrania pliku
        json_str = json.dumps(preset_data, indent=2, ensure_ascii=False)
        st.download_button("📥 Pobierz preset jako plik JSON", json_str, file_name=f"{preset_name}.json", mime="application/json")

    # Lista presetów
    preset_files = [f.replace(".json", "") for f in os.listdir(PRESET_FOLDER) if f.endswith(".json")]
    selected_preset = st.selectbox("📂 Wczytaj preset", options=[""] + preset_files)

    if selected_preset and st.button("Wczytaj preset"):
        path = os.path.join(PRESET_FOLDER, f"{selected_preset}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            st.session_state["alloc_Gold"] = loaded["allocation"]["Gold"]
            st.session_state["alloc_Silver"] = loaded["allocation"]["Silver"]
            st.session_state["alloc_Platinum"] = loaded["allocation"]["Platinum"]
            st.session_state["alloc_Palladium"] = loaded["allocation"]["Palladium"]
            st.session_state["initial_date_override"] = loaded["initial_date"]
            st.session_state["preset_loaded"] = loaded
            st.rerun()
        except Exception as e:
            st.error(f"Błąd podczas wczytywania: {e}")




# =========================================
# 3. Funkcje pomocnicze (rozbudowane)
# =========================================

def generate_purchase_dates(start_date, freq, day, end_date):
    dates = []
    current = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)  # upewniamy się, że end_date jest typu datetime

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

    # Brak zakupów jeśli "Brak"/"Keine"
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

            # Uwzględniamy tłumaczenia dla opcji "Best of year" i "ALL"
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
        "Akcja": h[3]  # Można później przetłumaczyć tę kolumnę używając action_translations
    } for h in history]).set_index("Date")

    return df_result

# =========================================
# 4. Główna sekcja aplikacji
# =========================================

st.title(translations[language]["app_title"])
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

# Nagłówki bardziej czytelne (opcjonalnie) - z tłumaczeniami
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

st.subheader(translations[language]["metal_price_growth"])

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
    st.metric(translations[language]["gold"], f"{wzrosty['Gold']:.2f}%")
with col2:
    st.metric(translations[language]["silver"], f"{wzrosty['Silver']:.2f}%")
with col3:
    st.metric(translations[language]["platinum"], f"{wzrosty['Platinum']:.2f}%")
with col4:
    st.metric(translations[language]["palladium"], f"{wzrosty['Palladium']:.2f}%")

st.subheader(translations[language]["current_metal_amounts_g"])

# Aktualne ilości uncji z ostatniego dnia
aktualne_ilosci_uncje = {
    "Gold": result.iloc[-1]["Gold"],
    "Silver": result.iloc[-1]["Silver"],
    "Platinum": result.iloc[-1]["Platinum"],
    "Palladium": result.iloc[-1]["Palladium"]
}

# Konwersja na gramy
aktualne_ilosci_gramy = {
    metal: ilosc * TROY_OUNCE_TO_GRAM 
    for metal, ilosc in aktualne_ilosci_uncje.items()
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

st.metric(translations[language]["capital_allocation"], f"{alokacja_kapitalu:,.2f} EUR")
st.metric(translations[language]["metals_sale_value"], f"{wartosc_metali:,.2f} EUR")

# 🛒 Wartość zakupu metali dziś (uwzględniając aktualne ceny + marże)
metale = ["Gold", "Silver", "Platinum", "Palladium"]

# Ilość posiadanych uncji na dziś
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
st.metric(translations[language]["metals_purchase_value"], f"{wartosc_zakupu_metali:,.2f} EUR")

# 🧮 Opcjonalnie: różnica procentowa
if wartosc_zakupu_metali > 0:
    roznica_proc = ((wartosc_zakupu_metali / wartosc_metali) - 1) * 100
else:
    roznica_proc = 0.0

st.caption(translations[language]["difference_vs_portfolio"].format(roznica_proc))

st.subheader(translations[language]["avg_annual_growth"])

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
st.metric(translations[language]["weighted_avg_growth"], f"{weighted_avg_annual_growth * 100:.2f}%")

st.subheader(translations[language]["simplified_view"])

# Grupujemy po roku i bierzemy pierwszy dzień roboczy
result_filtered = result.groupby(result.index.year).first()

# Konwersja z uncji na gramy dla tabeli
result_with_grams = result_filtered.copy()
for metal in ["Gold", "Silver", "Platinum", "Palladium"]:
    result_with_grams[metal] = result_with_grams[metal] * TROY_OUNCE_TO_GRAM

# Tworzymy prostą tabelę z wybranymi kolumnami
simple_table = pd.DataFrame({
    translations[language]["invested_eur"]: result_with_grams["Invested"].round(0),
    translations[language]["portfolio_value_eur"]: result_with_grams["Portfolio Value"].round(0),
    translations[language]["gold_g"]: result_with_grams["Gold"].round(2),
    translations[language]["silver_g"]: result_with_grams["Silver"].round(2),
    translations[language]["platinum_g"]: result_with_grams["Platinum"].round(2),
    translations[language]["palladium_g"]: result_with_grams["Palladium"].round(2),
    translations[language]["action"]: result_with_grams["Akcja"].apply(translate_action)
})

# Formatowanie EUR bez miejsc po przecinku
simple_table[translations[language]["invested_eur"]] = simple_table[translations[language]["invested_eur"]].map(lambda x: f"{x:,.0f} EUR")
simple_table[translations[language]["portfolio_value_eur"]] = simple_table[translations[language]["portfolio_value_eur"]].map(lambda x: f"{x:,.0f} EUR")

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

st.subheader(translations[language]["storage_costs_summary"])

col1, col2 = st.columns(2)
with col1:
    st.metric(translations[language]["avg_annual_storage_cost"], f"{avg_annual_storage_cost:,.2f} EUR")
with col2:
    st.metric(translations[language]["storage_cost_percentage"], f"{storage_cost_percentage:.2f}%")
