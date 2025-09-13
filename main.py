# main.py
# Telegram -> Facebook forwarder (photos + text)
# Uses StringSession so it can run non-interactively (suitable for Render)
#
# IMPORTANT: Keep this file private (it contains your session & page token).

import os
import time
import threading
import requests
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ==== TELEGRAM CONFIG ====
api_id = 20897579
api_hash = "73dfd54a9aada23f038a3df5bee759b6"

# <<< Your StringSession (keep secret) >>>
string_session = "1BJWap1wBu2WhV2HnlvqNraL2LY5Zn6wMo9sajMhsdLE8h26qxLveSA4SvjnorxKrNXDKvJLOqWBaCtfHUrqJiVzpZpTSweisQWXe7wpOcI5nsuMkLIEp3_uxlqQ3GIhthwl_PqLbjMnGm1px2wa8qWWXQAcMfkjPQumnVP6TwhIRc2d79bYsLv5uD4o0Mzg7hgJR6ZIgsjZZqBIz5cavAxzIQf7YQiurJxvXyHEWdCbn2FrjqEACYJYiUbRv5c1U_Yeg5_6fyg5vUxul_PQfcNk9I6rSXb7RSLCheKG4owsWq_X7CU3gN-DNJHIT615J9k2rKyxtrZFLbBxvx9ywZEhjU_KgiB8="

# ==== FACEBOOK CONFIG ====
page_id = "825222120665959"
page_access_token = "EAASGKwtJZAogBPVTXcyUZAmZAKNS7XPO2uBZAw8d2NrVpiBBVzrdMTYuchOhjPjRGdklwBtv6jyT8F1Vw9ZCegHZADujQdWlhPUvFd9BCZCZAmAZBRubLfFkUHDaHZA138pwtlU59JU6PQW7EU4Ghwn4cEJBTnhH3hx8sUGm7F46KKpFG1bdrscuw8QPK0xUPzZAxRq3ZBv8"

# ==== TARGET TELEGRAM CHAT IDS ====
target_chat_ids = [
    -1002246802603,   # •NIA•💎PRIVATE CLUB💎•channel•
    -1001478882874,   # All Nigeria Latest News
    -1002196614972    # 💸Trade with Nia💸
]

# ==== TELEGRAM CLIENT (StringSession) ====
client = TelegramClient(StringSession(string_session), api_id, api_hash)

# ==== Helper: POST with retry (works for text or media upload) ====
def post_with_retry(url, data=None, files=None, max_retries=3, timeout=30):
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, data=data, files=files, timeout=timeout)
            if resp.status_code == 200:
                print(f"✅ Success on attempt {attempt}")
                return resp
            else:
                print(f"⚠️ Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"❌ Exception on attempt {attempt}: {e}")
        # exponential backoff
        sleep_time = 2 ** attempt
        print(f"⏳ Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)
    print("🚨 All retries failed.")
    return None

# ==== Telegram Event Handler ====
@client.on(events.NewMessage(chats=target_chat_ids))
async def handler(event):
    # Get message text (caption or plain text). Keep exactly as-is.
    msg = event.message
    # Prefer msg.message (caption/text). If None, fallback to raw_text if available.
    message_text = getattr(msg, "message", "") or getattr(event, "raw_text", "") or ""
    print(f"📩 New message received (chat_id={event.chat_id}): {message_text}")

    # Photos only (forward photos with caption)
    try:
        if getattr(msg, "photo", None):
            print("🖼 Photo detected — downloading...")
            file_path = await msg.download_media()  # returns local file path
            print(f"📂 Downloaded photo to: {file_path}")

            url = f"https://graph.facebook.com/{page_id}/photos"
            # Open file and send with caption
            with open(file_path, "rb") as f:
                files = {"source": f}
                data = {"caption": message_text, "access_token": page_access_token}
                response = post_with_retry(url, data=data, files=files)
            # cleanup local file
            try:
                os.remove(file_path)
            except Exception as e:
                print("⚠️ Couldn't remove file:", e)

            if response:
                print("📤 Photo forwarded to Facebook.")
            else:
                print("❌ Photo forwarding failed after retries.")
            return

        # Text-only messages (forward exactly)
        if message_text and message_text.strip():
            url = f"https://graph.facebook.com/{page_id}/feed"
            data = {"message": message_text, "access_token": page_access_token}
            response = post_with_retry(url, data=data)
            if response:
                print("📤 Text forwarded to Facebook.")
            else:
                print("❌ Text forwarding failed after retries.")
    except Exception as e:
        print("Handler exception:", e)

# ==== Function to run the forwarder (non-interactive) ====
def run_forwarder():
    print("🚀 Forwarder starting (using StringSession)...")
    # start the client (no interactive login)
    client.start()
    client.run_until_disconnected()

# ==== Minimal Flask app to keep Render web service alive ====
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram->Facebook forwarder is running."

if __name__ == "__main__":
    # Run the forwarder in a background thread so Flask can also run
    t = threading.Thread(target=run_forwarder, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", "10000"))
    print(f"🌐 Starting Flask on port {port}")
    # Start Flask (keeps the process alive on Render)
    app.run(host="0.0.0.0", port=port)            if response.status_code == 200:
                print("✅ Posted to Facebook successfully")
                return True
            else:
                print(f"⚠️ Failed to post (status {response.status_code}): {response.text}")
        except Exception as e:
            print(f"❌ Error posting: {e}")

        print(f"🔄 Retry {attempt + 1}/{retries}...")
        time.sleep(5)

    return False

# ==== TELEGRAM EVENT HANDLER ====
@client.on(events.NewMessage(chats=target_chat_ids))
async def handler(event):
    message_text = event.message.message
    print(f"📩 New Telegram message: {message_text}")
    post_to_facebook(message_text)

# ==== START BOT ====
print("🚀 Forwarder is running... Waiting for Telegram messages.")
client.start()
client.run_until_disconnected()

# === Flask dummy app (to keep Render alive) ===
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Bot is running!"

if __name__ == "__main__":
    # Run the forwarder in a background thread
    threading.Thread(target=run_forwarder, daemon=True).start()
    # Start Flask server
    app.run(host="0.0.0.0", port=10000)
