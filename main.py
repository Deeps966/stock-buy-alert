import schedule
import time
import logging

import os
import json

import yfinance as yf
import ta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd

import http.server
import socketserver

# Configure logging
logging.basicConfig(filename='stock_alerts.log', 
                    level=logging.INFO, 
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
key = "gmailAppPassword"
gmailAppPassword = os.getenv(key,"Environment Not found")
json_file_path = "./.credentials.json"

try:
    with open(json_file_path, 'r') as file:
        config = json.load(file)
        gmailAppPassword = config.get(key)
except FileNotFoundError:
    print(f"Configuration file {json_file_path} not found.")
except json.JSONDecodeError:
    print(f"Error decoding JSON from the file {json_file_path}.")

print("Mail Creds: ", gmailAppPassword)


# Function to calculate RSI
def calculate_rsi(data, window=14):
    return ta.momentum.RSIIndicator(data['Close'], window=window).rsi()

# Function to send an email
def send_email(stock):
    sender_email = "deepshah.workspace@gmail.com"
    receiver_email = "deepshah.workspace@gmail.com"
    password = gmailAppPassword

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

# Fetch stock data and check RSI condition
def scan_stocks():
    # #: Retrieve data at daily intervals.
    # DAILY = "1d"

    # #: Retrieve data at weekly intervals.
    # WEEKLY = "1wk"

    # #: Retrieve data at montly intervals.
    # MONTHLY = "1mo"
    
    rsi_data = {}

    for stock in nifty_100_stocks:
        data = yf.download(stock+".NS", period="2y", interval="1wk")

        if len(data) < 15:
            continue

        data['RSI'] = calculate_rsi(data)
        current_rsi = data['RSI'].iloc[-1]
        previous_rsi = data['RSI'].iloc[-2]

        rsi_data[stock] = {
            "current_rsi": current_rsi,
            "previous_rsi": previous_rsi
        }

        print( stock, " || Current RSI: ", current_rsi, " || Previous RSI: " , previous_rsi, "\n")

        if current_rsi <= 40 and current_rsi > previous_rsi:
            alert_message = f"Alert sent for {stock} to buy || Current RSI: {current_rsi} || Previous RSI: {previous_rsi}"
            send_email(stock)
            print(alert_message)
            logging.info(alert_message)
    return rsi_data


# Define the handler to process the incoming HTTP requests
class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Set the response status code to 200 (OK)
        self.send_response(200)

        # Set the headers
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # Send the response message
        self.wfile.write(bytes("<html><body><h1>", rsi_data, "</h1></body></html>", "utf-8"))

# Define the port to listen on (port 80)
PORT = 80

# Create a TCP server that listens on the specified port
with socketserver.TCPServer(("", PORT), MyHttpRequestHandler) as httpd:
    print(f"Serving on port {PORT}")
    
    scan_stocks()

    # Schedule tasks
    # schedule.every(10).seconds.do(scan_stocks)
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
        time.sleep(1800)  # Wait a minute before checking again

    # Keep the server running
    httpd.serve_forever()
