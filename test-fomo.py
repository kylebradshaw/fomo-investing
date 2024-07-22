import random
import string
from datetime import datetime, timedelta
import traceback

def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def random_string(length=5):
    return ''.join(random.choices(string.ascii_letters, k=length))

def fuzz_test_parse_portfolio():
    print("Testing parse_portfolio...")
    try:
        for _ in range(10):
            random_ticker = random_string()
            random_shares = round(random.uniform(0, 1000), 3)
            portfolio_str = f"{random_ticker}({random_shares})"
            result = parse_portfolio(portfolio_str)
            assert len(result) == 1 and result[0][0] == random_ticker and result[0][1] == random_shares, f"Failed on input: {portfolio_str}"
        print("parse_portfolio passed")
    except Exception as e:
        print(f"parse_portfolio failed: {e}")
        traceback.print_exc()

def fuzz_test_fetch_stock_data():
    print("Testing fetch_stock_data...")
    try:
        random_ticker = random_string()
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        result = fetch_stock_data(random_ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        assert isinstance(result, pd.DataFrame), f"Expected DataFrame, got {type(result)}"
        print("fetch_stock_data passed")
    except Exception as e:
        print(f"fetch_stock_data failed: {e}")
        traceback.print_exc()

def fuzz_test_calculate_values():
    print("Testing calculate_values...")
    try:
        for _ in range(10):
            random_ticker = random_string()
            random_shares = round(random.uniform(0, 1000), 3)
            portfolio = [(random_ticker, random_shares)]
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
            result = calculate_values(portfolio, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            assert isinstance(result, tuple) and len(result) == 5, f"Failed on input: {portfolio}"
        print("calculate_values passed")
    except Exception as e:
        print(f"calculate_values failed: {e}")
        traceback.print_exc()

def fuzz_test_compare_portfolios():
    print("Testing compare_portfolios...")
    try:
        portfolio_names = [random_string() for _ in range(5)]
        compare_portfolios(portfolio_names)
        print("compare_portfolios passed")
    except Exception as e:
        print(f"compare_portfolios failed: {e}")
        traceback.print_exc()

def main():
    fuzz_test_parse_portfolio()
    fuzz_test_fetch_stock_data()
    fuzz_test_calculate_values()
    fuzz_test_compare_portfolios()

if __name__ == "__main__":
    main()