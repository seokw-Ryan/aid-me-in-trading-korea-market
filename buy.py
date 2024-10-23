import numpy as np
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import sys
import time
import threading

# Get KOSPI tickers
kospi_tickers = stock.get_market_ticker_list(market="KOSPI")

# Get KOSDAQ tickers
kosdaq_tickers = stock.get_market_ticker_list(market="KOSDAQ")

def combine_tickers():
    print("Combining KOSPI and KOSDAQ tickers...")
    combined_tickers = kospi_tickers + kosdaq_tickers
    print("Exporting combined tickers to CSV...")
    df = pd.DataFrame(combined_tickers, columns=['Ticker'])
    df.to_csv('combined_tickers.csv', index=False)
    print("Combined tickers have been exported to 'combined_tickers.csv'")

def loading_animation(stop):
    chars = "/—\\|"
    while not stop():
        for char in chars:
            sys.stdout.write('\r' + f'Processing... {char}')
            sys.stdout.flush()
            time.sleep(0.1)

def calculate_rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def find_stocks_to_buy():
    print("Analyzing stocks to buy...")

    # Read the combined tickers CSV
    tickers_df = pd.read_csv('combined_tickers.csv')

    # Prepare dates for analysis
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=100)).strftime("%Y%m%d")

    stocks_to_buy = []

    # Create a flag for stopping the animation
    stop_animation = threading.Event()

    # Start the loading animation in a separate thread
    loading_thread = threading.Thread(target=loading_animation, args=(stop_animation.is_set,))
    loading_thread.daemon = True
    loading_thread.start()

    total_stocks = len(tickers_df)
    for index, ticker in enumerate(tickers_df['Ticker'], 1):
        try:
            # Update progress
            progress = f"\rProcessing... {index}/{total_stocks} stocks"
            sys.stdout.write(progress)
            sys.stdout.flush()

            # Get stock data
            df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)

            if len(df) < 20:
                continue

            # Calculate 20-day moving average
            df['MA20'] = df['종가'].rolling(window=20).mean()

            # Drop rows with NaN values in 'MA20'
            df = df.dropna(subset=['MA20'])

            # Check if the stock meets the criteria
            for i in range(1, len(df)):
                if (df['종가'].iloc[i] > df['종가'].iloc[i - 1] and
                        df['종가'].iloc[i] > df['MA20'].iloc[i] and
                        df['종가'].iloc[i - 1] <= df['MA20'].iloc[i - 1]):

                    stocks_to_buy.append({
                        'Ticker': ticker,
                        'Date': df.index[i].strftime("%Y-%m-%d"),
                        'Price': df['종가'].iloc[i],
                        'MA20': df['MA20'].iloc[i]
                    })
                    break  # Move to the next stock after finding a match

        except Exception as e:
            print(f"\nError processing {ticker}: {e}")

    # Stop the loading animation
    stop_animation.set()
    loading_thread.join()

    # Clear the loading animation line
    sys.stdout.write('\r' + ' ' * 50 + '\r')
    sys.stdout.flush()

    # Create DataFrame with stocks to buy
    result_df = pd.DataFrame(stocks_to_buy)

    if not result_df.empty:
        print("\nStocks meeting the criteria:")
        print(result_df)
        result_df.to_csv('stocks_to_buy.csv', index=False)
        print("Results exported to 'stocks_to_buy.csv'")
    else:
        print("\nNo stocks found meeting the criteria.")

def get_stock_names(tickers):
    return {ticker: stock.get_market_ticker_name(ticker) for ticker in tickers}

def find_low_rsi_stocks():
    print("Finding stocks with RSI below 25 and market cap above 500 billion KRW...")

    # Read the combined tickers CSV
    tickers_df = pd.read_csv('combined_tickers.csv')

    # Prepare dates for analysis
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=100)).strftime("%Y%m%d")

    # Get today's market cap data
    today = datetime.now().strftime("%Y%m%d")
    market_cap_df = stock.get_market_cap(today)

    low_rsi_stocks = []

    # Create a flag for stopping the animation
    stop_animation = threading.Event()

    # Start the loading animation in a separate thread
    loading_thread = threading.Thread(target=loading_animation, args=(stop_animation.is_set,))
    loading_thread.daemon = True
    loading_thread.start()

    total_stocks = len(tickers_df)
    for index, ticker in enumerate(tickers_df['Ticker'], 1):
        try:
            # Update progress
            progress = f"\rProcessing... {index}/{total_stocks} stocks"
            sys.stdout.write(progress)
            sys.stdout.flush()

            # Check market cap
            if ticker not in market_cap_df.index or market_cap_df.loc[ticker, '시가총액'] < 500_000_000_000:
                continue

            df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)

            if len(df) < 20:
                continue

            df['RSI'] = calculate_rsi(df['종가'])

            # Ensure there are no NaN values in RSI
            if df['RSI'].isnull().all():
                continue

            latest_rsi = df['RSI'].iloc[-1]

            if np.isnan(latest_rsi):
                continue

            if latest_rsi < 30:
                low_rsi_stocks.append({
                    'Ticker': ticker,
                    'RSI': round(latest_rsi, 2),
                    'Price': df['종가'].iloc[-1],
                    'MarketCap': market_cap_df.loc[ticker, '시가총액']
                })

        except Exception as e:
            print(f"\nError processing {ticker}: {e}")

    # Stop the loading animation
    stop_animation.set()
    loading_thread.join()

    # Clear the loading animation line
    sys.stdout.write('\r' + ' ' * 50 + '\r')
    sys.stdout.flush()

    if low_rsi_stocks:
        result_df = pd.DataFrame(low_rsi_stocks)

        # Get stock names for the low RSI stocks
        low_rsi_tickers = result_df['Ticker'].tolist()
        stock_names = get_stock_names(low_rsi_tickers)

        # Add stock names to the DataFrame
        result_df['Name'] = result_df['Ticker'].map(stock_names)

        # Reorder columns
        result_df = result_df[['Ticker', 'Name', 'RSI', 'Price', 'MarketCap']]

        # Sort by market cap (descending)
        result_df = result_df.sort_values('MarketCap', ascending=False)

        # Format MarketCap as billions of KRW
        result_df['MarketCap'] = (result_df['MarketCap'] / 1_000_000_000).round(2)
        result_df = result_df.rename(columns={'MarketCap': 'MarketCap (Billion KRW)'})

        print("\nStocks with RSI below 25 and market cap above 500 billion KRW:")
        print(result_df)
        result_df.to_csv('low_rsi_high_cap_stocks.csv', index=False)
        print("Results exported to 'low_rsi_high_cap_stocks.csv'")
    else:
        print("\nNo stocks found with RSI below 25 and market cap above 500 billion KRW.")

def main():
    combine_tickers()
    while True:
        print("\nWhat would you like to do?")
        print("1. Find stocks to buy based on moving average")
        print("2. Find stocks with RSI below 25 and market cap above 500 billion KRW")
        print("3. Exit")

        choice = input("Enter your choice (1-3): ")

        if choice == '1':
            find_stocks_to_buy()
        elif choice == '2':
            find_low_rsi_stocks()
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
