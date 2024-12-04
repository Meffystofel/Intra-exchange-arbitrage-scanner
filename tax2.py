
api_key = "your_api_key"
secret_key = "your_secret_key"
from binance.client import Client

import datetime
from datetime import datetime
import datetime as dt
import requests
client = Client(api_key, secret_key)
import os


def get_agg_trades(symbol, start_date):
    url = f"https://api.binance.com/api/v3/aggTrades"
    params = {
        "symbol": symbol,
        "startTime": start_date,
        "limit": 1000  
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        trades = response.json()
        return trades
    except requests.exceptions.RequestException as e:
        print(f"Error fetching agg trades for {symbol}: {e}")
        return []

def get_historical_klines(symbol, interval, start_time, end_time):
    url = f"https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical klines for {symbol}: {e}")
        return []

def date_to_milliseconds(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    epoch = datetime.utcfromtimestamp(0)
    return int((dt - epoch).total_seconds() * 1000.0)

def calculate_commission(amount, commission_rate):
    return amount * commission_rate

# Функція для розрахунку податкової ставки для кожної угоди
def calculate_tax_rate_per_trade(trade_history, commission_rate, symbol, new_variable, first_part):
    base_currencies = ['BTC', 'ETH', 'BNB', 'PAX', 'GBP', 'AUD', 'USDT', 'USDC', 'USD', 'FDUSD']

    for trade in trade_history:
        trade_symbol = symbol
        base_currency = None
        quote_currency = None


        for base in base_currencies:
            if trade_symbol.endswith(base):
                base_currency = base
                quote_currency = trade_symbol.replace(base, '')
                break
        

        trade_volume = float(trade['q']) * float(trade['p'])

        commission = trade_volume * commission_rate
        commission_asset = base
        
        if commission_asset != 'USDT':
            timestamp = datetime.fromtimestamp(trade['T'] / 1000).strftime("%Y-%m-%d %H:%M:%S")
            start_time = date_to_milliseconds(timestamp)
            end_time = start_time + 60000 


            asset_usdt_klines = get_historical_klines(f"{commission_asset}USDT", "1m", start_time, end_time)
            if not asset_usdt_klines:
                continue
            asset_usdt_price = float(asset_usdt_klines[0][4])  


            adx_eth_klines = get_historical_klines(symbol, "1m", start_time, end_time)
            eth_usdt_klines = get_historical_klines(new_variable, "1m", start_time, end_time)
            if not adx_eth_klines or not eth_usdt_klines:
                continue


            adx_eth_price = float(adx_eth_klines[0][4])  
            eth_usdt_price = float(eth_usdt_klines[0][4])  


            adx_amount = float(trade['q'])


            eth_amount = adx_amount * adx_eth_price

            adx_eth_commission = calculate_commission(eth_amount, 0.0)
            eth_amount_after_commission = eth_amount - adx_eth_commission


            usdt_amount = eth_amount_after_commission * eth_usdt_price


            eth_usdt_commission = calculate_commission(usdt_amount, 0.0)
            usdt_amount_after_commission = usdt_amount - eth_usdt_commission
            print(f"Кількість {adx_amount} {first_part} на {timestamp}:")
            print(f"Підсумкова сума після перерахунку в USDT: {usdt_amount_after_commission:.2f} USDT")

            commission_in_usdt = commission * asset_usdt_price
        else:
            usdt_amount_after_commission = trade_volume
            commission_in_usdt = commission

        tax_rate = commission_in_usdt / usdt_amount_after_commission
        procent_tax_rate = tax_rate * 100
        
        tax_info = {
            'trade_id': trade['a'],
            'trade_volume': usdt_amount_after_commission,
            'tax_rate': tax_rate,
            'commission': commission,
            'commission_in_usdt': commission_in_usdt,
            'commission_asset': commission_asset,
            'procent_tax_rate': procent_tax_rate
        }

        yield tax_info

def process_symbols(file_path):
    base_currencies = ['BTC', 'ETH', 'BNB', 'PAX', 'GBP', 'AUD', 'USDT', 'USDC', 'USD', 'FDUSD']
    results = []

    with open(file_path, 'r', encoding='utf-8') as file:
        symbols = [line.strip() for line in file.readlines()]

    for symbol in symbols:
        first_part = ''
        second_part = ''

        for base in base_currencies:
            if symbol.endswith(base):
                second_part = base
                first_part = symbol.replace(base, '')
                break

        new_variable = second_part + 'USDT'
        start_date = int(datetime(2024, 6, 1).timestamp() * 1000)
        trade_history = get_agg_trades(symbol, start_date)
        commission_rate = 0.001  # 0.1% commission

        tax_rates = []
        for i, tax_info in enumerate(calculate_tax_rate_per_trade(trade_history, commission_rate, symbol, new_variable, first_part)):
            if i >= 5:
                break
            tax_rates.append(tax_info['tax_rate'])
            print(f"Trade ID: {tax_info['trade_id']}")
            print(f"Trade Volume: {tax_info['trade_volume']:.8f} USDT")
            print(f"Tax Rate: {tax_info['tax_rate']:.8f} USDT or {tax_info['procent_tax_rate']:.8f}%")
            print(f"Commission: {tax_info['commission']:.8f} {tax_info['commission_asset']}")
            print(f"Commission in USDT: {tax_info['commission_in_usdt']:.8f} USDT")
            print("")

            if tax_rates:
                average_tax_rate = sum(tax_rates) / len(tax_rates)
                print(f"Average Tax Rate for {symbol}: {average_tax_rate:.8f} USDT")
            results.append(f"{symbol}: {average_tax_rate:.8f} USDT")
        print("")

    # Write results to a new file
    output_file_path = 'average_tax_rates.txt'
    try:
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            for result in results:
                output_file.write(result + "\n")
        print(f"Results successfully written to {output_file_path}")
    except Exception as e:
        print(f"Failed to write results to {output_file_path}: {e}")

if __name__ == "__main__":
    process_symbols('Unique_TAXER.txt')