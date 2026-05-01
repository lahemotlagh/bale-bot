import os
import requests
import time
from flask import Flask
from threading import Thread

app = Flask(__name__)

# --- تنظیمات ---
TOKEN = os.getenv("BALE_TOKEN")
# حتما چک کن آدرس با tapi شروع بشه
API_URL = f"https://tapi.bale.ai/bot{TOKEN}" 
SHEET_ID = "1kuBmsqgBGHzctHJxoUFt9d3-Hb6m-ZQ6CDZMtJMKPzg"
GOOGLE_CREDS_JSON = os.getenv("GOOGLE_CREDS_JSON")

@app.route('/')
def health_check():
    return "Bot is Running!", 200

def send_message(chat_id, text, reply_markup=None):
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def bot_polling():
    offset = 0
    print("🚀 Polling started...")
    while True:
        try:
            # گرفتن آپدیت‌ها از بله
            response = requests.get(f"{API_URL}/getUpdates", params={"offset": offset, "timeout": 20}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        message = update.get("message")
                        if not message:
                            continue
                        
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "")

                        if text == "/start":
                            kb = {
                                "keyboard": [[{"text": "📱 ارسال شماره موبایل", "request_contact": True}]],
                                "resize_keyboard": True,
                                "one_time_keyboard": True
                            }
                            send_message(chat_id, "سلام! خوش آمدید. برای دریافت لینک دوره رایگان، لطفا دکمه «ارسال شماره موبایل» زیر را بزنید:", kb)
                        
                        elif "contact" in message:
                            phone = message["contact"]["phone_number"]
                            # اینجا کد ذخیره در گوگل شیت رو که قبلا داشتیم صدا بزن
send_message(
    chat_id,
    "✅ باتشکر!\n\n"
    " شماره ثبت شد.\n\n"
    "🎓  دوره آموزشی هوش مصنوعی برای کسب و کار:\n"
    "👉 ble.ir/join/9Ufz6EYmCs"
)

            time.sleep(1)
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # اجرای پولینگ در یک ترد جداگانه که Flask رو بلاک نکنه
    Thread(target=bot_polling, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
