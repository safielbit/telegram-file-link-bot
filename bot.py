#!/usr/bin/env python3
"""
Telegram File Link Generator Bot
Converts Telegram files to streamable/downloadable links without storing files
"""

import os
import asyncio
import logging
from typing import Optional
from urllib.parse import quote
import hashlib
import hmac
import time
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.types import Message
import aiofiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramFileLinkBot:
    def __init__(self):
        self.api_id = int(os.getenv('TELEGRAM_API_ID', '0'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH', '') 
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.url_secret = os.getenv('URL_SECRET', 'default-secret-key-change-me')
        self.base_url = os.getenv('BASE_URL', 'https://your-bot-name.koyeb.app')
        
        # Validate required credentials
        if not self.api_id or self.api_id == 0:
            raise ValueError("TELEGRAM_API_ID is required")
        if not self.api_hash:
            raise ValueError("TELEGRAM_API_HASH is required") 
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        
        logger.info(f"Bot configured for URL: {self.base_url}")
        
        # Initialize Pyrogram client
        self.app = Client(
            "file_link_bot",
            api_id=self.api_id,
            api_hash=self.api_hash,
            bot_token=self.bot_token,
            in_memory=True
        )
        
        # Register handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup message handlers"""
        
        @self.app.on_message(filters.command("start"))
        async def start_command(client, message: Message):
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
            await message.reply_text(welcome_text)

        @self.app.on_message(filters.document | filters.video | filters.audio | filters.photo | filters.animation)
        async def handle_file(client, message: Message):
            try:
                await self.process_file_message(message)
            except Exception as e:
                logger.error(f"Error processing file: {e}")
                await message.reply_text("❌ Sorry, there was an error processing your file. Please try again.")

    async def process_file_message(self, message: Message):
        """Process incoming file message and generate links"""
        
        # Determine file type and get file info
        file_info = None
        file_name = "file"
        file_size = 0
        
        if message.document:
            file_info = message.document
            file_name = file_info.file_name or f"document_{file_info.file_id}.{file_info.mime_type.split('/')[-1] if file_info.mime_type else 'bin'}"
            file_size = file_info.file_size
        elif message.video:
            file_info = message.video
            file_name = file_info.file_name or f"video_{file_info.file_id}.mp4"
            file_size = file_info.file_size
        elif message.audio:
            file_info = message.audio
            file_name = file_info.file_name or f"audio_{file_info.file_id}.mp3"
            file_size = file_info.file_size
        elif message.photo:
            file_info = message.photo
            file_name = f"photo_{file_info.file_id}.jpg"
            file_size = file_info.file_size
        elif message.animation:
            file_info = message.animation
            file_name = file_info.file_name or f"animation_{file_info.file_id}.gif"
            file_size = file_info.file_size
        
        if not file_info:
            await message.reply_text("❌ Unsupported file type.")
            return
        
        # Get file path from Telegram
        try:
            file_path = await self.get_file_path(file_info.file_id)
            if not file_path:
                await message.reply_text("❌ Could not get file information from Telegram.")
                return
        except Exception as e:
            logger.error(f"Error getting file path: {e}")
            await message.reply_text("❌ Could not access file. Please try again.")
            return
        
        # Generate secure URLs
        stream_url = self.generate_stream_url(file_info.file_id, file_name, file_path)
        download_url = self.generate_download_url(file_path)
        
        # Format file size
        size_str = self.format_file_size(file_size)
        
        # Create response message
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
        
        await message.reply_text(response_text)

    async def get_file_path(self, file_id: str) -> Optional[str]:
        """Get file path from Telegram using file_id"""
        try:
            # Download the file to get file path information
            file_obj = await self.app.download_media(file_id, in_memory=True)
            # For streaming, we need to use Bot API to get file path
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.telegram.org/bot{self.bot_token}/getFile?file_id={file_id}") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('ok') and 'result' in data:
                            return data['result'].get('file_path')
            return None
        except Exception as e:
            logger.error(f"Error getting file path for {file_id}: {e}")
            return None

    def generate_stream_url(self, file_id: str, file_name: str, file_path: str) -> str:
        """Generate streaming URL for the web player"""
        # Create hash for security
        timestamp = str(int(time.time()))
        hash_string = f"{file_id}:{file_path}:{timestamp}:{self.url_secret}"
        url_hash = hmac.new(
            self.url_secret.encode(),
            hash_string.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        # URL encode the filename
        encoded_filename = quote(file_name)
        
        return f"{self.base_url}/watch/{file_id}/{encoded_filename}?hash={url_hash}&t={timestamp}"

    def generate_download_url(self, file_path: str) -> str:
        """Generate direct download URL from Telegram CDN"""
        return f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size_float = float(size_bytes)
        while size_float >= 1024 and i < len(size_names) - 1:
            size_float /= 1024.0
            i += 1
        return f"{size_float:.1f} {size_names[i]}"

    async def run(self):
        """Start the bot"""
        logger.info("Starting Telegram File Link Bot...")
        await self.app.start()
        logger.info("Bot started successfully!")
        # Keep the bot running
        try:
            import signal
            import asyncio
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        finally:
            await self.app.stop()

# Bot instance
bot = TelegramFileLinkBot()

if __name__ == "__main__":
    asyncio.run(bot.run())