from http.server import BaseHTTPRequestHandler
import json
import os
import asyncio
import aiohttp
from urllib.parse import quote
import hashlib
import hmac
import time

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read the request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            
            # Parse Telegram update
            update = json.loads(body.decode('utf-8'))
            
            # Process the update
            asyncio.run(self.process_update(update))
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    async def process_update(self, update):
        """Process Telegram webhook update"""
        if 'message' not in update:
            return
        
        message = update['message']
        chat_id = message['chat']['id']
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        # Handle /start command
        if message.get('text') == '/start':
            welcome_text = """
🤖 **Welcome to File Link Generator Bot!**

Send me any file and I'll generate streaming and download links for you.

**Supported formats:**
• Images (JPG, PNG, GIF, etc.)
• Videos (MP4, AVI, MOV, etc.) 
• Audio files (MP3, WAV, etc.)
• Documents (PDF, TXT, etc.)

**Features:**
• Direct streaming links via Telegram's CDN
• Download links 
• No file storage - uses Telegram's servers
• Fast access from any browser

Just drop your file and I'll handle the rest! 📁✨
            """
            await self.send_message(chat_id, welcome_text, bot_token)
            return
        
        # Handle file uploads
        file_info = None
        file_name = "file"
        
        if 'document' in message:
            file_info = message['document']
            file_name = file_info.get('file_name', f"document_{file_info['file_id']}.bin")
        elif 'video' in message:
            file_info = message['video']
            file_name = file_info.get('file_name', f"video_{file_info['file_id']}.mp4")
        elif 'audio' in message:
            file_info = message['audio']
            file_name = file_info.get('file_name', f"audio_{file_info['file_id']}.mp3")
        elif 'photo' in message:
            # Get the largest photo
            file_info = max(message['photo'], key=lambda x: x.get('file_size', 0))
            file_name = f"photo_{file_info['file_id']}.jpg"
        elif 'animation' in message:
            file_info = message['animation']
            file_name = file_info.get('file_name', f"animation_{file_info['file_id']}.gif")
        
        if not file_info:
            await self.send_message(chat_id, "❌ Unsupported file type.", bot_token)
            return
        
        # Get file path from Telegram
        file_path = await self.get_file_path(file_info['file_id'], bot_token)
        if not file_path:
            await self.send_message(chat_id, "❌ Could not get file information.", bot_token)
            return
        
        # Generate URLs
        base_url = os.getenv('VERCEL_URL', 'https://your-vercel-app.vercel.app')
        if not base_url.startswith('http'):
            base_url = f'https://{base_url}'
            
        stream_url = self.generate_stream_url(file_info['file_id'], file_name, base_url)
        download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        
        # Format file size
        file_size = file_info.get('file_size', 0)
        size_str = self.format_file_size(file_size)
        
        response_text = f"""
✅ **File processed successfully!**

📁 **File:** `{file_name}`
📊 **Size:** {size_str}

🔗 **Stream Link:** 
`{stream_url}`

⬇️ **Download Link:**
`{download_url}`

💡 **Usage:**
• Stream link opens in browser player
• Download link saves file directly
• Links work from any device
• Powered by Telegram's CDN

*Tap to copy the links above* 📋
        """
        
        await self.send_message(chat_id, response_text, bot_token)

    async def send_message(self, chat_id, text, bot_token):
        """Send message via Telegram Bot API"""
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            await session.post(url, json=data)

    async def get_file_path(self, file_id, bot_token):
        """Get file path from Telegram API"""
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{bot_token}/getFile"
            params = {'file_id': file_id}
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('ok'):
                        return data['result'].get('file_path')
        return None

    def generate_stream_url(self, file_id, file_name, base_url):
        """Generate streaming URL"""
        timestamp = str(int(time.time()))
        url_secret = os.getenv('URL_SECRET', 'default-secret')
        
        hash_string = f"{file_id}:{timestamp}:{url_secret}"
        url_hash = hmac.new(
            url_secret.encode(),
            hash_string.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        encoded_filename = quote(file_name)
        return f"{base_url}/watch/{file_id}/{encoded_filename}?hash={url_hash}&t={timestamp}"

    def format_file_size(self, size_bytes):
        """Format file size"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size_float = float(size_bytes)
        while size_float >= 1024 and i < len(size_names) - 1:
            size_float /= 1024.0
            i += 1
        return f"{size_float:.1f} {size_names[i]}"