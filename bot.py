import os
import json
import requests
import gspread
import threading
from flask import Flask
from google.oauth2.service_account import Credentials

# --- Flask health check برای Render ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)


# --- تنظیمات محیط ---
TOKEN = os.environ.get('BALE_TOKEN')
CREDS_JSON = os.environ.get('GOOGLE_CREDS_JSON')
SHEET_ID = "1kuBmsqgBGHzctHJxoUFt9d3-Hb6m-ZQ6CDZMtJMKPzg"

# --- اتصال به Google Sheets ---
def connect_to_sheets():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_dict = json.loads(CREDS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    return sheet

# --- ارسال پیام به بله ---
def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.bale.ai/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    requests.post(url, json=payload)

# --- حلقه اصلی بات ---
def main():
    print("✅ بات بله اجرا شد و منتظر پیام‌های جدید است...")
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

                    # اگر کاربر استارت زد
                    text = message.get("text")
                    if text == "/start":
                        # نمایش دکمه دریافت شماره
                        reply_markup = {
                            "keyboard": [
                                [{"text": "📱 ارسال شماره من", "request_contact": True}]
                            ],
                            "resize_keyboard": True,
                            "one_time_keyboard": True
                        }
                        send_message(chat_id, "سلام! برای ادامه لطفاً شماره موبایل خود را ارسال کنید 👇", reply_markup)
                        continue

                    # اگر کاربر شماره‌اش را فرستاد
                    contact = message.get("contact")
                    if contact:
                        phone = contact.get("phone_number")
                        username = message.get("from", {}).get("username", "بدون آیدی")
                        name = contact.get("first_name")

                        # ذخیره‌سازی در گوگل شیت
                        sheet.append_row([chat_id, username, name, phone])

                        # ارسال لینک دوره به کاربر، بدون اعلام شماره
                        channel_link = "https://bale.ai/join/YOUR_CHANNEL_ID"  # لینک کانال دوره‌ات را اینجا بگذار
                        send_message(chat_id, f"🎯 ممنون {name}! این لینک دوره مخصوص شماست 👇\n ble.ir/join/9Ufz6EYmCs")
                        continue

        except Exception as e:
            print(f"❗ خطا در اجرا: {e}")

if __name__ == "__main__":
    # اجرای Flask در ترد جدا برای Render
    threading.Thread(target=run_flask, daemon=True).start()
    main()
