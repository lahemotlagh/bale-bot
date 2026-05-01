import os
import json
import threading
import time
import requests
from flask import Flask
import gspread
from google.oauth2.service_account import Credentials

# -------- ۱. لاگ شروع برنامه --------
print("--- [STARTING BOT] ---")

# -------- ۲. بررسی متغیرهای محیطی --------
TOKEN = os.environ.get("BALE_TOKEN")
GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_CREDS_JSON")
# آیدی شیت رو حتماً چک کن که درست گذاشته باشی
SHEET_ID = "1uVbL_Vsc99U-8-N6n9jW9_8pWkI5_DEx-60O5oXF7kU" # <-- اینجا آیدی شیت خودت رو بذار

if not TOKEN:
    print("❌ خطا: BALE_TOKEN پیدا نشد!")
if not GOOGLE_CREDS_JSON:
    print("❌ خطا: GOOGLE_CREDS_JSON پیدا نشد!")

# -------- ۳. تلاش برای اتصال به گوگل شیت --------
sheet = None
try:
    print("🔄 در حال اتصال به Google Sheets...")
    creds_dict = json.loads(GOOGLE_CREDS_JSON)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(SHEET_ID).sheet1
    print("✅ اتصال به Google Sheets موفقیت‌آمیز بود.")
except Exception as e:
    print(f"❌ خطای بحرانی در اتصال به گوگل‌شیت: {e}")

# -------- ۴. تنظیمات Flask برای Render --------
app = Flask(__name__)
@app.route("/")
def health(): return "Bot is Alive!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 در حال اجرای Flask روی پورت {port}...")
    app.run(host="0.0.0.0", port=port)

# -------- ۵. توابع اصلی بات --------
API_URL = f"https://api.bale.ai/bot{TOKEN}"

def send_message(chat_id, text, reply_markup=None):
    try:
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup: payload["reply_markup"] = json.dumps(reply_markup)
        requests.post(f"{API_URL}/sendMessage", data=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def main_loop():
    print("🚀 شروع لوپ اصلی بات بله...")
    # پاک کردن وبهوک برای اطمینان از کارکرد پولینگ
    try:
        requests.get(f"{API_URL}/deleteWebhook", timeout=10)
    except: pass

    last_update_id = 0
    keyboard = {
        "keyboard": [[{"text": "ارسال شماره موبایل 📱", "request_contact": True}]],
        "resize_keyboard": True, "one_time_keyboard": True
    }

    while True:
        try:
            url = f"{API_URL}/getUpdates?offset={last_update_id + 1}&timeout=30"
            response = requests.get(url, timeout=35).json()
            
            if response.get("ok"):
                for update in response.get("result", []):
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    chat_id = msg.get("chat", {}).get("id")
                    
                    if "text" in msg and msg["text"] == "/start":
                        send_message(chat_id, "سلام! لطفاً شماره موبایل‌ت رو بفرست:", keyboard)
                    
                    elif "contact" in msg:
                        phone = msg["contact"].get("phone_number")
                        user = msg.get("from", {}).get("username", "Unknown")
                        # ذخیره در شیت
                        if sheet:
                            sheet.append_row([str(chat_id), user, phone])
                        send_message(chat_id, "ممنون! این هم لینک کانال دوره: \n https://ble.ir/YOUR_CHANNEL")
            
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ اخطار در لوپ: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # اجرای وب‌سرور در ترد جدا
    threading.Thread(target=run_flask, daemon=True).start()
    # اجرای بات
    main_loop()
