# Define the file paths
all_coins_file_path = "filtered_coins(all).txt"
unique_endings_file_path = "extract_unique_endings.txt"

# Read the files
with open(all_coins_file_path, 'r') as file:
    all_coins = file.read().splitlines()

with open(unique_endings_file_path, 'r') as file:
    unique_endings = file.read().split()

# Prepare the output list
output_pairs = []

# Create the pairs
for coin in all_coins:
    # Remove the ending if it matches one from the unique_endings list
    for ending in unique_endings:
        if coin.endswith(ending):
            base_coin = coin[:-len(ending)]
            output_pairs.append(f"{coin}, {base_coin}USDT")
            break

# Write the output to a new file
output_file_path = "filtered_coins_output_pairs_simplified02.txt"
with open(output_file_path, 'w') as file:
    for pair in output_pairs:
        file.write(f"{pair}\n")

output_file_path