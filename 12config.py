import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_ID").split(",")]
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
AUTH_GROUPS = [int(id) for id in os.getenv("AUTH_GRP").split(",")]
DATABASE_URL = os.getenv("DATABASE_URL", "movies.db")

# Validate configuration
if not all([BOT_TOKEN, ADMIN_IDS, CHANNEL_ID, AUTH_GROUPS]):
    raise ValueError("Missing required environment variables. Check your .env file.")
  
