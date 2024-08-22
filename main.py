import schedule
import time

import yfinance as yf
import ta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd

# Function to calculate RSI
def calculate_rsi(data, window=14):
    return ta.momentum.RSIIndicator(data['Close'], window=window).rsi()

# Function to send an email
def send_email(stock):
    sender_email = "deepshah.workspace@gmail.com"
    receiver_email = "deepshah.workspace@gmail.com"
    password = "gmail-app-password"

    subject = f"Buy Alert: {stock}"
    body = f"Buy alert for {stock}: The weekly RSI(14) <= 40 and is greater than last week's RSI."

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()

# List of Nifty 100 stocks
nifty_100_stocks = [
    "ABB", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ADANIPOWER",
    "ATGL", "AMBUJACEM", "APOLLOHOSP", "ASIANPAINT", "DMART", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BAJAJHLDNG", "BANKBARODA",
    "BERGEPAINT", "BEL", "BPCL", "BHARTIARTL", "BOSCHLTD", "BRITANNIA",
    "CANBK", "CHOLAFIN", "CIPLA", "COALINDIA", "COLPAL", "DLF", "DABUR",
    "DIVISLAB", "DRREDDY", "EICHERMOT", "GAIL", "GODREJCP", "GRASIM", 
    "HCLTECH", "HDFCBANK", "HDFCLIFE", "HAVELLS", "HEROMOTOCO", "HINDALCO",
    "HAL", "HINDUNILVR", "ICICIBANK", "ICICIGI", "ICICIPRULI", "ITC", "IOC",
    "IRCTC", "IRFC", "INDUSINDBK", "NAUKRI", "INFY", "INDIGO", "JSWSTEEL",
    "JINDALSTEL", "JIOFIN", "KOTAKBANK", "LTIM", "LT", "LICI", "M&M", "MARICO",
    "MARUTI", "NTPC", "NESTLEIND", "ONGC", "PIDILITIND", "PFC", "POWERGRID",
    "PNB", "RECLTD", "RELIANCE", "SBICARD", "SBILIFE", "SRF", "MOTHERSON",
    "SHREECEM", "SHRIRAMFIN", "SIEMENS", "SBIN", "SUNPHARMA", "TVSMOTOR",
    "TCS", "TATACONSUM", "TATAMTRDVR", "TATAMOTORS", "TATAPOWER", "TATASTEEL",
    "TECHM", "TITAN", "TORNTPHARM", "TRENT", "ULTRACEMCO", "UNITDSPR", "VBL",
    "VEDL", "WIPRO", "ZOMATO", "ZYDUSLIFE"
]


# #: Retrieve data at daily intervals.
# DAILY = "1d"

# #: Retrieve data at weekly intervals.
# WEEKLY = "1wk"

# #: Retrieve data at montly intervals.
# MONTHLY = "1mo"


# Fetch stock data and check RSI condition
def scan_stocks():
    for stock in nifty_100_stocks:
        data = yf.download(stock+".NS", period="2y", interval="1wk")

        if len(data) < 15:
            continue

        data['RSI'] = calculate_rsi(data)
        current_rsi = data['RSI'].iloc[-1]
        previous_rsi = data['RSI'].iloc[-2]

        print( stock, " || Current RSI: ", current_rsi, " || Previous RSI: " , previous_rsi, "\n")

        if current_rsi <= 40 and current_rsi > previous_rsi:
            send_email(stock)
            print(f"Alert sent for {stock}")


scan_stocks()

# Schedule tasks
schedule.every().monday.at("09:30").do(scan_stocks)
schedule.every().monday.at("15:00").do(scan_stocks)
schedule.every().tuesday.at("09:30").do(scan_stocks)
schedule.every().tuesday.at("15:00").do(scan_stocks)
schedule.every().wednesday.at("09:30").do(scan_stocks)
schedule.every().wednesday.at("15:00").do(scan_stocks)
schedule.every().thursday.at("09:30").do(scan_stocks)
schedule.every().thursday.at("15:00").do(scan_stocks)
schedule.every().friday.at("09:30").do(scan_stocks)
schedule.every().friday.at("15:00").do(scan_stocks)

while True:
    schedule.run_pending()
    time.sleep(60)  # Wait a minute before checking again