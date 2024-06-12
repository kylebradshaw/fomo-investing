import argparse
import yfinance as yf
import pandas as pd
from datetime import datetime
from tabulate import tabulate
from termcolor import colored
import csv
import os
import re

HISTORY_FILE = 'portfolio_history.csv'

def parse_args():
    parser = argparse.ArgumentParser(description="Calculate portfolio value changes over a specified date range.")
    parser.add_argument('--portfolio', type=str, required=True, help="Portfolio of tickers and shares, e.g., 'VTSAX(485.113),VOO(40.000)'")
    parser.add_argument('--from', dest='frm', type=str, required=True, help="Start date in YYYY.MM.DD format")
    parser.add_argument('--to', type=str, required=False, help="End date in YYYY.MM.DD format. Defaults to previous market close.")
    parser.add_argument('--aggregate', action='store_true', help="Run aggregate of all historical executions")
    parser.add_argument('--save', action='store_true', help="Save this command to the historical file")
    return parser.parse_args()

def fetch_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date)
    return df

def parse_portfolio(portfolio_str):
    pattern = r"([A-Za-z]+)\(([\d\.]+)\)"
    matches = re.findall(pattern, portfolio_str)
    return [(ticker, float(shares)) for ticker, shares in matches]

def calculate_values(portfolio, start_date, end_date):
    data = []
    total_value_change = 0

    for ticker, shares in portfolio:
        df = fetch_stock_data(ticker, start_date, end_date)
        if df.empty:
            continue

        start_value = df.iloc[0]['Close'] * shares
        end_value = df.iloc[-1]['Close'] * shares
        percent_change = ((end_value - start_value) / start_value) * 100
        value_change = end_value - start_value
        total_value_change += value_change

        data.append([f"{ticker} ({shares})", start_value, end_value, percent_change, value_change])

    return data, total_value_change

def colorize_value(value):
    if value >= 0:
        return colored(f'{value:.2f}', 'green')
    else:
        return colored(f'{value:.2f}', 'red')

def print_results(data, start_date, end_date, total_value_change):
    df = pd.DataFrame(data, columns=['Ticker (Shares)', f'Start Value ({start_date})', f'End Value ({end_date})', 'Percent Change (%)', 'Value Change (USD)'])

    df['Percent Change (%)'] = df['Percent Change (%)'].apply(colorize_value)
    df['Value Change (USD)'] = df['Value Change (USD)'].apply(colorize_value)

    table = tabulate(df, headers='keys', tablefmt='fancy_grid', showindex=False)
    print(table)

    total_row = ['Total', '', '', '', colorize_value(total_value_change)]
    total_table = tabulate([total_row], headers=['Ticker (Shares)', f'Start Value ({start_date})', f'End Value ({end_date})', 'Percent Change (%)', 'Value Change (USD)'], tablefmt='fancy_grid', showindex=False)
    print(total_table)

def save_to_history(portfolio, start_date, end_date):
    history = load_history()

    # Remove any existing entry with the same portfolio and start_date
    history = [entry for entry in history if not (entry[0] == portfolio and entry[1] == start_date)]

    # Add the new entry
    history.append([portfolio, start_date, end_date])

    # Save the updated history
    with open(HISTORY_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['portfolio', 'start_date', 'end_date'])
        writer.writerows(history)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    with open(HISTORY_FILE, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        return list(reader)

def main():
    args = parse_args()

    if args.aggregate:
        history = load_history()
        for entry in history:
            portfolio_str, start_date, end_date = entry
            portfolio = parse_portfolio(portfolio_str)
            data, total_value_change = calculate_values(portfolio, start_date, end_date)
            print_results(data, start_date, end_date, total_value_change)
    else:
        start_date = args.frm.replace('.', '-')
        end_date = args.to

        # Convert dates from YYYY.MM.DD to YYYY-MM-DD format
        if end_date:
            end_date = end_date.replace('.', '-')
        else:
            end_date = datetime.now().strftime('%Y-%m-%d')

        portfolio = parse_portfolio(args.portfolio)
        data, total_value_change = calculate_values(portfolio, start_date, end_date)
        print_results(data, start_date, end_date, total_value_change)

        # Save the current execution to history if --save flag is used
        if args.save:
            save_to_history(args.portfolio, start_date, end_date)

if __name__ == "__main__":
    main()