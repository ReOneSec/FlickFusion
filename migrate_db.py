# migrate_db.py
import logging
from peewee import PostgresqlDatabase
from config import DATABASE_URL

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate database columns from INTEGER to BIGINT."""
    # Connect to the database
    db = PostgresqlDatabase(DATABASE_URL)
    db.connect()
    
    logger.info("Starting database migration: Converting INTEGER columns to BIGINT")
    
    # Begin transaction
    with db.atomic() as transaction:
        try:
            # Alter Movie table columns
            logger.info("Altering Movie.message_id column")
            db.execute_sql("ALTER TABLE movie ALTER COLUMN message_id TYPE BIGINT;")
            
            logger.info("Altering Movie.added_by column")
            db.execute_sql("ALTER TABLE movie ALTER COLUMN added_by TYPE BIGINT;")
            
            # Alter RequestLog table columns
            logger.info("Altering RequestLog.user_id column")
            db.execute_sql("ALTER TABLE requestlog ALTER COLUMN user_id TYPE BIGINT;")
            
            logger.info("Altering RequestLog.group_id column")
            db.execute_sql("ALTER TABLE requestlog ALTER COLUMN group_id TYPE BIGINT;")
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            # If anything goes wrong, roll back the transaction
            transaction.rollback()
            logger.error(f"Migration failed: {str(e)}")
            raise
    
    # Close the database connection
    db.close()

if __name__ == "__main__":
    try:
        migrate_database()
    except Exception as e:
        logger.error(f"Migration script failed: {str(e)}")
      
