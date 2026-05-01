import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials

import os
import threading
import http.server
import socketserver

# --- این بخش برای گول زدن رندر اضافه شده ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Dummy server running on port {port}")
        httpd.serve_forever()

# اجرای سرور در یک رشته جداگانه
threading.Thread(target=run_dummy_server, daemon=True).start()
# ------------------------------------------

# --- تنظیمات اولیه ---
TOKEN = os.environ.get('BALE_TOKEN')
# خواندن JSON از محیط Render
CREDS_JSON = os.environ.get('GOOGLE_CREDS_JSON')
# آیدی شیت خودت رو اینجا بذار (همون که تو URL شیت هست)
SHEET_ID = "1kuBmsqgBGHzctHJxoUFt9d3-Hb6m-ZQ6CDZMtJMKPzg"

# --- متصل شدن به Google Sheets ---
def connect_to_sheets():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_dict = json.loads(CREDS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    # باز کردن شیت اول
    sheet = client.open_by_key(SHEET_ID).sheet1
    return sheet

# --- تابع ارسال پیام به بله ---
def send_message(chat_id, text):
    url = f"https://api.bale.ai/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

# --- حلقه اصلی بات ---
def main():
    print("بات بله با موفقیت اجرا شد...")
    sheet = connect_to_sheets()
    last_update_id = 0

    while True:
        try:
            url = f"https://api.bale.ai/bot{TOKEN}/getUpdates?offset={last_update_id + 1}"
            response = requests.get(url).json()

            if response.get("ok"):
                for update in response.get("result", []):
                    last_update_id = update["update_id"]
                    message = update.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text")
                    username = message.get("from", {}).get("username", "بدون آیدی")

                    if text:
                        # ذخیره در گوگل شیت: [آیدی چت، نام کاربری، متن پیام]
                        sheet.append_row([chat_id, username, text])
                        
                        # تایید به کاربر
                        send_message(chat_id, "اطلاعات شما با موفقیت در گوگل شیت ثبت شد! ✅")
        
        except Exception as e:
            print(f"خطایی رخ داد: {e}")

if __name__ == "__main__":
    main()
