#!/usr/bin/env python3
"""
Main application entry point
Runs both the Telegram bot and FastAPI server
"""

import asyncio
import os
import logging
import threading
from bot import bot
from server import app
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_server():
    """Run FastAPI server in a separate thread"""
    port = int(os.getenv('PORT', 5000))
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )

async def run_bot():
    """Run Telegram bot"""
    try:
        await bot.run()
    except Exception as e:
        logger.error(f"Bot error: {e}")

async def main():
    """Main application entry point"""
    logger.info("Starting Telegram File Link Generator...")
    
    # Start FastAPI server in a separate thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    logger.info("FastAPI server started on port 5000")
    
    # Run the bot in the main thread
    await run_bot()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")