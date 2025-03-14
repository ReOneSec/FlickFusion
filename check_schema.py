import os
from dotenv import load_dotenv
import psycopg2
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def check_schema():
    """Check database schema."""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check Movie table
        logger.info("Checking Movie table schema:")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'movie'
            ORDER BY column_name;
        """)
        
        for row in cursor.fetchall():
            logger.info(f"  {row[0]}: {row[1]}")
        
        # Check RequestLog table
        logger.info("\nChecking RequestLog table schema:")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'requestlog'
            ORDER BY column_name;
        """)
        
        for row in cursor.fetchall():
            logger.info(f"  {row[0]}: {row[1]}")
        
        # Close connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking schema: {str(e)}")

if __name__ == "__main__":
    check_schema()
