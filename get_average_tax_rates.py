def calculate_average_rates(input_file, output_file):
    rates = {}
    counts = {}

    # Читаємо файл і обробляємо дані
    with open(input_file, 'r') as file:
        for line in file:
            coin, value = line.split(': ')
            value = float(value.replace(' USDT', ''))

            if coin in rates:
                rates[coin] += value
                counts[coin] += 1
            else:
                rates[coin] = value
                counts[coin] = 1

    # Обчислюємо середні значення
    averages = {coin: rates[coin] / counts[coin] for coin in rates}

    # Записуємо результати в новий файл
    with open(output_file, 'w') as file:
        for coin, avg in averages.items():
            file.write(f'{coin}: {avg:.8f} USDT\n')

# Приклад використання
input_file = 'average_tax_rates.txt'
output_file = 'average_rates_TAXE.txt'
calculate_average_rates(input_file, output_file)