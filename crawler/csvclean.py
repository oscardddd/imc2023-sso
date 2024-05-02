import pandas as pd

# Load the CSV file
df = pd.read_csv('de.csv')

# Drop the 'country_code' column
df = df.drop(columns=['country_code'])

# Save the result to a new CSV file
df.to_csv('de1.csv', index=False)