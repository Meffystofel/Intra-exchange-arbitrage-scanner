# Intra-exchange-arbitrage-scanner 
After filtering the filtered_coins_output_pairs_simplified02 list, we get filtered_coins_output_pairs_simplified03, which is used to created trading pairs.
The code takes into account the average tax_rate, which makes the calculation more accurate. The peculiarity of this code is that it rechecks the tested pairs within some radius from the tested pair
In practice, the code is of no value, because the exchange limits selling in step-size, so arbitrage is inexpedient, just like on other exchanges.
The code is written for introductory purposes. Run via coin.py


https://github.com/user-attachments/assets/238dc822-85e4-4575-a132-88a39f0b1794

