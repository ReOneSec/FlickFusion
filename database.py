from peewee import *
from config import DATABASE_URL
import datetime

# Database connection
db = SqliteDatabase(DATABASE_URL)

class BaseModel(Model):
    class Meta:
        database = db

class Movie(BaseModel):
    title = CharField(max_length=200)
    year = IntegerField(null=True)
    description = TextField(null=True)
    message_id = IntegerField(unique=True)
    added_by = IntegerField()
    added_at = DateTimeField(default=datetime.datetime.now)
    
    class Meta:
        indexes = (
            # Create a unique index on title/year combination
            (('title', 'year'), True),
        )

class RequestLog(BaseModel):
    user_id = IntegerField()
    movie_id = ForeignKeyField(Movie, backref='requests')
    request_time = DateTimeField(default=datetime.datetime.now)
    group_id = IntegerField(null=True)

def initialize_db():
    """Initialize the database and create tables if they don't exist."""
    db.connect()
    db.create_tables([Movie, RequestLog], safe=True)
    return db
