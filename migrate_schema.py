# migrate_schema.py
import logging
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

def migrate_database():
    """Migrate database columns from INTEGER to BIGINT."""
    logger.info("Starting database migration: Converting INTEGER columns to BIGINT")
    
    # Connect to the database
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False  # Start a transaction
        cursor = conn.cursor()
        
        try:
            # Alter Movie table columns
            logger.info("Altering Movie.message_id column to BIGINT")
            cursor.execute("ALTER TABLE movie ALTER COLUMN message_id TYPE BIGINT;")
            
            logger.info("Altering Movie.added_by column to BIGINT")
            cursor.execute("ALTER TABLE movie ALTER COLUMN added_by TYPE BIGINT;")
            
            # Alter RequestLog table columns
            logger.info("Altering RequestLog.user_id column to BIGINT")
            cursor.execute("ALTER TABLE requestlog ALTER COLUMN user_id TYPE BIGINT;")
            
            logger.info("Altering RequestLog.group_id column to BIGINT")
            cursor.execute("ALTER TABLE requestlog ALTER COLUMN group_id TYPE BIGINT;")
            
            # Commit the transaction
            conn.commit()
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            # If anything goes wrong, roll back the transaction
            conn.rollback()
            logger.error(f"Migration failed: {str(e)}")
            raise
        finally:
            cursor.close()
            
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    try:
        migrate_database()
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
