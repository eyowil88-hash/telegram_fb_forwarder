from telethon import TelegramClient, events
from telethon.sessions import StringSession
import requests
import time

# ==== TELEGRAM CONFIG ====
api_id = 20897579
api_hash = "73dfd54a9aada23f038a3df5bee759b6"
string_session = "1BJWap1wBu2WhV2HnlvqNraL2LY5Zn6wMo9sajMhsdLE8h26qxLveSA4SvjnorxKrNXDKvJLOqWBaCtfHUrqJiVzpZpTSweisQWXe7wpOcI5nsuMkLIEp3_uxlqQ3GIhthwl_PqLbjMnGm1px2wa8qWWXQAcMfkjPQumnVP6TwhIRc2d79bYsLv5uD4o0Mzg7hgJR6ZIgsjZZqBIz5cavAxzIQf7YQiurJxvXyHEWdCbn2FrjqEACYJYiUbRv5c1U_Yeg5_6fyg5vUxul_PQfcNk9I6rSXb7RSLCheKG4owsWq_X7CU3gN-DNJHIT615J9k2rKyxtrZFLbBxvx9ywZEhjU_KgiB8="

# ==== FACEBOOK CONFIG ====
page_id = "825222120665959"
page_access_token = "EAASGKwtJZAogBPVTXcyUZAmZAKNS7XPO2uBZAw8d2NrVpiBBVzrdMTYuchOhjPjRGdklwBtv6jyT8F1Vw9ZCegHZADujQdWlhPUvFd9BCZCZAmAZBRubLfFkUHDaHZA138pwtlU59JU6PQW7EU4Ghwn4cEJBTnhH3hx8sUGm7F46KKpFG1bdrscuw8QPK0xUPzZAxRq3ZBv8"

# ==== TARGET TELEGRAM CHAT IDS ====
target_chat_ids = [
    -1002246802603,   # Chat 1
    -1001478882874,   # Chat 2
    -1002196614972    # Chat 3
]

# ==== CREATE TELEGRAM CLIENT ====
client = TelegramClient(StringSession(string_session), api_id, api_hash)

# ==== FACEBOOK POST FUNCTION (WITH RETRY) ====
def post_to_facebook(message):
    url = f"https://graph.facebook.com/{page_id}/feed"
    payload = {
        "message": message,
        "access_token": page_access_token
    }

    retries = 3
    for attempt in range(retries):
        try:
            response = requests.post(url, data=payload)
            if response.status_code == 200:
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
