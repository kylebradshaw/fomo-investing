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
    parser.add_argument('--name', type=str, help="Name of the portfolio")
    parser.add_argument('--portfolio', type=str, help="Portfolio of tickers and shares, e.g., 'VTSAX(485.113),VOO(40.000)'")
    parser.add_argument('--from', dest='frm', type=str, help="Start date in YYYY.MM.DD format")
    parser.add_argument('--to', type=str, help="End date in YYYY.MM.DD format. Defaults to previous market close.")
    parser.add_argument('--aggregate', action='store_true', help="Run aggregate of all historical executions")
    parser.add_argument('--compare', type=str, help="Compare the value change of two named portfolios, e.g., 'Portfolio1,Portfolio2'")
    parser.add_argument('--save', action='store_true', help="Save this command to the historical file")
    args = parser.parse_args()

    if not args.aggregate and not args.compare:
        if not args.portfolio or not args.frm:
            parser.error("--portfolio and --from are required unless --aggregate or --compare is specified.")

    return args

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

        start_price = df.iloc[0]['Close']
        end_price = df.iloc[-1]['Close']
        start_value = start_price * shares
        end_value = end_price * shares
        percent_change = ((end_value - start_value) / start_value) * 100
        value_change = end_value - start_value
        total_value_change += value_change

        data.append([
            f"{ticker} ({shares:.3f})",
            f"${start_value:,.2f}",
            f"${end_value:,.2f}",
            f"${start_price:,.2f}",
            f"${end_price:,.2f}",
            f"{percent_change:.2f}%",
            f"${value_change:,.2f}"
        ])

    formatted_total_value_change = f"${total_value_change:,.2f}"
    return data, formatted_total_value_change

def colorize_value(value):
    numeric_value = float(value.replace("$", "").replace(",", ""))
    if numeric_value >= 0:
        return colored(f'{value}', 'green')
    else:
        return colored(f'{value}', 'red')

def print_results(data, start_date, end_date, total_value_change):
    df = pd.DataFrame(data, columns=[
        'Ticker (Shares)',
        f'Start Value ({start_date})',
        f'End Value ({end_date})',
        f'Start Price/Share ({start_date})',
        f'End Price/Share ({end_date})',
        'Percent Change (%)',
        'Value Change (USD)'
    ])

    df['Percent Change (%)'] = df['Percent Change (%)'].apply(lambda x: colored(x, 'green') if '-' not in x else colored(x, 'red'))
    df['Value Change (USD)'] = df['Value Change (USD)'].apply(colorize_value)

    table = tabulate(df, headers='keys', tablefmt='fancy_grid', showindex=False)
    print(table)

    total_row = ['Total', '', '', '', '', '', colorize_value(total_value_change)]
    total_table = tabulate([total_row], headers=[
        'Ticker (Shares)',
        f'Start Value ({start_date})',
        f'End Value ({end_date})',
        f'Start Price/Share ({start_date})',
        f'End Price/Share ({end_date})',
        'Percent Change (%)',
        'Value Change (USD)'
    ], tablefmt='fancy_grid', showindex=False)
    print(total_table)

def save_to_history(name, portfolio, start_date, end_date):
    history = load_history()

    # Remove any existing entry with the same name and date range
    history = [entry for entry in history if not (entry[0] == name and entry[2] == start_date and entry[3] == end_date)]

    # Add the new entry
    history.append([name, portfolio, start_date, end_date])

    # Save the updated history
    with open(HISTORY_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['name', 'portfolio', 'start_date', 'end_date'])
        writer.writerows(history)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    with open(HISTORY_FILE, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        return list(reader)

def compare_portfolios(portfolio1, portfolio2):
    history = load_history()
    data1 = next(entry for entry in history if entry[0] == portfolio1)
    data2 = next(entry for entry in history if entry[0] == portfolio2)

    if not data1 or not data2:
        print(f"Both portfolios {portfolio1} and {portfolio2} must exist in the history with matching date ranges.")
        return

    portfolio_str1, start_date1, end_date1 = data1[1:]
    portfolio_str2, start_date2, end_date2 = data2[1:]

    if start_date1 != start_date2 or end_date1 != end_date2:
        print("The date ranges for the portfolios must match to compare.")
        return

    portfolio1 = parse_portfolio(portfolio_str1)
    portfolio2 = parse_portfolio(portfolio_str2)

    data1, total_value_change1 = calculate_values(portfolio1, start_date1, end_date1)
    data2, total_value_change2 = calculate_values(portfolio2, start_date2, end_date2)

    print(f"Comparison of {portfolio1} and {portfolio2} from {start_date1} to {end_date1}")
    print(f"{portfolio1} total value change: {total_value_change1}")
    print(f"{portfolio2} total value change: {total_value_change2}")

def main():
    args = parse_args()

    if args.aggregate:
        history = load_history()
        for entry in history:
            portfolio_str, start_date, end_date = entry[1:]
            portfolio = parse_portfolio(portfolio_str)
            data, total_value_change = calculate_values(portfolio, start_date, end_date)
            print_results(data, start_date, end_date, total_value_change)
    elif args.compare:
        portfolio1, portfolio2 = args.compare.split(',')
        compare_portfolios(portfolio1, portfolio2)
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
            if not args.name:
                raise ValueError("Name is required when saving a portfolio.")
            save_to_history(args.name, args.portfolio, start_date, end_date)

if __name__ == "__main__":
    main()