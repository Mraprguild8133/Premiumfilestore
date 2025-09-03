#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for the Telegram FileStore Bot
"""

import asyncio
import logging
import signal
import sys
import os
from typing import Optional

from pyrogram import Client
from pyrogram.errors import UserDeactivated

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("filestore_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class FileStoreBot:
    def __init__(self):
        self.bot: Optional[Client] = None
        self.shutdown_event = asyncio.Event()
        self.token = os.getenv("TG_BOT_TOKEN")  # Changed to TG_BOT_TOKEN
        
        if not self.token:
            logger.error("TG_BOT_TOKEN environment variable not set!")  # Updated error message
            sys.exit(1)

    async def validate_token(self):
        """Validate the bot token before starting"""
        try:
            # Create a temporary client to validate the token
            async with Client("temp_session", self.token) as temp_client:
                me = await temp_client.get_me()
                logger.info(f"Token validated for bot: @{me.username}")
                return True
        except UserDeactivated:
            logger.error("""
            The bot token is invalid or the bot has been deactivated.
            Please check:
            1. Your bot token is correct and properly set in the TG_BOT_TOKEN environment variable
            2. The bot hasn't been banned or deleted by Telegram
            3. You've obtained the token from @BotFather
            """)
            return False
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return False

    async def start(self):
        """Start the bot"""
        try:
            logger.info("Validating bot token...")
            if not await self.validate_token():
                sys.exit(1)
            
            logger.info("Starting FileStore Bot...")
            self.bot = Client("my_bot", bot_token=self.token)
            
            # Set up signal handlers for graceful shutdown
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(
                    sig, 
                    lambda: asyncio.create_task(self.shutdown(sig))
                )
            
            await self.bot.start()
            logger.info("Bot started successfully!")
            
            # Keep the bot running until shutdown signal
            await self.shutdown_event.wait()
            
        except UserDeactivated:
            logger.error("""
            The bot token is invalid or the bot has been deactivated.
            Please check:
            1. Your bot token is correct and properly set in the TG_BOT_TOKEN environment variable
            2. The bot hasn't been banned or deleted by Telegram
            3. You've obtained the token from @BotFather
            """)
            raise
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise

    async def shutdown(self, signal=None):
        """Shutdown the bot gracefully"""
        if signal:
            logger.info(f"Received exit signal {signal.name}...")
        
        logger.info("Shutting down bot...")
        if self.bot:
            await self.bot.stop()
        
        self.shutdown_event.set()

async def main():
    """Main function to run the bot"""
    bot_instance = FileStoreBot()
    try:
        await bot_instance.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
        await bot_instance.shutdown()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await bot_instance.shutdown()
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
