import numpy as np
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
import sys

def analyze_ticker(ticker, start_date, end_date):
    try:
        # Get stock data for the specified date range
        df = stock.get_market_ohlcv(start_date, end_date, ticker)

        # Handle empty or missing data
        if df.empty:
            print(f"No data available for ticker {ticker}. Skipping.")
            return None

        # Calculate 20-day moving average
        df['MA20'] = df['종가'].rolling(window=20).mean()

        # Drop rows with NaN values in 'MA20'
        df = df.dropna(subset=['MA20'])

        # Ensure we have at least two days of data after calculating MA20
        if len(df) < 2:
            return None

        # Get the latest date in the data
        latest_date = df.index[-1]
        previous_date = df.index[-2]

        # Get closing prices for the last two trading days
        latest_close = df['종가'].iloc[-1]
        previous_close = df['종가'].iloc[-2]

        # Get 20-day moving averages for the last two trading days
        latest_ma20 = df['MA20'].iloc[-1]
        previous_ma20 = df['MA20'].iloc[-2]

        # Check if the stock increased in the most recent trading day
        if latest_close <= previous_close:
            return None

        # Check if the stock price surpassed MA20 today but not the previous day
        if latest_close > latest_ma20 and previous_close <= previous_ma20:
            return {
                'Ticker': ticker,
                'Date': latest_date.strftime("%Y-%m-%d"),
                'Price': latest_close,
                'MA20': latest_ma20
            }
        else:
            return None

    except Exception as e:
        print(f"Error processing {ticker}: {e}")
        return None

def get_recent_business_day():
    today = datetime.now()
    # Loop backwards to find the most recent business day
    while True:
        day_str = today.strftime("%Y%m%d")
        try:
            # Check if the day is a valid business day by trying to get the tickers
            tickers = stock.get_market_ticker_list(day_str)
            if tickers:
                return day_str
        except:
            pass
        today -= timedelta(days=1)

def main():
    print("Analyzing stocks to buy...")

    # Get KOSPI and KOSDAQ tickers
    recent_business_day = get_recent_business_day()
    kospi_tickers = stock.get_market_ticker_list(market="KOSPI", date=recent_business_day)
    kosdaq_tickers = stock.get_market_ticker_list(market="KOSDAQ", date=recent_business_day)
    combined_tickers = kospi_tickers + kosdaq_tickers

    # Prepare dates for analysis
    start_date = "20220720"
    end_date = datetime.now().strftime("%Y%m%d")

    # Filter tickers by market cap > 300 billion won
    market_cap_data = stock.get_market_cap(recent_business_day)
    valid_tickers = market_cap_data[market_cap_data['시가총액'] > 300_000_000_000].index.tolist()
    combined_tickers = [ticker for ticker in combined_tickers if ticker in valid_tickers]

    stocks_to_buy = []

    total_stocks = len(combined_tickers)

    for index, ticker in enumerate(combined_tickers, 1):
        # Update progress
        progress = f"\rProcessing... {index}/{total_stocks} stocks"
        sys.stdout.write(progress)
        sys.stdout.flush()

        result = analyze_ticker(ticker, start_date, end_date)
        if result:
            stocks_to_buy.append(result)

    # Clear the progress line
    sys.stdout.write('\r' + ' ' * 50 + '\r')
    sys.stdout.flush()

    # Create DataFrame with stocks to buy
    result_df = pd.DataFrame(stocks_to_buy)

    if not result_df.empty:
        # Get stock names
        tickers = result_df['Ticker'].tolist()
        stock_names = {ticker: stock.get_market_ticker_name(ticker) for ticker in tickers}
        result_df['Name'] = result_df['Ticker'].map(stock_names)

        # Reorder columns
        result_df = result_df[['Ticker', 'Name', 'Date', 'Price', 'MA20']]

        print("\nStocks meeting the criteria:")
        print(result_df)
        result_df.to_csv('stocks_to_buy.csv', index=False)
        print("Results exported to 'stocks_to_buy.csv'")
    else:
        print("\nNo stocks found meeting the criteria.")

if __name__ == "__main__":
    main()
