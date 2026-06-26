import os
import json
import logging
from datetime import datetime
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError
from dotenv import load_dotenv

load_dotenv()

class TelegramScraper:
    
    def __init__(self, api_id: int, api_hash: str, request_delay: float = 1.0, session_name: str = 'scraper_session'):
        self.api_id = api_id
        self.api_hash = api_hash
        self.request_delay = request_delay
        self.session_name = session_name
        
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        self.total_processed = 0
        self.successful_downloads = 0
        
        self._setup_logging()

    def _setup_logging(self):
        
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, "scraper.log")

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, encoding='utf-8'),
                logging.StreamHandler()
            ],
            force=True
        )
        self.logger = logging.getLogger("TelegramScraper")

    async def connect(self):
        if not self.client.is_connected():
            self.logger.info("Connecting and authenticating Telegram client...")
            await self.client.start()
            self.logger.info("Telegram Client connected and authenticated successfully.")

    async def scrape_channels(self, channels_list: list, limit_per_channel: int = 100):
        
        await self.connect()

        self.logger.info(f"Starting batch pipeline for {len(channels_list)} target channels.")
        
        for channel in channels_list:
            await self._scrape_single_channel(channel, limit=limit_per_channel)
            
        self.logger.info("Batch pipeline execution sequence finished.")

    async def _scrape_single_channel(self, channel_username: str, limit: int):

        clean_channel = channel_username.lstrip('@').strip()
        self.logger.info(f"Beginning data extraction for target: {clean_channel}")
        
        partitioned_buffer = {}
        self.total_processed = 0
        self.successful_downloads = 0

        try:
            async for message in self.client.iter_messages(channel_username, limit=limit):
                self.total_processed += 1
                
                date_str = message.date.strftime('%Y-%m-%d') if message.date else "unknown_date"
                
                raw_message_data = json.loads(message.to_json())
                
                if date_str not in partitioned_buffer:
                    partitioned_buffer[date_str] = []
                partitioned_buffer[date_str].append(raw_message_data)
                
                if getattr(message, 'photo', None):
                    await self._download_image(message, clean_channel)
                await asyncio.sleep(self.request_delay)

        except FloodWaitError as e:
            self.logger.warning(f"Hit aggressive Telegram rate boundaries. Cooldown forced: {e.seconds}s.")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            self.logger.critical(f"Scraping run broken unexpectedly on channel {clean_channel}: {e}", exc_info=True)
            return

        await self._flush_buffer_to_lake(clean_channel, partitioned_buffer)
        
        self.logger.info(
            f"Run Finished for {clean_channel}. "
            f"Processed: {self.total_processed} items | Photos Downloaded: {self.successful_downloads}"
        )

    async def _download_image(self, message, channel_name: str):
        img_dir = f"data/raw/images/{channel_name}"
        os.makedirs(img_dir, exist_ok=True)
        target_path = os.path.join(img_dir, f"{message.id}.jpg")
        
        try:
            await message.download_media(file=target_path)
            self.successful_downloads += 1
        except Exception as err:
            self.logger.error(f"Failed image payload save on Message ID {message.id}: {err}")

    async def _flush_buffer_to_lake(self, channel_name: str, buffer: dict):
        
        self.logger.info(f"Committing memory buffers to data lake storage partitions for {channel_name}...")
        
        for date_key, messages in buffer.items():
            lake_dir = f"data/raw/telegram_messages/{date_key}"
            os.makedirs(lake_dir, exist_ok=True)
            lake_file_path = os.path.join(lake_dir, f"{channel_name}.json")
            
            existing_records = []
            if os.path.exists(lake_file_path):
                try:
                    with open(lake_file_path, 'r', encoding='utf-8') as f:
                        existing_records = json.load(f)
                except Exception:
                    self.logger.error(f"Stale parsing conflict at {lake_file_path}. Rewriting partition.")

            seen_ids = {msg.get('id') for msg in existing_records if 'id' in msg}
            for new_msg in messages:
                if new_msg.get('id') not in seen_ids:
                    existing_records.append(new_msg)

           
            try:
                with open(lake_file_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_records, f, indent=4, ensure_ascii=False)
            except Exception as io_err:
                self.logger.error(f"Failed to persist partition path {lake_file_path}: {io_err}")

    async def disconnect(self):
        if self.client and self.client.is_connected():
            await self.client.disconnect()
            self.logger.info("Telegram client disconnected smoothly.")


if __name__ == '__main__':
    MY_API_ID = os.getenv('API_ID')               
    MY_API_HASH = os.getenv('API_HASH')
    TARGETS_LIST = ['CheMed123', 'lobelia4cosmetics']
    
    scraper = TelegramScraper(api_id=MY_API_ID, api_hash=MY_API_HASH, request_delay=1.0)
    
    async def run_pipeline():
        try:
            await scraper.connect()
            await scraper.scrape_channels(TARGETS_LIST, limit_per_channel=50)
                
        finally:
            await scraper.disconnect()

    asyncio.run(run_pipeline())