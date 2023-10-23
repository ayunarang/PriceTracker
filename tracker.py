from decouple import config

import http.server
import socketserver
import json
import requests
from bs4 import BeautifulSoup as BS
from urllib.parse import urlparse, parse_qs
from smtplib import SMTP

class MyHandler(http.server.SimpleHTTPRequestHandler):
    users_emails = set()  # Store user emails in-memory (for simplicity)

    def do_GET(self):
        if self.path.startswith('/check_price'):
            query_components = parse_qs(urlparse(self.path).query)
            url = query_components['url'][0]
            affordable_price = float(query_components['affordablePrice'][0])
            email = query_components['email'][0]
            current_price = self.get_price(url)

            if current_price <= affordable_price:
                response_data = {"message": f"Price dropped to {current_price}! Email notification sent."}
                self.send_email(url, email)
            else:
                response_data = {"message": f"Current Price: {current_price} (Above your affordable price)"}

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
        else:
            super().do_GET()

    def get_price(self, url):
        page = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"})
        soup = BS(page.content, "html.parser")
        price = float((soup.find(class_="a-price-whole")).text.replace(",", ""))
        return price

    def send_email(self, url, email):
        SERVER_NAME = "smtp.gmail.com"
        PORT = 587
        MYEMAIL = config('EMAIL')
        PASSWORD = config('PASSWORD')

        if email not in self.users_emails:
            s = SMTP(host=SERVER_NAME, port=PORT)
            s.starttls()
            s.login(MYEMAIL, PASSWORD)
            subject = "Amazon Price Drop Notification"
            body = f"Price dropped for the product at {url}. Go buy it now!"
            msg = f"Subject:{subject}\n\n{body}"
            s.sendmail(MYEMAIL, email, msg)
            s.quit()
            self.users_emails.add(email)

PORT = 8000

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
