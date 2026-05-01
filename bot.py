import requests
import time
import json
import os

TOKEN = os.getenv("BALE_TOKEN")
BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}"

def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(f"{BASE_URL}/sendMessage", json=payload)

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"offset": offset} if offset else {}
    response = requests.get(url, params=params)
    return response.json()

print("Bot started...")

last_update_id = None

while True:
    updates = get_updates(last_update_id)

    if "result" in updates and len(updates["result"]) > 0:
        for update in updates["result"]:
            last_update_id = update["update_id"] + 1

            message = update.get("message")
            if not message:
                continue

            chat_id = message["chat"]["id"]

            # کاربر شماره تلفن ارسال کرده
            if "contact" in message:
                phone = message["contact"]["phone_number"]
                
                send_message(chat_id, f"شماره شما ثبت شد: {phone}")
                send_message(chat_id, "لطفاً وارد کانال دوره شوید: ble.ir/join/9Ufz6EYmCs")
                continue

            # پیام عادی کاربر
            if "text" in message:
                text = message["text"]

                # درخواست شماره تلفن + دکمه مخصوص
                reply_markup = {
                    "keyboard": [
                        [
                            {
                                "text": "ارسال شماره موبایل 📱",
                                "request_contact": True
                            }
                        ]
                    ],
                    "one_time_keyboard": True,
                    "resize_keyboard": True
                }

                send_message(chat_id, "سلام دوست عزیز! شماره موبایلت رو برام بفرست 🌟", reply_markup)

    time.sleep(2)
