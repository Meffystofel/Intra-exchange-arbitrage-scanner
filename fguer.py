with open('tax_analizer.txt', 'r') as file:
    lines = file.readlines()

# Видалення коїнів, що повторюються
unique_coins = list(set(line.strip() for line in lines))

# Сортування коїнів
unique_coins.sort()

# Запис унікальних коїнів у новий файл
with open('Unique_TAXER.txt', 'w') as file:
    for coin in unique_coins:
        file.write(coin + '\n')

print("Видалення повторюваних коїнів завершено. Результат записано у файл Unique_TAXER.txt.")