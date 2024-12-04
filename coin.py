# --------------------------------------------- #
# analysis of all intra-exchange transactions   #
#               coded by AркаДій                #
# --------------------------------------------- #

import time
import threading
from binance.client import Client as binanceClient
import requests
from concurrent.futures import ThreadPoolExecutor
import math
import re
# Binance API keys
api_key = "your_key"
secret_key = "your_secret_key"

# Initialize Binance client
client = binanceClient(api_key, secret_key)

extract_unique_endings = ['BTC', 'ETH', 'BNB', 'PAX', 'GBP', 'AUD', 'USDT', 'USDC', 'USD', 'FDUSD']

def remove_currency_suffix(symbol, currency_endings):
    for ending in currency_endings:
        if symbol.endswith(ending):
            return symbol.replace(ending, ''), ending
    return symbol, ''

def fetch_order_book(symbol):
    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=5"
    response = requests.get(url)
    data = response.json()
    if 'asks' in data and data['asks'] and 'bids' in data and data['bids']:
        ask_price = float(data['asks'][0][0])
        ask_qty = float(data['asks'][0][1])
        bid_price = float(data['bids'][0][0])
        bid_qty = float(data['bids'][0][1])
        return {
            'symbol': symbol,
            'ask_price': ask_price,
            'ask_qty': ask_qty,
            'bid_price': bid_price,
            'bid_qty': bid_qty
        }
    return None

def get_conversion_rate(coin_pair):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={coin_pair}"
    response = requests.get(url)
    data = response.json()
    if 'price' in data:
        return float(data['price'])
    else:
        return None

def convert_usdt(amount_usdt, coin_pair):
    rate = get_conversion_rate(coin_pair)
    if rate is not None:
        return amount_usdt / rate
    else:
        return 0
def fetch_coin_popularity(symbol):
    url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
    response = requests.get(url)
    data = response.json()
    if 'volume' in data:
        return float(data['volume'])
    return 0

# Список валют для конвертації
coins = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "PAXUSDT", "GBPUSDT", "AUDUSDT", "USDCUSDT", "USDUSDT", "FDUSDUSDT"]

# Сума в USDT для конвертації
amount_usdt = 650

# Threshold for popularity to consider the trade as practically guaranteed
POPULARITY_THRESHOLD = 50000

lock = threading.Lock()

# Список для відстеження вигідних угод
profitable_trades = []

def update_duration():
    global profitable_trades
    while True:
        with lock:
            for trade in profitable_trades[:]:
                trade['current_duration'] = time.time() - trade['start_time']
                # Recalculate the current profit
                initial_profit = trade['initial_profit']
                symbols_set = trade['symbols_set']
                # Fetch latest order books to update profit
                order_books = [fetch_order_book(symbol) for symbol in symbols_set[1:]]
                if None not in order_books:
                    currency, base_currency0 = remove_currency_suffix(symbols_set[1], extract_unique_endings)
                    current_amount = trade['converted_amount'] / order_books[0]['ask_price']
                    final_amount_usdt = current_amount * order_books[1]['bid_price']
                    trade['profit'] = final_amount_usdt - trade['start_amount_usdt']
                    # Remove the trade if it becomes unprofitable
                    if trade['profit'] <= 0:
                        print(f"Вигідну угоду завершено (стала мінусовою): {symbols_set}, Тривалість: {trade['current_duration']:.2f} секунд, Прибуток: {trade['profit']:.2f} USDT")
                        profitable_trades.remove(trade)
                        continue
                print(f"Вигідна угода триває: {symbols_set}, Поточна тривалість: {trade['current_duration']:.2f} секунд, Поточний прибуток: {initial_profit:.2f} USDT, Поточний прибуток: {trade['profit']:.2f} USDT")
        time.sleep(1)




def calculate_fee(pair, amount_usdt):
    price_info = client.get_symbol_ticker(symbol=pair)
    price = float(price_info['price'])

    account_info = client.get_account()
    trade_fee = client.get_trade_fee(symbol=pair)
    taker_fee_rate = float(trade_fee[0]['takerCommission']) / 10000
    maker_fee_rate = float(trade_fee[0]['makerCommission']) / 10000

    tax_rate_file = 'average_rates_TAXE.txt'
    with open(tax_rate_file, 'r') as file:
        data = file.read()

    pattern = rf"{pair}: ([0-9.]+) USDT"
    match = re.search(pattern, data)
    if match:
        tax_rate = float(match.group(1))
    else:
        raise ValueError(f"Tax rate for {pair} not found in {tax_rate_file}")

    quantity = amount_usdt / price
    notional_value = price * quantity
    standard_commission = notional_value * taker_fee_rate
    tax_commission = notional_value * tax_rate
    total_commission = standard_commission + tax_commission


    return total_commission

    

def calculate_arbitrage_for_set(symbols_set):
    global profitable_trades
    order_books = []
    for symbol in symbols_set:
        order_book = fetch_order_book(symbol)
        if order_book is None:
            return
        order_books.append(order_book)
    currency, base_currency0 = remove_currency_suffix(symbols_set[0], extract_unique_endings)
    third_currency = f"{base_currency0}USDT"
    new_symbols_set = [third_currency] + symbols_set


    order_books2 = []
    for symbol2 in new_symbols_set:
        order_book2 = fetch_order_book(symbol2)
        if order_book2 is None:
            return
        order_books2.append(order_book2)

        fees_usdt = []
        for pair in new_symbols_set:
            fee_usdt = calculate_fee(pair, amount_usdt)
            fees_usdt.append(fee_usdt)

            first_coin_fee = fees_usdt[0] if len(fees_usdt) > 0 else 0
            second_coin_fee = fees_usdt[1] if len(fees_usdt) > 1 else 0
            third_coin_fee = fees_usdt[2] if len(fees_usdt) > 2 else 0

            start_amount_usdt = amount_usdt - first_coin_fee

            second_pair = symbols_set[0]
            converted_amount = convert_usdt(start_amount_usdt, f"{base_currency0}USDT")
            current_amount = converted_amount / order_books[0]['ask_price']

            current_amount2 = current_amount - second_coin_fee

            third_pair = symbols_set[1]

            final_amount_usdt = current_amount2 * order_books[1]['bid_price']
            final_amount_usdt2 = final_amount_usdt - third_coin_fee

            currency, base_currency = remove_currency_suffix(symbols_set[1], extract_unique_endings)
            profit = final_amount_usdt2 - start_amount_usdt
            print(new_symbols_set, 'have:', profit)

            # Wait for a specified interval before updating again

    
            with lock:
                if profit > 0:
                    trade_exists = False
                    for trade in profitable_trades:
                        if trade['symbols_set'] == new_symbols_set:
                            trade_exists = True
                            trade['profit'] = profit
                            break

                    if not trade_exists:
                        popularity = fetch_coin_popularity(symbols_set[0])
                        practically_guaranteed = popularity >= POPULARITY_THRESHOLD
                        practically_guaranteed_msg = " (практично гарантовано)" if practically_guaranteed else ""
                        profitable_trades.append({
                            'symbols_set': new_symbols_set,
                            'start_time': time.time(),
                            'current_duration': 0,
                            'start_amount_usdt': start_amount_usdt,
                            'converted_amount': converted_amount,
                            'initial_profit': profit,
                            'profit': profit,
                            'popularity': popularity,
                            'converted_currency_amounts': {
                                symbols_set[0]: converted_amount,
                                symbols_set[1]: current_amount
                            }
                        })
                        print(f"Вигідну угоду знайдено: {new_symbols_set}, Поточна тривалість: 0.00 секунд, Прибуток: {profit:.2f} USDT, Проміжні суми: {symbols_set[0]}: {converted_amount:.6f}, {symbols_set[1]}: {current_amount:.6f}, Популярність: {popularity}{practically_guaranteed_msg}")
                        with open("arbitrage_profits2.txt", "a") as file:
                            file.write(f"Arbitrage pair: {new_symbols_set}, Profit: {profit:.2f} USDT, Проміжні суми: {symbols_set[0]}: {converted_amount:.6f}, {symbols_set[1]}: {current_amount:.6f}, Популярність: {popularity}{practically_guaranteed_msg}\n")
                else:
                    for trade in profitable_trades:
                        if trade['symbols_set'] == new_symbols_set:
                            duration = time.time() - trade['start_time']
                            print(f"Вигідну угоду завершено: {new_symbols_set}, Тривалість: {duration:.2f} секунд, Прибуток: {trade['profit']:.2f} USDT")
                            profitable_trades.remove(trade)
                            break


duration_thread = threading.Thread(target=update_duration)
duration_thread.daemon = True
duration_thread.start()

def main():
    symbols_sets = []
    with open("filtered_coins_output_pairs_simplified03.txt", "r") as file:
        for line in file:
            symbols_set = line.strip().split(", ")
            symbols_sets.append(symbols_set)
    
    while True:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(calculate_arbitrage_for_set, symbols_set) for symbols_set in symbols_sets]
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    pass
        time.sleep(1)

if __name__ == "__main__":
    main()



