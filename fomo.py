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
            continue

        start_price = df.iloc[0]['Close']
        end_price = df.iloc[-1]['Close']
        start_value = start_price * shares
        end_value = end_price * shares
        percent_change = ((end_value - start_value) / start_value) * 100
        value_change = end_value - start_value
        total_value_change += value_change
        total_start_value += start_value
        total_end_value += end_value

        data.append([
            f"{ticker} ({shares:.3f})",
            f"${start_value:,.2f}",
            f"${end_value:,.2f}",
            f"{start_price:,.2f}",
            f"{end_price:,.2f}",
            f"{percent_change:.2f}%",
            f"${value_change:,.2f}"
        ])

    formatted_total_value_change = f"${total_value_change:,.2f}"
    formatted_total_start_value = f"${total_start_value:,.2f}"
    formatted_total_end_value = f"${total_end_value:,.2f}"
    formatted_percent_change = f"{(total_value_change / total_start_value) * 100:.2f}%"

    return data, formatted_total_start_value, formatted_total_end_value, formatted_percent_change, formatted_total_value_change

def colorize_value(value):
    numeric_value = float(value.replace("$", "").replace(",", ""))
    if numeric_value >= 0:
        return colored(f'{value}', 'green')
    else:
        return colored(f'{value}', 'red')

def print_results(data, start_date, end_date, total_start_value, total_end_value, total_percent_change, total_value_change):
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

    total_row = ['Total', total_start_value, total_end_value, '', '', total_percent_change, colorize_value(total_value_change)]
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

    # Remove any existing entry with the same name
    history = [entry for entry in history if entry[0] != name]

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
        history = []
        for row in reader:
            if not row[3]:  # If end_date is blank
                row[3] = get_previous_market_close()
            history.append(row)
        return history

def get_previous_market_close():
    # Fetch the previous market close date
    today = datetime.today()
    stock = yf.Ticker("AAPL")  # Using AAPL as a reference ticker
    df = stock.history(period="5d")
    previous_close_date = df.index[-2].strftime('%Y-%m-%d')  # The second last date
    return previous_close_date

def compare_portfolios(portfolios):
    history = load_history()
    portfolio_data = []

    for portfolio_name in portfolios:
        data = next((entry for entry in history if entry[0] == portfolio_name), None)
        if not data:
            print(f"Portfolio {portfolio_name} must exist in the history with matching date ranges.")
            return
        portfolio_data.append(data)

    start_dates = {data[2] for data in portfolio_data}
    end_dates = {data[3] for data in portfolio_data}

        # if len(start_dates) > 1 or len(end_dates) > 1:
        #     print("The date ranges for the portfolios must match to compare.")
        #     return

    start_date = start_dates.pop()
    end_date = end_dates.pop()

    comparison_data = []
    for portfolio_name, portfolio_str, _, _ in portfolio_data:
        portfolio = parse_portfolio(portfolio_str)
        _, total_start_value, total_end_value, percent_change, total_value_change = calculate_values(portfolio, start_date, end_date)
        comparison_data.append([portfolio_name, total_start_value, total_end_value, percent_change, total_value_change])

    total_comparison = pd.DataFrame(comparison_data, columns=['Name', 'Start Value', 'End Value', 'Percent Change (%)', 'Value Change (USD)'])
    total_comparison_table = tabulate(total_comparison, headers='keys', tablefmt='fancy_grid', showindex=False)
    print(total_comparison_table)

def main():
    args = parse_args()

    if args.aggregate:
        history = load_history()
        for entry in history:
            name, portfolio_str, start_date, end_date = entry
            portfolio = parse_portfolio(portfolio_str)
            data, total_start_value, total_end_value, percent_change, total_value_change = calculate_values(portfolio, start_date, end_date)
            print_results(data, start_date, end_date, total_start_value, total_end_value, percent_change, total_value_change)
    elif args.compare:
        portfolios = args.compare.split(',')
        if len(portfolios) > 5:
            print("You can compare up to 5 portfolios at a time.")
            return
        compare_portfolios(portfolios)
    else:
        start_date = args.frm.replace('.', '-')
        end_date = args.to

        # Convert dates from YYYY.MM.DD to YYYY-MM-DD format
        if end_date:
            end_date = end_date.replace('.', '-')
        else:
            end_date = ''

        portfolio = parse_portfolio(args.portfolio)
        data, total_start_value, total_end_value, percent_change, total_value_change = calculate_values(portfolio, start_date, end_date or get_previous_market_close())
        print_results(data, start_date,end_date or get_previous_market_close(), total_start_value, total_end_value, percent_change, total_value_change)
        # Save the current execution to history if –save flag is used
        if args.save:
            if not args.name:
                raise ValueError("Name is required when saving a portfolio.")
            save_to_history(args.name, args.portfolio, start_date, end_date)

if __name__ == "__main__":
    main()