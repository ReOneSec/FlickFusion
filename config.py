import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
AUTH_GROUPS = [int(id) for id in os.getenv("AUTH_GRP").split(",")]
DATABASE_URL = os.getenv("DATABASE_URL", "movies.db")

# Dynamic channel configuration
def get_required_channels():
    """Dynamically build the list of required channels from environment variables."""
    channels = []
    i = 1
    
    while True:
        channel_id_key = f"REQUIRED_CHANNEL{i}_ID"
        channel_id = os.getenv(channel_id_key)
        
        if not channel_id:
            break  # No more channels defined
            
        channels.append({
            'channel_id': int(channel_id),
            'channel_name': os.getenv(f"REQUIRED_CHANNEL{i}_NAME", f"Channel {i}"),
            'invite_link': os.getenv(f"REQUIRED_CHANNEL{i}_LINK", f"https://t.me/channel{i}")
        })
        
        i += 1
    
    # If no channels were defined, use the main channel as a fallback
    if not channels:
        channels.append({
            'channel_id': CHANNEL_ID,
            'channel_name': "FlickFusion Movies",
            'invite_link': os.getenv("REQUIRED_CHANNEL1_LINK", "https://t.me/your_channel")
        })
    
    return channels

# Force join configuration
REQUIRED_CHANNELS = get_required_channels()

# Log the channels that will be required
logger = logging.getLogger(__name__)
logger.info(f"Requiring membership in {len(REQUIRED_CHANNELS)} channels:")
for i, channel in enumerate(REQUIRED_CHANNELS):
    logger.info(f"  {i+1}. {channel['channel_name']} (ID: {channel['channel_id']})")

# Validate configuration
if not all([BOT_TOKEN, ADMIN_IDS, CHANNEL_ID, AUTH_GROUPS]):
    raise ValueError("Missing required environment variables. Check your .env file.")
    
    # Verification configuration
MODIJI_API_TOKEN = os.getenv("MODIJI_API_TOKEN")
if not MODIJI_API_TOKEN:
    logger.error("MODIJI_API_TOKEN not found in environment variables!")

BOT_USERNAME = os.getenv("BOT_USERNAME", "FlickFusionBot")
