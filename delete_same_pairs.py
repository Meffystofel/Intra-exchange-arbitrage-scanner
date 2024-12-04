# Read the file and filter out coins with 'USDT' in their names
file_path = 'all_coins.txt'

with open(file_path, 'r') as file:
    coins = file.readlines()

# Filter out coins that end with 'USDT'
filtered_coins = [coin for coin in coins if not coin.strip().endswith('USDT')]

# Write the filtered coins back to a new file
filtered_file_path = 'filtered_coins(usdt).txt'

with open(filtered_file_path, 'w') as filtered_file:
    filtered_file.writelines(filtered_coins)

filtered_file_path