import urllib.request
import json
import datetime
import time
import os
import smtplib
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load env variables
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "ttasfique323162@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "afrl mhaj pxcw ucot")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "pkm.tasfique.tanveer@g.bracu.ac.bd")
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "30"))

TARGET_MOVIE_KEYWORDS = ["spider-man", "spiderman", "spider man", "spider"]
TARGET_DAYS = ["sunday"]
API_BASE_URL = "https://cineplex-ticket-api.cineplexbd.com/api/v1"
CINEPLEX_URL = "https://ticket.cineplexbd.com/home"

LOCATIONS = {
    1: "Bashundhara Shopping Mall, Panthapath",
    2: "Shimanto Shambhar, Dhanmondi 2",
    3: "Star Cineplex, SKS Tower, Mohakhali",
    4: "Sony Square, Mirpur",
    5: "Bangladesh Military Museum, Bijoy Shoroni",
    6: "Bali Arcade, Chattogram",
    8: "Centrepoint, Uttara",
    9: "Shimanto Tower, Narayanganj",
    10: "Finlay Square, Chattogram"
}

DEVICE_KEY = "d40fc4be2c27da8fe8d71e820bb4e39606b457f106197aaf465e870fae9fa9b0"
GUEST_TOKEN = "1293001|CINE-TICKET-VBUQQtwUcxmppqpaEwCFl4ZnEMOyL7RuS5QP62Yqd2533103"

def send_email_alert(matches):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🚨 URGENT: Spider-Man Sunday Tickets Released on Cineplex BD! 🎟️"
    msg["From"] = f"Cineplex Ticket Monitor <{SENDER_EMAIL}>"
    msg["To"] = RECIPIENT_EMAIL

    text_content = "CINEPLEX TICKET ALERT!\n\nSpider-Man tickets for SUNDAY have just been released on Star Cineplex!\n\n"
    for m in matches:
        text_content += f"- Location: {m['location_name']}\n  Date: {m['date']}\n  Movie: {m['movie_title']} ({m['category']})\n\n"
    text_content += f"Book now: {CINEPLEX_URL}\n"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f6f9; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; padding: 24px; border-top: 6px solid #e50914;">
            <h1 style="color: #e50914;">🚨 Spider-Man Sunday Tickets Released!</h1>
            <p>Spider-Man Sunday tickets are now available for booking on Star Cineplex Bangladesh!</p>
            <div style="background: #fff5f5; border: 1px solid #ffcdd2; padding: 16px; border-radius: 8px; margin: 16px 0;">
    """
    for m in matches:
        html_content += f"""
                <div style="border-bottom: 1px dashed #ccc; padding: 8px 0;">
                    <strong>📍 {m['location_name']}</strong><br>
                    🗓️ Date: {m['date']} | 🎬 Movie: {m['movie_title']} ({m['category']})
                </div>
        """
    html_content += f"""
            </div>
            <div style="text-align: center;">
                <a href="{CINEPLEX_URL}" style="background: #e50914; color: #fff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">BOOK TICKETS NOW</a>
            </div>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
        server.quit()
        print(f"[SUCCESS] Email alert sent to {RECIPIENT_EMAIL}", flush=True)
        return True
    except Exception as e:
        print(f"[ERROR] Email error: {e}", flush=True)
        return False

def check_cineplex():
    url = f"{API_BASE_URL}/get-showdate"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin": "https://ticket.cineplexbd.com",
        "Referer": "https://ticket.cineplexbd.com/",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "appsource": "web",
        "device-key": DEVICE_KEY,
        "Authorization": f"Bearer {GUEST_TOKEN}"
    }

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now_str}] [FREE RENDER BOT] Checking Cineplex locations...", flush=True)

    new_matches = []
    for loc_id, loc_name in LOCATIONS.items():
        body = json.dumps({"location": loc_id}).encode('utf-8')
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_data = json.loads(resp.read().decode('utf-8'))
                if res_data.get("status") == "success":
                    dates = res_data.get("data", [])
                    for d in dates:
                        s_date = d.get("showDate", "")
                        dt = datetime.datetime.strptime(s_date, "%Y-%m-%d")
                        if dt.strftime("%A").lower() in TARGET_DAYS:
                            movies = d.get("availableMovies", [])
                            for m in movies:
                                m_title = m.get("movie_title", "")
                                if any(kw in m_title.lower() for kw in TARGET_MOVIE_KEYWORDS):
                                    item = {
                                        "location_id": loc_id,
                                        "location_name": loc_name,
                                        "date": f"{s_date} (Sunday)",
                                        "movie_title": m_title,
                                        "category": m.get("category", "2D/3D")
                                    }
                                    print(f"🎉 [MATCH FOUND] {loc_name} | {s_date} | {m_title}", flush=True)
                                    new_matches.append(item)
        except Exception as e:
            print(f"Err Loc {loc_id}: {e}", flush=True)

    if new_matches:
        send_email_alert(new_matches)
    else:
        print(f"[{now_str}] No Sunday Spider-Man tickets released yet.", flush=True)

def monitor_loop():
    while True:
        try:
            check_cineplex()
        except Exception as main_e:
            print(f"Loop Exception: {main_e}", flush=True)
        time.sleep(CHECK_INTERVAL_SECONDS)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Star Cineplex Ticket Bot is running 24/7!")

if __name__ == "__main__":
    print("Starting Free Render Web Service Ticket Monitor...", flush=True)
    # Start monitor loop in background thread
    t = threading.Thread(target=monitor_loop, daemon=True)
    t.start()

    # Bind HTTP server to PORT for Render Free Web Service
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()
