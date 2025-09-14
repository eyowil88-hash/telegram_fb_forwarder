import os
import time
import asyncio
import requests
import json
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import tempfile

print("🔧 Starting Telegram to Facebook forwarder as Web Service...")

# Load configuration from environment variables
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
string_session = os.environ.get('STRING_SESSION')
page_id = os.environ.get('PAGE_ID')
page_access_token = os.environ.get('PAGE_ACCESS_TOKEN')

# Validate required environment variables
required_vars = {
    'API_ID': api_id,
    'API_HASH': api_hash,
    'STRING_SESSION': string_session,
    'PAGE_ID': page_id,
    'PAGE_ACCESS_TOKEN': page_access_token
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    error_msg = f"Missing environment variables: {', '.join(missing_vars)}"
    print(f"❌ {error_msg}")
    raise ValueError(error_msg)

try:
    api_id = int(api_id)
except (ValueError, TypeError):
    error_msg = "API_ID must be an integer"
    print(f"❌ {error_msg}")
    raise ValueError(error_msg)

print("✅ Environment variables loaded successfully")

# Target Telegram chat IDs
target_chat_ids = [
    -1002246802603,   # •NIA•💎PRIVATE CLUB💎•channel•
    -1001478882874,   # All Nigeria Latest News
    -1002196614972    # 💸Trade with Nia💸
]

# Create Telegram client
client = TelegramClient(StringSession(string_session), api_id, api_hash)

# Rate limiting
last_post_time = 0
MIN_POST_INTERVAL = 2

def post_with_retry(url, data=None, files=None, max_retries=3, timeout=30):
    for attempt in range(1, max_retries + 1):
        try:
            if files:
                resp = requests.post(url, data=data, files=files, timeout=timeout)
            else:
                resp = requests.post(url, data=data, timeout=timeout)
            
            if resp.status_code == 200:
                print(f"✅ Success on attempt {attempt}")
                try:
                    response_json = resp.json()
                    if "error" in response_json:
                        print(f"❌ Facebook API error: {response_json['error']['message']}")
                        return None
                except:
                    pass
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

async def process_media(msg, caption, media_type):
    """Process different types of media and upload to Facebook"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            file_path = await msg.download_media(file=os.path.join(tmp_dir, media_type))
            if not file_path:
                print("⚠️ Failed to download media.")
                return

            print(f"📂 Downloaded {media_type} to {file_path}")
            
            # Facebook supports different endpoints for different media
            if media_type in ["photo", "sticker", "image"]:
                url = f"https://graph.facebook.com/{page_id}/photos"
                file_param = "source"
            elif media_type == "video":
                url = f"https://graph.facebook.com/{page_id}/videos"
                file_param = "file"
            else:
                print(f"❌ Unsupported media type: {media_type}")
                return
            
            with open(file_path, "rb") as f:
                files = {file_param: f}
                data = {"caption": caption, "access_token": page_access_token}
                
                # For videos, we need to use a longer timeout
                timeout = 60 if media_type == "video" else 30
                resp = post_with_retry(url, data=data, files=files, timeout=timeout)
            
            if resp and resp.status_code == 200:
                fb_response = resp.json()
                if "error" in fb_response:
                    print(f"❌ Facebook API error: {fb_response['error']['message']}")
                else:
                    print(f"📤 {media_type.capitalize()} forwarded to Facebook.")
            else:
                print(f"❌ {media_type.capitalize()} forwarding failed.")
                
        except Exception as download_error:
            print(f"❌ Failed to process {media_type}: {download_error}")

@client.on(events.NewMessage(chats=target_chat_ids))
async def handler(event):
    global last_post_time
    
    msg = event.message
    message_text = getattr(msg, "message", "") or getattr(event, "raw_text", "") or ""
    print(f"📩 New message from chat {event.chat_id}: {message_text}")

    current_time = time.time()
    if current_time - last_post_time < MIN_POST_INTERVAL:
        wait_time = MIN_POST_INTERVAL - (current_time - last_post_time)
        print(f"⏳ Rate limiting: waiting {wait_time:.2f} seconds")
        await asyncio.sleep(wait_time)
    
    last_post_time = time.time()

    try:
        # Check for various media types
        media_type = None
        
        # Photos
        if getattr(msg, "photo", None):
            media_type = "photo"
            
        # Stickers
        elif getattr(msg, "sticker", None):
            media_type = "sticker"
            
        # Videos
        elif getattr(msg, "video", None):
            media_type = "video"
            
        # Documents (could be images, PDFs, etc.)
        elif getattr(msg, "document", None):
            document = msg.document
            if document:
                # Check if document is an image
                if document.mime_type and document.mime_type.startswith('image/'):
                    media_type = "image"
                # Check if document is a video
                elif document.mime_type and document.mime_type.startswith('video/'):
                    media_type = "video"
                else:
                    print(f"📄 Document detected but not processed (type: {document.mime_type})")
        
        # Process media if detected
        if media_type:
            print(f"📦 {media_type.capitalize()} detected — downloading...")
            await process_media(msg, message_text, media_type)
            
        # Text only messages
        elif message_text.strip():
            url = f"https://graph.facebook.com/{page_id}/feed"
            data = {"message": message_text, "access_token": page_access_token}
            resp = post_with_retry(url, data=data)
            if resp:
                print("📤 Text forwarded to Facebook.")
            else:
                print("❌ Text forwarding failed.")
                
        else:
            print("ℹ️ Ignored message (no processable content).")

    except Exception as ex:
        print(f"Handler exception: {ex}")

def run_telegram_client():
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        print("🚀 Starting Telegram client...")
        with client:
            print("✅ Telegram client started successfully")
            print("🤖 Bot is now running and listening for messages...")
            print("📡 Supported media types: photos, stickers, videos, images")
            client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Telegram client crashed: {e}")

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Telegram → Facebook forwarder is running."

@app.route('/health')
def health():
    return "OK", 200

@app.route('/status')
def status():
    return {
        "status": "running",
        "service": "Telegram to Facebook Forwarder",
        "telegram": "connected" if client.is_connected() else "disconnected",
        "supported_media": ["photos", "stickers", "videos", "images", "text"],
        "target_chats": target_chat_ids
    }

if __name__ == "__main__":
    # Start Telegram client in a separate thread
    telegram_thread = Thread(target=run_telegram_client, daemon=True)
    telegram_thread.start()
    
    # Start Flask server in main thread (this is what Render expects)
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Starting Flask server on port {port}")
    print(f"🔗 Web service will be available at: https://telegram-fb-forwarder.onrender.com")
    print(f"📊 Check status at: https://telegram-fb-forwarder.onrender.com/status")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
