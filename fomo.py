import argparse
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
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
    parser.add_argument('--compare', type=str, help="Compare the value change of two to five named portfolios, e.g., 'Portfolio1,Portfolio2,...'")
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
    total_start_value = 0
    total_end_value = 0

    for ticker, shares in portfolio:
        df = fetch_stock_data(ticker, start_date, end_date)

        if df.empty:
            print(f"No data for {ticker} between {start_date} and {end_date}. Skipping.")
            continue

        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        start_value = start_price * shares
        end_value = end_price * shares
        value_change = end_value - start_value
        percent_change = (value_change / start_value) * 100

        total_value_change += value_change
        total_start_value += start_value
        total_end_value += end_value

        data.append([
            ticker,
            shares,
            start_price,
            end_price,
            start_value,
            end_value,
            percent_change,
            value_change
        ])

    if total_start_value == 0:
        print("Total start value is zero, cannot calculate overall percent change.")
        overall_percent_change = 0
    else:
        overall_percent_change = (total_value_change / total_start_value) * 100

    return data, total_start_value, total_end_value, overall_percent_change, total_value_change

# def print_results(data, start_date, end_date, total_start_value, total_end_value, percent_change, total_value_change):
#     df = pd.DataFrame(data, columns=[
#         'Ticker', 'Shares', 'Start Price', 'End Price', 'Start Value', 'End Value', 'Percent Change (%)', 'Value Change (USD)'
#     ])
#     table = tabulate(df, headers='keys', tablefmt='fancy_grid', showindex=False)
#     print(colored(f"\nPortfolio performance from {start_date} to {end_date}:", 'cyan'))
#     print(table)
#     print(colored(f"\nTotal start value: ${total_start_value:,.2f}", 'green'))
#     print(colored(f"Total end value: ${total_end_value:,.2f}", 'green'))
#     print(colored(f"Overall percent change: {percent_change:.2f}%", 'yellow'))
#     print(colored(f"Total value change: ${total_value_change:,.2f}", 'yellow'))
def print_results(data, start_date, end_date, total_start_value, total_end_value, percent_change, total_value_change):
    df = pd.DataFrame(data, columns=[
        'Ticker', 'Shares', 'Start Price', 'End Price', 'Start Value', 'End Value', 'Percent Change (%)', 'Value Change (USD)'
    ])

    # Calculate summation and average
    total_end_value_sum = df['End Value'].sum()
    average_percent_change = df['Percent Change (%)'].mean()

    # Create the summation row
    summation_row = pd.DataFrame([{
        'Ticker': 'Summation',
        'Shares': '',
        'Start Price': '',
        'End Price': '',
        'Start Value': '',
        'End Value': total_end_value_sum,
        'Percent Change (%)': average_percent_change,
        'Value Change (USD)': ''
    }])

    # Concatenate the summation row to the original DataFrame
    df = pd.concat([df, summation_row], ignore_index=True)

    # Format all prices and values as USD
    for column in ['Start Price', 'End Price', 'Start Value', 'End Value', 'Value Change (USD)']:
        df[column] = df[column].map(lambda x: f"${x:,.2f}" if x != '' else '')

    table = tabulate(df, headers='keys', tablefmt='fancy_grid', showindex=False)
    print(colored(f"\nPortfolio performance from {start_date} to {end_date}:", 'cyan'))
    print(table)
    print(colored(f"\nTotal start value: ${total_start_value:,.2f}", 'green'))
    print(colored(f"Total end value: ${total_end_value:,.2f}", 'green'))
    print(colored(f"Overall percent change: {percent_change:.2f}%", 'yellow'))
    print(colored(f"Total value change: ${total_value_change:,.2f}", 'yellow'))

def get_previous_market_close():
    now = datetime.now()
    if now.hour < 16:
        now = now - timedelta(days=1)
    previous_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return previous_close.strftime('%Y-%m-%d')

def save_to_history(name, portfolio, start_date, end_date):
    with open(HISTORY_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([name, portfolio, start_date, end_date])

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, 'r') as f:
        reader = csv.reader(f)
        return list(reader)

def compare_portfolios(portfolios):
    history = load_history()
    comparison_data = []

    for portfolio_name in portfolios:
        matching_entries = [entry for entry in history if entry[0] == portfolio_name]
        if not matching_entries:
            print(f"No history found for portfolio '{portfolio_name}'. Skipping.")
            continue

        for entry in matching_entries:
            name, portfolio_str, start_date, end_date = entry
            portfolio = parse_portfolio(portfolio_str)
            data, total_start_value, total_end_value, percent_change, total_value_change = calculate_values(portfolio, start_date, end_date)
            comparison_data.append([
                name,
                start_date,
                end_date,
                total_start_value,
                total_end_value,
                percent_change,
                total_value_change
            ])

    comparison_df = pd.DataFrame(comparison_data, columns=[
        'Name', 'Start Date', 'End Date', 'Start Value', 'End Value', 'Percent Change (%)', 'Value Change (USD)'
    ])
    comparison_table = tabulate(comparison_df, headers='keys', tablefmt='fancy_grid', showindex=False)
    print(comparison_table)

def main():
    args = parse_args()

    if args.aggregate:
        history = load_history()
        for entry in history:
            name, portfolio_str, start_date, end_date = entry
            portfolio = parse_portfolio(portfolio_str)
            data, total_start_value, total_end_value, percent_change, total_value_change = calculate_values(portfolio, start_date, end_date or get_previous_market_close())
            print_results(data, start_date, end_date or get_previous_market_close(), total_start_value, total_end_value, percent_change, total_value_change)
    elif args.compare:
        portfolios = args.compare.split(',')
        if len(portfolios) > 5:
            print("You can compare up to 5 portfolios at a time.")
            return
        compare_portfolios(portfolios)
    else:
        start_date = args.frm.replace('.', '-')
        end_date = args.to

        if end_date:
            end_date = end_date.replace('.', '-')
        else:
            end_date = get_previous_market_close()

        portfolio = parse_portfolio(args.portfolio)
        data, total_start_value, total_end_value, percent_change, total_value_change = calculate_values(portfolio, start_date, end_date)
        print_results(data, start_date, end_date, total_start_value, total_end_value, percent_change, total_value_change)

        if args.save:
            if not args.name:
                raise ValueError("Name is required when saving a portfolio.")
            save_to_history(args.name, args.portfolio, start_date, end_date)

if __name__ == "__main__":
    main()