from telethon import TelegramClient, events
from telethon.sessions import StringSession
import requests
import os
import time
import threading
from flask import Flask

# ==== TELEGRAM CONFIG ====
api_id = 20897579
api_hash = "73dfd54a9aada23f038a3df5bee759b6"
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

# ==== Create Telegram client ====
client = TelegramClient(StringSession(string_session), api_id, api_hash)


# ==== Retry helper ====
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
    msg = event.message
    message_text = getattr(msg, "message", "") or getattr(event, "raw_text", "") or ""
    print(f"📩 New Telegram message (chat {event.chat_id}): {message_text}")

    try:
        # Case 1: Photos
        if getattr(msg, "photo", None):
            print("🖼 Photo detected — downloading...")
            file_path = await msg.download_media()
            if not file_path:
                print("⚠️ Failed to download media.")
                return

            print(f"📂 Downloaded to {file_path}")
            url = f"https://graph.facebook.com/{page_id}/photos"
            with open(file_path, "rb") as f:
                files = {"source": f}
                data = {"caption": message_text, "access_token": page_access_token}
                resp = post_with_retry(url, data=data, files=files)

            # cleanup
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"⚠️ Could not delete file: {e}")

            if resp:
                print("📤 Photo forwarded to Facebook.")
            else:
                print("❌ Photo forwarding failed.")
            return

        # Case 2: Text only
        if message_text.strip():
            url = f"https://graph.facebook.com/{page_id}/feed"
            data = {"message": message_text, "access_token": page_access_token}
            resp = post_with_retry(url, data=data)
            if resp:
                print("📤 Text forwarded to Facebook.")
            else:
                print("❌ Text forwarding failed.")
            return

        print("ℹ️ Ignored message (no text, no photo).")

    except Exception as ex:
        print(f"Handler exception: {ex}")


# ==== Run Telegram Forwarder ====
def run_forwarder():
    try:
        print("🚀 Starting Telegram forwarder...")
        client.start()
        client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Forwarder crashed: {e}")


# ==== Flask app to keep Render alive ====
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram → Facebook forwarder is running."


if __name__ == "__main__":
    # Run Telegram in background thread
    threading.Thread(target=run_forwarder, daemon=True).start()

    # Start Flask in main thread (Render expects a web server)
    port = int(os.environ.get("PORT", "10000"))
    print(f"🌐 Starting Flask on port {port}")
    app.run(host="0.0.0.0", port=port)                print(f"⚠️ Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Exception on attempt {attempt}: {e}")

        # Wait before retrying (exponential backoff)
        sleep_time = 2 ** attempt
        print(f"⏳ Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)

    print("🚨 All retries failed.")
    return None

# ==== Telegram message handler ====
@client.on(events.NewMessage(chats=target_chat_ids))
async def handler(event):
    message_text = event.message.message or ""
    print(f"📩 New message: {message_text}")

    # Case 1: Handle photos
    if event.message.photo:
        file_path = await event.message.download_media()
        print(f"📂 Downloaded photo: {file_path}")

        url = f"https://graph.facebook.com/{page_id}/photos"
        files = {"source": open(file_path, "rb")}
        payload = {
            "caption": message_text,
            "access_token": page_access_token,
        }

        response = post_with_retry(url, payload=payload, files=files)
        print(f"📤 FB Photo Final Response: {response.status_code if response else 'FAILED'}")

        os.remove(file_path)

    # Case 2: Handle text-only messages
    elif message_text.strip():
        url = f"https://graph.facebook.com/{page_id}/feed"
        payload = {
            "message": message_text,
            "access_token": page_access_token,
        }

        response = post_with_retry(url, payload=payload)
        print(f"📤 FB Text Final Response: {response.status_code if response else 'FAILED'}")

# === Flask tiny web server (for Render) ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Telegram → Facebook forwarder is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Start Flask in a separate thread
threading.Thread(target=run_flask).start()

# ==== Start Telegram client ====
print("🚀 Forwarder is running with retry logic... Waiting for messages.")

try:
    client.start()
    client.run_until_disconnected()
except Exception as e:
    print(f"❌ Fatal error: {e}")            else:
                print(f"⚠️ Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Exception on attempt {attempt}: {e}")

        sleep_time = 2 ** attempt
        print(f"⏳ Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)

    print("🚨 All retries failed.")
    return None


# ==== Telegram Event Handler ====
@client.on(events.NewMessage(chats=target_chat_ids))
async def handler(event):
    message_text = event.message.message or ""
    print(f"📩 New message: {message_text}")

    # Case 1: Handle photos
    if event.message.photo:
        file_path = await event.message.download_media()
        print(f"📂 Downloaded photo: {file_path}")

        url = f"https://graph.facebook.com/{page_id}/photos"
        files = {"source": open(file_path, "rb")}
        payload = {
            "caption": message_text,
            "access_token": page_access_token,
        }

        response = post_with_retry(url, payload=payload, files=files)
        print(f"📤 FB Photo Final Response: {response.status_code if response else 'FAILED'}")

        os.remove(file_path)

    # Case 2: Handle text-only messages
    elif message_text.strip():
        url = f"https://graph.facebook.com/{page_id}/feed"
        payload = {
            "message": message_text,
            "access_token": page_access_token,
        }

        response = post_with_retry(url, payload=payload)
        print(f"📤 FB Text Final Response: {response.status_code if response else 'FAILED'}")


# ==== Flask tiny web server (for Render) ====
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Telegram → Facebook forwarder is running!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# Start Flask in a separate thread
threading.Thread(target=run_flask).start()


# ==== Start Telegram client ====
print("🚀 Forwarder is running with retry logic... Waiting for messages.")
client.start()
client.run_until_disconnected()        try:
            resp = requests.post(url, data=data, files=files, timeout=timeout)
            if resp.status_code == 200:
                print(f"✅ Success on attempt {attempt}")
                return resp.json()
            else:
                print(f"⚠️ Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"❌ Exception on attempt {attempt}: {e}")

        sleep_time = 2 ** attempt
        print(f"⏳ Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)
    print("🚨 All retries failed.")
    return None


# ==== TELEGRAM EVENT HANDLER ====
@client.on(events.NewMessage(chats=target_chat_ids))
async def handler(event):
    """Forward Telegram messages (photos + caption or text) to Facebook Page."""
    try:
        msg = event.message
        message_text = (getattr(msg, "message", None) or getattr(event, "raw_text", "") or "").strip()
        print(f"📩 New message (chat_id={event.chat_id}): {message_text}")

        # === Case A: Handle albums (multi-photo carousel) ===
        if event.grouped_id:
            print("🖼 Album detected — downloading photos...")
            grouped_msgs = await client.get_messages(
                event.chat_id,
                min_id=event.id - 20,
                max_id=event.id + 20
            )

            photos = []
            for m in grouped_msgs:
                if m.grouped_id == event.grouped_id and getattr(m, "photo", None):
                    file_path = await m.download_media()
                    if file_path:
                        photos.append(file_path)

            if not photos:
                print("⚠️ No photos found in album.")
                return

            print(f"📂 Downloaded {len(photos)} photos. Uploading to Facebook...")

            media_ids = []
            for i, photo_path in enumerate(photos, start=1):
                url = f"https://graph.facebook.com/{page_id}/photos"
                with open(photo_path, "rb") as f:
                    files = {"source": f}
                    data = {
                        "published": "false",  # don't publish immediately
                        "access_token": page_access_token
                    }
                    resp = post_with_retry(url, data=data, files=files)
                try:
                    os.remove(photo_path)
                except:
                    pass

                if resp and "id" in resp:
                    media_ids.append(resp["id"])
                    print(f"📤 Uploaded photo {i}/{len(photos)} (id={resp['id']})")
                else:
                    print(f"❌ Failed to upload photo {i}")

            if not media_ids:
                print("⚠️ No media IDs collected, aborting album post.")
                return

            # Now publish carousel post
            url = f"https://graph.facebook.com/{page_id}/feed"
            data = {
                "message": message_text,
                "access_token": page_access_token
            }
            for i, mid in enumerate(media_ids):
                data[f"attached_media[{i}]"] = f'{{"media_fbid":"{mid}"}}'

            resp = post_with_retry(url, data=data)
            if resp and "id" in resp:
                print(f"✅ Album posted successfully (post_id={resp['id']})")
            else:
                print("❌ Failed to create album post.")
            return

        # === Case B: Single photo ===
        if getattr(msg, "photo", None):
            print("🖼 Single photo detected — downloading...")
            file_path = await msg.download_media()
            if not file_path:
                print("⚠️ Failed to download photo.")
                return

            url = f"https://graph.facebook.com/{page_id}/photos"
            with open(file_path, "rb") as f:
                files = {"source": f}
                data = {"caption": message_text, "access_token": page_access_token}
                resp = post_with_retry(url, data=data, files=files)
            try:
                os.remove(file_path)
            except:
                pass

            if resp:
                print("📤 Single photo forwarded to Facebook.")
            else:
                print("❌ Single photo forwarding failed.")
            return

        # === Case C: Text-only ===
        if message_text:
            url = f"https://graph.facebook.com/{page_id}/feed"
            data = {"message": message_text, "access_token": page_access_token}
            resp = post_with_retry(url, data=data)
            if resp:
                print("📤 Text forwarded to Facebook.")
            else:
                print("❌ Text forwarding failed.")
            return

        print("ℹ️ Message ignored (no text, no photo).")

    except Exception as ex:
        print("Handler exception:", ex)


# ==== RUN TELEGRAM FORWARDER ====
def run_forwarder():
    try:
        print("🚀 Forwarder starting...")
        client.start()
        client.run_until_disconnected()
    except Exception as e:
        print("Forwarder crashed:", e)


# ==== FLASK (keep Render alive) ====
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram → Facebook forwarder is running."

if __name__ == "__main__":
    threading.Thread(target=run_forwarder, daemon=True).start()
    port = int(os.environ.get("PORT", "10000"))
    print(f"🌐 Starting Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(url, data=data, files=files, timeout=timeout)
            if resp.status_code == 200:
                print(f"✅ Success on attempt {attempt}")
                return resp
            else:
                print(f"⚠️ Error {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"❌ Exception on attempt {attempt}: {e}")

        sleep_time = 2 ** attempt
        print(f"⏳ Retrying in {sleep_time} seconds...")
        time.sleep(sleep_time)
    print("🚨 All retries failed.")
    return None


@client.on(events.NewMessage(chats=target_chat_ids))
async def handler(event):
    """Handle new Telegram messages: forward photos (with caption) or text exactly as-is."""
    try:
        msg = event.message
        # Get textual content (caption or plain text)
        message_text = (getattr(msg, "message", None) or getattr(event, "raw_text", "") or "") 
        message_text = message_text if message_text is not None else ""
        message_text_stripped = message_text.strip()

        print(f"📩 New message (chat_id={event.chat_id}): {message_text_stripped}")

        # Case A: Photo (only photos forwarded)
        if getattr(msg, "photo", None):
            print("🖼 Photo detected — downloading...")
            file_path = await msg.download_media()  # returns local path or None
            if not file_path:
                print("⚠️ Failed to download media.")
                return

            print(f"📂 Downloaded photo: {file_path}")
            url = f"https://graph.facebook.com/{page_id}/photos"
            try:
                with open(file_path, "rb") as f:
                    files = {"source": f}
                    data = {"caption": message_text, "access_token": page_access_token}
                    resp = post_with_retry(url, data=data, files=files)
                if resp:
                    print("📤 Photo forwarded to Facebook.")
                else:
                    print("❌ Photo forwarding failed after retries.")
            finally:
                # cleanup
                try:
                    os.remove(file_path)
                except Exception as e:
                    print("⚠️ Could not remove downloaded file:", e)
            return

        # Case B: Text-only messages (forward exactly, including URLs)
        if message_text_stripped:
            url = f"https://graph.facebook.com/{page_id}/feed"
            data = {"message": message_text, "access_token": page_access_token}
            resp = post_with_retry(url, data=data)
            if resp:
                print("📤 Text forwarded to Facebook.")
            else:
                print("❌ Text forwarding failed after retries.")
            return

        # Otherwise (no text & not a photo) — ignore
        print("ℹ️ Message has no text and is not a photo — ignored.")

    except Exception as ex:
        print("Handler exception:", ex)


def run_forwarder():
    """Start Telegram client and block until disconnected (runs in background thread)."""
    try:
        print("🚀 Forwarder starting (StringSession).")
        client.start()  # non-interactive because we're using a StringSession
        client.run_until_disconnected()
    except Exception as e:
        print("Forwarder crashed:", e)


# === Minimal Flask app (keeps Render web service alive) ===
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram → Facebook forwarder is running."

if __name__ == "__main__":
    # Run the forwarder in a daemon thread so Flask can run in the main thread (Render expects a web server)
    t = threading.Thread(target=run_forwarder, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", "10000"))
    print(f"🌐 Starting Flask server on port {port} (this keeps Render happy)")
    app.run(host="0.0.0.0", port=port)def post_with_retry(url, data=None, files=None, max_retries=3, timeout=30):
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
