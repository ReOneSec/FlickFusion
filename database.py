from peewee import *
from config import DATABASE_URL
import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection
# Determine database type based on URL
if DATABASE_URL.endswith('.db'):
    db = SqliteDatabase(DATABASE_URL)
    logger.info(f"Using SQLite database: {DATABASE_URL}")
else:
    db = PostgresqlDatabase(DATABASE_URL)
    logger.info(f"Using PostgreSQL database: {DATABASE_URL}")

class BaseModel(Model):
    class Meta:
        database = db

class Movie(BaseModel):
    title = CharField(max_length=200)
    year = IntegerField(null=True)
    description = TextField(null=True)
    # Change to BigIntegerField for Telegram message IDs
    message_id = BigIntegerField(unique=True)
    # Change to BigIntegerField for Telegram user IDs
    added_by = BigIntegerField()
    added_at = DateTimeField(default=datetime.datetime.now)
    
    class Meta:
        indexes = (
            # Create a unique index on title/year combination
            (('title', 'year'), True),
        )

class RequestLog(BaseModel):
    # Change to BigIntegerField for Telegram user IDs
    user_id = BigIntegerField()
    movie_id = ForeignKeyField(Movie, backref='requests')
    request_time = DateTimeField(default=datetime.datetime.now)
    # Change to BigIntegerField for Telegram group IDs
    group_id = BigIntegerField(null=True)

# Add User model for force join functionality
class User(BaseModel):
    user_id = BigIntegerField(primary_key=True)
    username = CharField(null=True)
    first_name = CharField()
    last_name = CharField(null=True)
    is_member = BooleanField(default=False)
    last_checked = DateTimeField(default=datetime.datetime.now)
    joined_date = DateTimeField(default=datetime.datetime.now)

def initialize_db():
    """Initialize the database and create tables if they don't exist."""
    db.connect()
    db.create_tables([Movie, RequestLog, User], safe=True)
    logger.info("Database initialized with tables: Movie, RequestLog, User")
    return db
