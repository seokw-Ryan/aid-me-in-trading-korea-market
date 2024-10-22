import pandas as pd
from pykrx import stock
from pykrx import bond
from datetime import datetime, timedelta
import numpy as np

def display_menu():
    print("What would you like to do?")
    print("1. Current price of a stock")
    print("2. 5 day average price of a stock")
    print("3. 20 day average price of a stock")
    print("4. 60 day average price of a stock")
    print("5. 120 day average price of a stock")
    
    choice = input("Enter your choice (1-5): ")
    return choice

def get_current_stock_price():
    ticker = input("Enter the stock ticker: ")
    try:
        df = stock.get_market_ohlcv_by_date("20220701", "20241022", ticker)
        if df.empty:
            print(f"No data found for ticker {ticker}")
        else:
            current_price = df.iloc[-1]['종가']  # '종가' means 'closing price' in Korean
            print(f"The current price of {ticker} is {current_price:,} KRW")
        
    except Exception as e:
        print(f"An error occurred: {e}")

def get_average_stock_price(days):
    ticker = input("Enter the stock ticker: ")
    end_date = (datetime.now()).strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days+1)).strftime("%Y%m%d")
    
    try:
        df = stock.get_market_ohlcv_by_date(start_date, end_date, ticker)
        if df.empty:
            print(f"No data found for ticker {ticker}")
        else:
            average_price = df['종가'].mean()
            print(f"The {days}-day average price of {ticker} is {average_price:,.2f} KRW")
    except Exception as e:
        print(f"An error occurred: {e}")

def calculate_rsi(data, periods=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def main():
    while True:
        user_choice = display_menu()
        if user_choice == '1':
            get_current_stock_price()
        elif user_choice == '2':
            get_average_stock_price(5)
        elif user_choice == '3':
            get_average_stock_price(20)
        elif user_choice == '4':
            get_average_stock_price(60)
        elif user_choice == '5':
            get_average_stock_price(120)
        else:
            print(f"Option {user_choice} is not implemented yet.")
        
        if input("Do you want to continue? (y/n): ").lower() != 'y':
            break

if __name__ == "__main__":
    main()
