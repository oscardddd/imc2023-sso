import pandas as pd


def anayze_2():
    # Path to your CSV file
    file_path = 'websites-DEV-all.csv'

    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path, header=None)

    # Extract the 3rd and the last column
    # third_column = df.iloc[:, 2]  # 3rd column has index 2
    last_column = df.iloc[:, -1]  # Last column
    print(last_column)

    print("Google SSO: ", sum(last_column))


def analyze_all():
    # Path to your CSV file
    file_path = 'websites-DEV-all.csv'

    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path, header=None)


    last_column = df.iloc[:, 10]  # Google is the 11th
    print(last_column)

    print("Google SSO: ", sum(last_column))
