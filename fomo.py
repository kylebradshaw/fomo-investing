import argparse
import yfinance as yf
import pandas as pd
from datetime import datetime
from tabulate import tabulate
from termcolor import colored

def parse_args():
    parser = argparse.ArgumentParser(description="Calculate portfolio value changes over a specified date range.")
    parser.add_argument('--portfolio', type=str, required=True, help="Portfolio of tickers and shares, e.g., '485.113-VTSAX,40.000-VOO'")
    parser.add_argument('--from', dest='frm', type=str, required=True, help="Start date in YYYY.MM.DD format")
    parser.add_argument('--to', type=str, required=False, help="End date in YYYY.MM.DD format. Defaults to previous market close.")
    return parser.parse_args()

def fetch_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    df = stock.history(start=start_date, end=end_date)
    return df

def calculate_values(portfolio, start_date, end_date):
    data = []
    total_value_change = 0

    for item in portfolio.split(','):
        shares, ticker = item.split('-')
        shares = float(shares)

        df = fetch_stock_data(ticker, start_date, end_date)
        if df.empty:
            continue

        start_value = df.iloc[0]['Close'] * shares
        end_value = df.iloc[-1]['Close'] * shares
        percent_change = ((end_value - start_value) / start_value) * 100
        value_change = end_value - start_value
        total_value_change += value_change

        data.append([ticker, shares, start_value, end_value, percent_change, value_change])

    return data, total_value_change

def colorize_value(value):
    if value >= 0:
        return colored(f'{value:.2f}', 'green')
    else:
        return colored(f'{value:.2f}', 'red')

def print_results(data, start_date, end_date, total_value_change):
    df = pd.DataFrame(data, columns=['Ticker', 'Shares', f'Start Value ({start_date})', f'End Value ({end_date})', 'Percent Change (%)', 'Value Change (USD)'])

    df['Percent Change (%)'] = df['Percent Change (%)'].apply(colorize_value)
    df['Value Change (USD)'] = df['Value Change (USD)'].apply(colorize_value)

    table = tabulate(df, headers='keys', tablefmt='fancy_grid', showindex=False)
    print(table)

    total_row = ['Total', '', '', '', '', colorize_value(total_value_change)]
    total_table = tabulate([total_row], headers=['Ticker', 'Shares', f'Start Value ({start_date})', f'End Value ({end_date})', 'Percent Change (%)', 'Value Change (USD)'], tablefmt='fancy_grid', showindex=False)
    print(total_table)

def main():
    args = parse_args()
    start_date = args.frm.replace('.', '-')
    end_date = args.to

    # Convert dates from YYYY.MM.DD to YYYY-MM-DD format
    if end_date:
        end_date = end_date.replace('.', '-')
    else:
        end_date = datetime.now().strftime('%Y-%m-%d')

    portfolio = args.portfolio
    data, total_value_change = calculate_values(portfolio, start_date, end_date)
    print_results(data, start_date, end_date, total_value_change)

if __name__ == "__main__":
    main()