import logging
from database import db, User

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_user_table():
    """Add User table to the database."""
    # Connect to the database
    db.connect()
    
    logger.info("Starting database migration: Adding User table")
    
    # Create User table if it doesn't exist
    db.create_tables([User], safe=True)
    
    logger.info("Migration completed successfully!")
    
    # Close the database connection
    db.close()

if __name__ == "__main__":
    try:
        migrate_user_table()
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
