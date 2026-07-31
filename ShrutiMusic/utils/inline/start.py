import requests
from config import BOT_TOKEN

def send_custom_colored_menu(chat_id, text, reply_photo_url=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # Agar photo ke sath bhejna ho toh endpoint 'sendPhoto' ho jayega
    if reply_photo_url:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        payload = {
            "chat_id": chat_id,
            "photo": reply_photo_url,
            "caption": text,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        # Blue Button (Primary Style)
                        {"text": "Profile", "callback_data": "profile", "style": "primary"},
                        # Red Button (Danger Style)
                        {"text": "Buy VIP", "callback_data": "vip", "style": "danger"}
                    ],
                    [
                        # Green Button (Success Style)
                        {"text": "Refer & Earn", "callback_data": "earn", "style": "success"}
                    ]
                ]
            }
        }
    else:
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "Profile", "callback_data": "profile", "style": "primary"},
                        {"text": "Buy VIP", "callback_data": "vip", "style": "danger"}
                    ],
                    [
                        {"text": "Refer & Earn", "callback_data": "earn", "style": "success"}
                    ]
                ]
            }
        }
    
    requests.post(url, json=payload)
