import os
import json
import threading
import time
import requests
from flask import Flask

# -------- تنظیمات اولیه --------
TOKEN = os.environ.get("BALE_TOKEN")
if not TOKEN:
    raise RuntimeError("BALE_TOKEN is not set in environment variables")

# Google Sheets config
import gspread
from google.oauth2.service_account import Credentials

GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_CREDS_JSON")
if not GOOGLE_CREDS_JSON:
    raise RuntimeError("GOOGLE_CREDS_JSON is not set in environment variables")

creds_dict = json.loads(GOOGLE_CREDS_JSON)
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gc = gspread.authorize(credentials)

# TODO: اینو با آیدی شیت خودت عوض کن
SHEET_ID = "YOUR_SHEET_ID_HERE"
sheet = gc.open_by_key(SHEET_ID).sheet1

COURSE_CHANNEL_LINK = "https://t.me/YOUR_CHANNEL_ID"

# -------- Flask برای Render --------
app = Flask(__name__)

@app.route("/")
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# -------- توابع بات بله --------
API_URL = f"https://api.bale.ai/bot{TOKEN}"

def delete_webhook():
    try:
        url = f"{API_URL}/deleteWebhook"
        r = requests.get(url, timeout=10)
        print("deleteWebhook:", r.status_code, r.text)
    except Exception as e:
        print("Error in delete_webhook:", e)

def get_updates(offset=None, timeout=30):
    params = {"timeout": timeout}
    if offset:
        params["offset"] = offset
    r = requests.get(f"{API_URL}/getUpdates", params=params, timeout=timeout+5)
    print("getUpdates status:", r.status_code)
    if r.status_code != 200:
        print("getUpdates text:", r.text)
        return []
    data = r.json()
    return data.get("result", [])

def send_message(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    r = requests.post(f"{API_URL}/sendMessage", data=payload, timeout=10)
    print("sendMessage status:", r.status_code, "->", r.text[:200])
    return r

def save_contact(chat_id, username, phone):
    try:
        sheet.append_row([str(chat_id), username or "", phone])
        print("Saved to sheet:", chat_id, username, phone)
    except Exception as e:
        print("Error saving to sheet:", e)

def main_loop():
    print("Starting bot main loop ...")
    delete_webhook()  # مهم: وبهوک رو پاک کن که polling کار کنه
    last_update_id = None

    # کیبورد درخواست شماره
    keyboard = {
        "keyboard": [[{
            "text": "ارسال شماره موبایل 📱",
            "request_contact": True
        }]],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }

    while True:
        try:
            print("polling...")
            updates = get_updates(offset=last_update_id+1 if last_update_id else None)
            for update in updates:
                print("update:", json.dumps(update, ensure_ascii=False))
                last_update_id = update["update_id"]

                message = update.get("message") or {}
                chat = message.get("chat") or {}
                chat_id = chat.get("id")
                username = chat.get("username") or message.get("from", {}).get("username")

                text = message.get("text")
                contact = message.get("contact")

                # 1) شروع گفتگو
                if text == "/start":
                    send_message(
                        chat_id,
                        "سلام 👋\nبرای دسترسی به لینک کانال دوره، لطفاً شماره موبایل‌ت رو با دکمه زیر برام بفرست:",
                        reply_markup=keyboard
                    )

                # 2) دریافت شماره تماس
                elif contact and "phone_number" in contact:
                    phone = contact["phone_number"]
                    save_contact(chat_id, username, phone)

                    send_message(
                        chat_id,
                        f"مرسی 🌟\nاین هم لینک کانال دوره:\n{COURSE_CHANNEL_LINK}"
                    )

            time.sleep(2)

        except Exception as e:
            print("❗ Loop error:", e)
            time.sleep(3)

if __name__ == "__main__":
    # Flask را در یک ترد جدا بزن تا Render راضی باشد
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()

    # حلقه بات
    main_loop()
