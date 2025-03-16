from database import db, User
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def migrate_db():
    """Add verification fields to User model"""
    logger.info("Starting database migration")
    
    # Ensure database connection is open
    need_to_close = False
    if db.is_closed():
        db.connect()
        need_to_close = True
    
    try:
        # Check if columns exist in PostgreSQL
        cursor = db.execute_sql("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users'
        """)
        existing_columns = [column[0].lower() for column in cursor.fetchall()]
        
        # Add verification_token column if it doesn't exist
        if 'verification_token' not in existing_columns:
            db.execute_sql("ALTER TABLE users ADD COLUMN verification_token TEXT;")
            logger.info("Added verification_token column")
        
        # Add token_created_at column if it doesn't exist
        if 'token_created_at' not in existing_columns:
            db.execute_sql("ALTER TABLE users ADD COLUMN token_created_at TIMESTAMP;")
            logger.info("Added token_created_at column")
        
        # Add verified_until column if it doesn't exist
        if 'verified_until' not in existing_columns:
            db.execute_sql("ALTER TABLE users ADD COLUMN verified_until TIMESTAMP;")
            logger.info("Added verified_until column")
        
        logger.info("Database migration completed successfully")
    except Exception as e:
        logger.error(f"Error during migration: {e}")
    finally:
        # Only close the connection if we opened it
        if need_to_close and not db.is_closed():
            db.close()

if __name__ == "__main__":
    migrate_db()
