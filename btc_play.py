import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import os

def fetch_data(tickers, start_date):
    return yf.download(tickers, start=start_date)['Adj Close']

def calculate_portfolio_value(data, shares):
    return data * shares

def plot_performance(old_portfolio, new_portfolio, start_date):
    fig, ax1 = plt.subplots(figsize=(14, 7))

    old_portfolio_value = old_portfolio.sum(axis=1)
    new_portfolio_value = new_portfolio.sum(axis=1)

    old_portfolio_change = (old_portfolio_value / old_portfolio_value.iloc[0] - 1) * 100
    new_portfolio_change = (new_portfolio_value / new_portfolio_value.iloc[0] - 1) * 100

    ax1.plot(old_portfolio.index, old_portfolio_value, label='Old Portfolio Value (USD)', color='blue')
    ax1.plot(new_portfolio.index, new_portfolio_value, label='New Portfolio Value (USD)', color='green')

    ax1.set_xlabel('Date')
    ax1.set_ylabel('Portfolio Value (USD)')
    ax1.legend(loc='upper left')
    ax1.grid(True)

    ax2 = ax1.twinx()
    ax2.plot(old_portfolio.index, old_portfolio_change, label='Old Portfolio Change (%)', color='cyan', linestyle='--')
    ax2.plot(new_portfolio.index, new_portfolio_change, label='New Portfolio Change (%)', color='lime', linestyle='--')

    ax2.set_ylabel('Percentage Change (%)')
    ax2.legend(loc='upper right')

    plt.title('Portfolio Performance Comparison')
    fig.tight_layout()
    plt.show()

def export_to_excel(old_portfolio, new_portfolio):
    # Create a directory 'output' if it doesn't exist
    if not os.path.exists('output'):
        os.makedirs('output')

    # Create a filename with the current date
    today = datetime.now().strftime('%Y.%m.%d')
    filename = f'output/{today}_btc_play_history.xls'

    # Combine data into a single DataFrame
    combined_data = pd.DataFrame({
        'Date': old_portfolio.index,
        'Old Portfolio Value (USD)': old_portfolio.sum(axis=1),
        'New Portfolio Value (USD)': new_portfolio.sum(axis=1),
        'Old Portfolio Change (%)': (old_portfolio.sum(axis=1) / old_portfolio.sum(axis=1).iloc[0] - 1) * 100,
        'New Portfolio Change (%)': (new_portfolio.sum(axis=1) / new_portfolio.sum(axis=1).iloc[0] - 1) * 100
    }).set_index('Date')

    # Export to Excel
    combined_data.to_excel(filename)
    print(f'Data exported to {filename}')

def main():
    # Define the date of the transaction
    start_date = '2024-05-28'

    # Define the tickers and shares for the old and new portfolios
    old_tickers = ['VTSAX', 'VOO']
    new_tickers = ['MSTR', 'FBTC']

    old_shares = [485.113, 40.000]
    new_shares = [25.000, 689.000]

    # Fetch historical data from the start date to the present
    old_data = fetch_data(old_tickers, start_date)
    new_data = fetch_data(new_tickers, start_date)

    # Calculate the portfolio values
    old_portfolio = calculate_portfolio_value(old_data, old_shares)
    new_portfolio = calculate_portfolio_value(new_data, new_shares)

    # Plot the performance
    plot_performance(old_portfolio, new_portfolio, start_date)

    # Export data to Excel
    export_to_excel(old_portfolio, new_portfolio)

    # Calculate the relative performance
    old_value_start = old_portfolio.sum(axis=1).iloc[0]
    new_value_start = new_portfolio.sum(axis=1).iloc[0]

    old_value_current = old_portfolio.sum(axis=1).iloc[-1]
    new_value_current = new_portfolio.sum(axis=1).iloc[-1]

    old_return = (old_value_current - old_value_start) / old_value_start * 100
    new_return = (new_value_current - new_value_start) / new_value_start * 100

    print(f"Old Portfolio Return: {old_return:.2f}%")
    print(f"New Portfolio Return: {new_return:.2f}%")

    if new_return > old_return:
        print(f"Your new portfolio has outperformed the old one by {new_return - old_return:.2f}%.")
    else:
        print(f"Your old portfolio would have performed better by {old_return - new_return:.2f}%.")

if __name__ == "__main__":
    main()