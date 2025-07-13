from flask import Flask, jsonify, request
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from apscheduler.schedulers.background import BackgroundScheduler 
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


app = Flask(__name__)

# --- Configuration ---
JET2_URL = 'https://www.jet2holidays.com/beach/balearics/majorca/cala-dor/alua-suites-las-rocas?holiday=591&duration=7&airport=1&date=14-06-2026&occupancy=r2c_r2c&board=5&iflight=1308104&oflight=1312119&rooms=72791_72791&gtmsearchtype=Beach%20Search%20Results&smartsearchid=962a55c0-d4a4-4f9c-baf5-ef485a17cff3&property=81041'
PRICE_FILE = 'Price.json'

EMAIL_ADDRESS = 'jet2notify@gmail.com'  # Your email
EMAIL_PASSWORD = 'ekza xios svjh orwl'    # Your app password
TO_EMAIL = 'joelcott4329@gmail.com'       # Where to send alerts

# --- Price functions ---


def get_current_price():
    options = Options()
    #options.add_argument("--headless")  # Comment this line out to see the browser
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    try:
        print("Starting price check...")

        # Automatically install the correct ChromeDriver for your system
        ("ChromeDriverManager is installing the driver...")
        service = Service(ChromeDriverManager().install())
        print(f"Driver installed at: {service.path}")
        driver = webdriver.Chrome(service=service, options=options)


        driver.get(JET2_URL)

        # Print part of the page source for debugging
        print(driver.page_source[:1000])

        wait = WebDriverWait(driver, 15)
        price_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.basket-summary__price-value--total'))
        )

        price_text = price_element.text.strip()
        price = int(''.join(filter(str.isdigit, price_text)))

        return price, None

    except Exception as e:
        return None, str(e)

    finally:
        try:
            driver.quit()
        except:
            pass






def load_previous_price():
    if os.path.exists(PRICE_FILE):
        try:
            with open(PRICE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('price')
        except Exception:
            return None
    return None

def save_price(price):
    with open(PRICE_FILE, 'w') as f:
        json.dump({'price': price}, f)

def send_email_alert(new_price, old_price):
    subject = '⚠️ Jet2 Price Drop Alert ⚠️'
    body = (
        f"📉 The holiday price has dropped! 📉\n\n"
        f"Hello Joel,\n"
        f"Your Holiday to Las Rocas Alua Suites in Palma De Mallorca Cala D'or has dropped in price:\n\n"
        f"Previous: £{old_price}\nNow: £{new_price}\n\n{JET2_URL}\n\n"
        f"Please click on the link to secure your new holiday price now!\n\n"
        f"Thanks for using the Jet2 Holidays Notifier✈️\n"
        f"Created by Joel"
    )

    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return "✅ Email alert sent."
    except Exception as e:
        return f"❌ Failed to send email: {e}"

def send_email_status(body):
    subject = "✈️ Jet2 Scheduled Price Check Report ✈️"
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return "✅ Scheduled check email sent."
    except Exception as e:
        return f"❌ Failed to send scheduled check email: {e}"

def check_price_job():
    """Background job that runs every 30 minutes to check price and send email with all info."""
    price, error = get_current_price()
    if error:
        msg = f"❌ Scheduled Job - Error getting price: {error}"
        print(msg)
        send_email_status(msg)
        return

    previous_price = load_previous_price()
    msg_lines = [f"ℹ️ Scheduled Job - Previous price: {previous_price}", f"Scheduled Job - Current price: {price}"]

    #price = 50
    #if previous_price is None:
    #    save_price(price)
    #    msg_lines.append(f"💾 Scheduled Job - First run, saved price: £{price}")
    if price < previous_price:
        msg_lines.append(f"🎉 Scheduled Job - Price dropped! Previous: £{previous_price}, Now: £{price} Secure the holiday here: {JET2_URL}")
        alert_result = send_email_alert(price, previous_price)
        msg_lines.append(f"💷 Scheduled Job - {alert_result}")
        save_price(price)
    #else:
        #msg_lines.append(f"ℹ️ Scheduled Job - No price drop. Current: £{price}, Previous: £{previous_price}")

    final_message = "\n".join(msg_lines)
    print(final_message)
    send_email_status(final_message)

# --- Flask routes ---

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>Jet2 Holiday Price Checker</title>
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

        body {
          margin: 0;
          font-family: 'Montserrat', sans-serif;
          background-color: #fff;
          color: #222;
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 2rem;
          min-height: 100vh;
          box-sizing: border-box;
          text-align: center;
        }

        header {
          width: 100%;
          max-width: 600px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 1rem;
          margin-bottom: 2rem;
          border-bottom: 3px solid #E10600;
          padding-bottom: 1rem;
        }

        header h1 {
          color: #E10600;
          font-weight: 700;
          font-size: 1.8rem;
          margin: 0;
          text-align: center;
          align-items: center;
        }

        button {
          background-color: #E10600;
          color: white;
          border: none;
          padding: 1rem 2rem;
          font-size: 1.3rem;
          font-weight: 700;
          border-radius: 6px;
          cursor: pointer;
          transition: background-color 0.3s ease;
          box-shadow: 0 6px 12px rgba(225, 6, 0, 0.4);
          margin-bottom: 1.5rem;
        }

        button:hover {
          background-color: #b80400;
        }

        #price-result {
          font-size: 1.5rem;
          font-weight: 700;
          color: #333;
          min-height: 2em;
          margin-bottom: 1rem;
          text-align: center;
        }

        #log-output {
          width: 100%;
          max-width: 600px;
          background: #f7f7f7;
          border: 1px solid #ddd;
          padding: 1rem;
          height: 200px;
          overflow-y: auto;
          font-family: monospace;
          font-size: 0.9rem;
          color: #444;
          white-space: pre-wrap;
          box-sizing: border-box;
          border-radius: 6px;
          text-align: left;
        }

        @media (max-width: 600px) {
          body {
            padding: 1rem;
          }
          button {
            width: 100%;
          }
          header {
            flex-direction: column;
            align-items: center;
          }
          header h1 {
            font-size: 1.5rem;
          }
          #log-output {
            height: 150px;
          }
        }
      </style>
    </head>
    <body>
        <header>
            <h1>Jet2 Holiday Price Checker</h1>
        </header>

      <button id="check-price-btn">Check Current Price</button>
      <p id="price-result">Price will show here</p>

      <div id="log-output" aria-live="polite" aria-atomic="true"></div>

      <script>
        const result = document.getElementById('price-result');
        const log = document.getElementById('log-output');

        function logMessage(msg) {
          log.textContent += msg + '\\n';
          log.scrollTop = log.scrollHeight;
        }

        document.getElementById('check-price-btn').onclick = async () => {
          result.textContent = 'Checking price...';
          log.textContent = '';  // clear logs
          logMessage('Starting price check...');

          try {
            const response = await fetch('/api/price');
            const data = await response.json();

            if (data.price) {
              result.textContent = `Current Price: £${data.price}`;
              logMessage(`Price fetched successfully: £${data.price}`);
            } else if(data.error) {
              result.textContent = 'Error fetching price';
              logMessage('Error: ' + data.error);
            } else {
              result.textContent = 'Unexpected response';
              logMessage('Unexpected response from server.');
            }

            if(data.logs && data.logs.length) {
              data.logs.forEach(m => logMessage(m));
            }

          } catch (e) {
            result.textContent = 'Error fetching price';
            logMessage('Fetch error: ' + e.message);
          }
        }
      </script>
    </body>
    </html>
    '''

@app.route('/api/price')
def api_price():
    logs = []
    def log(msg):
        print(msg)
        logs.append(msg)

    try:
        price, error = get_current_price()
        if error:
            log(f"❌ Error getting price: {error}")
            return jsonify({'error': error, 'logs': logs}), 500

        previous_price = load_previous_price()
        log(f"💷 Previous saved price: {previous_price}")

        if previous_price is None:
            save_price(price)
            log(f"💾 First run - saved current price: £{price}")
        elif price < previous_price:
            log(f"🎉 Price dropped! Previous: £{previous_price}, Now: £{price}")
            alert_result = send_email_alert(price, previous_price)
            log(alert_result)
            save_price(price)
        else:
            log(f"ℹ️ No price drop detected. Current price: £{price}, Previous price: £{previous_price}")

        return jsonify({'price': price, 'logs': logs})
    except Exception as e:
        import traceback
        err_trace = traceback.format_exc()
        log(f"❌ Unexpected error: {e}\n{err_trace}")
        return jsonify({'error': str(e), 'logs': logs}), 500

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_price_job, trigger="interval", minutes=1440)
    scheduler.start()
    try:
        app.run(host='0.0.0.0', port=5000, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        scheduler.shutdown()
