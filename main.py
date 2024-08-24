import threading
import requests
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

import socketserver
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configure logging
logging.basicConfig(filename='stock_alerts.log', 
                    level=logging.INFO, 
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
key = "gmailAppPassword"
gmailAppPassword = os.getenv(key,"Environment Not found")
scheduleSeconds = os.getenv("scheduleSeconds", 60)
environment = os.getenv("environment", 'development')
rsi = os.getenv("rsi", 40)

json_file_path = "./.credentials.json"

print(scheduleSeconds)
# Define the port to listen on (port 80)
PORT = 80

alerts = []
gmailAppPassword = ""
try:
    with open(json_file_path, 'r') as file:
        config = json.load(file)
        gmailAppPassword = config.get(key)
except FileNotFoundError:
    print(f"Configuration file {json_file_path} not found.")
except json.JSONDecodeError:
    print(f"Error decoding JSON from the file {json_file_path}.")

print("Mail Creds: ", gmailAppPassword)

# Function to add alert
def add_alert(stock, current_rsi, previous_rsi):
    alert_message = f"Alert sent for {stock} to buy || Current RSI: {current_rsi} || Previous RSI: {previous_rsi}"
    alerts.append(alert_message)



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

rsi_data = {}

# File paths
alert_log_file = 'stock_alerts.log'

# Function to read alerts from file
def read_alerts_from_file():
    try:
        with open(alert_log_file, 'r') as file:
            oldAlerts = file.readlines()
    except FileNotFoundError:
        oldAlerts = []
    return oldAlerts

# Fetch stock data and check RSI condition
def scan_stocks():
    # #: Retrieve data at daily intervals.
    # DAILY = "1d"

    # #: Retrieve data at weekly intervals.
    # WEEKLY = "1wk"

    # #: Retrieve data at montly intervals.
    # MONTHLY = "1mo"
    
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

        if current_rsi <= rsi and current_rsi > previous_rsi:
            alert_message = f"Alert sent for {stock} to buy || Current RSI: {current_rsi} || Previous RSI: {previous_rsi}"
            print(alert_message)
            logging.info(alert_message)
            add_alert(stock, current_rsi, previous_rsi)
            send_email(stock)
    return rsi_data

# Define the HTTP request handler
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/alerts':
            # Read alert messages from file
            oldAlerts = read_alerts_from_file()
            
            # Convert alerts to HTML table
            alert_rows = [f"<tr><td>{alert.strip()}</td></tr>" for alert in oldAlerts]
            alert_html = """
                <html>
                <head>
                    <title>RSI Alerts</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                        }}
                        h1 {{
                            color: #333;
                        }}
                        h2 a {{
                            color: #0066cc;
                            text-decoration: none;
                        }}
                        h2 a:hover {{
                            text-decoration: underline;
                        }}
                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin-top: 20px;
                        }}
                        th, td {{
                            padding: 10px;
                            text-align: left;
                            border: 1px solid #ddd;
                        }}
                        th {{
                            background-color: #f2f2f2;
                            cursor: pointer;
                        }}
                        th.sort-asc::after {{
                            content: " \\25B2"; /* Up arrow */
                        }}
                        th.sort-desc::after {{
                            content: " \\25BC"; /* Down arrow */
                        }}
                        tr:nth-child(even) {{
                            background-color: #f9f9f9;
                        }}
                        tr:hover {{
                            background-color: #f1f1f1;
                        }}
                        .alert {{
                            color: #d9534f; /* Red color for alerts */
                        }}
                    </style>
                    <script>
                        function sortTable() {{
                            var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                            table = document.getElementById("rsiTable");
                            switching = true;
                            dir = "asc"; 
                            while (switching) {{
                                switching = false;
                                rows = table.rows;
                                for (i = 1; i < (rows.length - 1); i++) {{
                                    shouldSwitch = false;
                                    x = rows[i].getElementsByTagName("TD")[0];
                                    y = rows[i + 1].getElementsByTagName("TD")[0];
                                    if (dir == "asc") {{
                                        if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {{
                                            shouldSwitch = true;
                                            break;
                                        }}
                                    }} else if (dir == "desc") {{
                                        if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {{
                                            shouldSwitch = true;
                                            break;
                                        }}
                                    }}
                                }}
                                if (shouldSwitch) {{
                                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                                    switching = true;
                                    switchcount++;
                                }} else {{
                                    if (switchcount == 0 && dir == "asc") {{
                                        dir = "desc";
                                        switching = true;
                                    }}
                                }}
                            }}
                            updateSortArrows(dir);
                        }}
                        
                        function updateSortArrows(direction) {{
                            var thElement = document.getElementById("alertHeader");
                            thElement.classList.remove("sort-asc", "sort-desc");
                            if (direction === "asc") {{
                                thElement.classList.add("sort-asc");
                            }} else {{
                                thElement.classList.add("sort-desc");
                            }}
                        }}
                    </script>
                </head>
                <body>
                    <h1>Alerts Triggered by Weekly RSI Below 40 (All Triggered Alerts)</h1>
                    <h2><a href="/">Show Weekly RSI Data</a></h2>
                    <table id="rsiTable">
                        <thead>
                            <tr>
                                <th id="alertHeader" onclick="sortTable()">Alert Message</th>
                            </tr>
                        </thead>
                        <tbody>
                            {}
                        </tbody>
                    </table>
                </body>
                </html>
                """.format(''.join(alert_rows))

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(alert_html.encode('utf-8'))
        else:
            # Convert RSI data dictionary to HTML table with conditional formatting
            table_rows = []
            for stock, data in rsi_data.items():
                # Determine the color for Current RSI
                if data['current_rsi'] < 40:
                    color = '#FF7F7F'
                elif data['current_rsi'] > 60:
                    color = '#D1FFBD'
                else:
                    color = 'white'  # Default color

                row = f"<tr><td>{stock}</td><td style='background-color: {color};'>{data['current_rsi']}</td><td>{data['previous_rsi']}</td></tr>"
                table_rows.append(row)
             
            # Convert alerts list to HTML table
            alert_rows = [f"<tr><td>{alert}</td></tr>" for alert in alerts]
            
            combined_html = """
            <html>
            <head>
                <title>Weekly RSI Data and Alerts</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                    }}
                    h1 {{
                        color: #333;
                    }}
                    h2 a {{
                        color: #0066cc;
                        text-decoration: none;
                    }}
                    h2 a:hover {{
                        text-decoration: underline;
                    }}
                    .container {{
                        display: flex;
                        justify-content: space-between;
                    }}
                    .table-container {{
                        width: 48%;
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 20px;
                    }}
                    th, td {{
                        padding: 10px;
                        text-align: left;
                        border: 1px solid #ddd;
                    }}
                    th {{
                        background-color: #f2f2f2;
                        cursor: pointer;
                    }}
                    th.sort-asc::after {{
                        content: " \\25B2"; /* Up arrow */
                    }}
                    th.sort-desc::after {{
                        content: " \\25BC"; /* Down arrow */
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                    tr:hover {{
                        background-color: #f1f1f1;
                    }}
                    .alert {{
                        color: #d9534f; /* Red color for alerts */
                    }}
                </style>
                <script>
                    function sortTable(n) {{
                        var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                        table = document.getElementById("rsiTable");
                        switching = true;
                        dir = "asc"; 
                        while (switching) {{
                            switching = false;
                            rows = table.rows;
                            for (i = 1; i < (rows.length - 1); i++) {{
                                shouldSwitch = false;
                                x = rows[i].getElementsByTagName("TD")[n];
                                y = rows[i + 1].getElementsByTagName("TD")[n];
                                if (dir == "asc") {{
                                    if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {{
                                        shouldSwitch = true;
                                        break;
                                    }}
                                }} else if (dir == "desc") {{
                                    if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {{
                                        shouldSwitch = true;
                                        break;
                                    }}
                                }}
                            }}
                            if (shouldSwitch) {{
                                rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                                switching = true;
                                switchcount++;
                            }} else {{
                                if (switchcount == 0 && dir == "asc") {{
                                    dir = "desc";
                                    switching = true;
                                }}
                            }}
                        }}
                        updateSortArrows(dir, n);
                    }}
                    
                    function updateSortArrows(direction, column) {{
                        var thElements = document.getElementsByTagName("th");
                        for (var i = 0; i < thElements.length; i++) {{
                            thElements[i].classList.remove("sort-asc", "sort-desc");
                        }}
                        var thElement = thElements[column];
                        if (direction === "asc") {{
                            thElement.classList.add("sort-asc");
                        }} else {{
                            thElement.classList.add("sort-desc");
                        }}
                    }}
                </script>
            </head>
            <body>
                <div class="container">
                    <div class="table-container">
                        <h1>Weekly RSI Data</h1>
                        <h2><a href="/alerts">Show Old Alerts</a></h2>
                        <table id="rsiTable">
                            <thead>
                                <tr>
                                    <th onclick="sortTable(0)">Stock</th>
                                    <th onclick="sortTable(1)">Current Week RSI</th>
                                    <th onclick="sortTable(2)">Previous Week RSI</th>
                                </tr>
                            </thead>
                            <tbody>
                                {}
                            </tbody>
                        </table>
                    </div>
                    <div class="table-container">
                        <h1>Alerts Triggered by Weekly RSI Below 40 (While Running Script)</h1>
                        <table id="alertsTable">
                            <thead>
                                <tr>
                                    <th>Alert Message</th>
                                </tr>
                            </thead>
                            <tbody>
                                {}
                            </tbody>
                        </table>
                    </div>
                </div>
            </body>
            </html>
            """.format(''.join(table_rows), ''.join(alert_rows))





            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(combined_html.encode('utf-8'))

# Function to start the HTTP server
def start_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print("Starting server at port ",PORT,"...")
    httpd.serve_forever()

# Function to handle HTTP requests every second
def make_periodic_http_request():
    while True:
        try:
            response = requests.get("https://stock-buy-alert.adaptable.app/")
            print(f"Received response: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print("------HTTP Request failed----------")
        time.sleep(scheduleSeconds)

# Schedule tasks
# schedule.every(int(2)).seconds.do(make_periodic_http_request)

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

# Function to handle the scheduled tasks
def run_scheduled_tasks():
    while True:
        schedule.run_pending()
        time.sleep(60)  # Wait a minute before checking again

# Main
if __name__ == "__main__":

    # Create and start threads
    server_thread = threading.Thread(target=start_server)
    scheduler_thread = threading.Thread(target=scan_stocks)
    request_thread = threading.Thread(target=make_periodic_http_request)
    
    server_thread.start()
    scheduler_thread.start()
    if environment == "production":
        request_thread.start()

    server_thread.join()
    scheduler_thread.join()
    request_thread.join()
