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
from pyrogram.errors import UserDeactivated, AuthKeyUnregistered

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
        self.token = os.getenv("TG_BOT_TOKEN")
        
        if not self.token:
            logger.error("TG_BOT_TOKEN environment variable not set!")
            sys.exit(1)
            
        # Remove any quotes or whitespace from the token
        self.token = self.token.strip().strip('"').strip("'")

    async def validate_token(self):
        """Validate the bot token before starting"""
        try:
            logger.info(f"Attempting to validate token: {self.token[:10]}...")
            
            # Create a temporary client to validate the token with explicit parameters
            async with Client(
                name="temp_session",
                api_id=1,  # Placeholder, we'll use get_me which doesn't need full auth
                api_hash="placeholder",  # Placeholder
                bot_token=self.token,
                in_memory=True
            ) as temp_client:
                me = await temp_client.get_me()
                logger.info(f"Token validated for bot: @{me.username} (ID: {me.id})")
                return True
                
        except (UserDeactivated, AuthKeyUnregistered):
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
            logger.error(f"Token being used: {self.token}")
            return False

    async def start(self):
        """Start the bot"""
        try:
            logger.info("Validating bot token...")
            if not await self.validate_token():
                sys.exit(1)
            
            logger.info("Starting FileStore Bot...")
            # Initialize the client with proper parameters
            self.bot = Client(
                "my_bot_session",
                bot_token=self.token,
                api_id=1,  # You need to get actual API ID from https://my.telegram.org
                api_hash="your_api_hash_here"  # You need to get actual API Hash
            )
            
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
            
        except (UserDeactivated, AuthKeyUnregistered):
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
