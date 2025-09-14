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
    """Process photos and stickers for Facebook"""
    print(f"🔄 Processing {media_type} with caption: '{caption}'")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        try:
            file_path = await msg.download_media(file=os.path.join(tmp_dir, media_type))
            if not file_path:
                print("⚠️ Failed to download media.")
                return

            print(f"📂 Downloaded {media_type} to {file_path}")
            
            # Facebook photos endpoint for both photos and stickers
            url = f"https://graph.facebook.com/{page_id}/photos"
            
            print(f"🌐 Uploading to Facebook...")
            
            with open(file_path, "rb") as f:
                files = {"source": f}
                data = {"caption": caption, "access_token": page_access_token}
                
                resp = post_with_retry(url, data=data, files=files, timeout=30)
            
            if resp:
                print(f"📊 Facebook response: {resp.status_code}")
                
                if resp.status_code == 200:
                    fb_response = resp.json()
                    if "error" in fb_response:
                        print(f"❌ Facebook API error: {fb_response['error']['message']}")
                    else:
                        print(f"✅ {media_type.capitalize()} successfully forwarded to Facebook!")
                else:
                    print(f"❌ Facebook API returned error: {resp.status_code}")
                    print(f"📄 Response: {resp.text[:200]}...")
            else:
                print("❌ No response from Facebook API after retries")
                
        except Exception as download_error:
            print(f"❌ Failed to process {media_type}: {str(download_error)}")

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
        # Check for supported media types only
        media_type = None
        
        # Photos
        if getattr(msg, "photo", None):
            media_type = "photo"
            
        # Stickers (we'll process them as images)
        elif getattr(msg, "sticker", None):
            media_type = "sticker"
        
        # Process media if detected
        if media_type:
            print(f"📦 {media_type.capitalize()} detected")
            await process_media(msg, message_text, media_type)
            
        # Text only messages
        elif message_text.strip():
            print("📝 Text message detected")
            url = f"https://graph.facebook.com/{page_id}/feed"
            data = {"message": message_text, "access_token": page_access_token}
            resp = post_with_retry(url
