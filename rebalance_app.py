def apply_rebalance(d, label, condition_enabled, threshold_percent):
    prices = data.loc[d]
    total_value = sum(prices[m + "_EUR"] * portfolio[m] for m in allocation)
    current_values = {m: prices[m + "_EUR"] * portfolio[m] for m in allocation}
    target_values = {m: total_value * allocation[m] for m in allocation}
    
    # Sprawdzenie warunku wyzwolenia ReBalancingu
    rebalance_trigger = False
    for metal in allocation:
        current_share = current_values[metal] / total_value
        target_share = allocation[metal]
        deviation = abs(current_share - target_share)
        if deviation >= (threshold_percent / 100):
            rebalance_trigger = True
            break

    if condition_enabled and not rebalance_trigger:
        return f"rebalancing_skipped_{label}"

    # Korekta wartości portfela do alokacji początkowej
    cash = 0.0

    # 1. Sprzedaż nadwyżek
    for metal in allocation:
        if current_values[metal] > target_values[metal]:
            value_to_sell = current_values[metal] - target_values[metal]
            sell_price = prices[metal + "_EUR"] * (1 + buyback_discounts[metal] / 100)
            grams_to_sell = value_to_sell / sell_price
            portfolio[metal] -= grams_to_sell
            cash += value_to_sell  # Wartość uzyskana ze sprzedaży to wartość "przeliczona", nie oryginalna gramatura!

    # 2. Zakup brakujących metali
    for metal in allocation:
        if current_values[metal] < target_values[metal]:
            value_to_buy = target_values[metal] - current_values[metal]
            buy_price = prices[metal + "_EUR"] * (1 + rebalance_markup[metal] / 100)
            grams_to_buy = value_to_buy / buy_price
            portfolio[metal] += grams_to_buy
            cash -= value_to_buy

    return label
