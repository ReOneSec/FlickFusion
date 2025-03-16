# migrate_db.py
from database import db, User
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def migrate_db():
    """Add verification fields to User model"""
    logger.info("Starting database migration")
    db.connect()
    
    # Check if the columns already exist
    cursor = db.execute_sql("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add verification_token column if it doesn't exist
    if 'verification_token' not in columns:
        db.execute_sql("ALTER TABLE users ADD COLUMN verification_token TEXT;")
        logger.info("Added verification_token column")
    
    # Add token_created_at column if it doesn't exist
    if 'token_created_at' not in columns:
        db.execute_sql("ALTER TABLE users ADD COLUMN token_created_at TIMESTAMP;")
        logger.info("Added token_created_at column")
    
    # Add verified_until column if it doesn't exist
    if 'verified_until' not in columns:
        db.execute_sql("ALTER TABLE users ADD COLUMN verified_until TIMESTAMP;")
        logger.info("Added verified_until column")
    
    db.close()
    logger.info("Database migration completed")

if __name__ == "__main__":
    migrate_db()
