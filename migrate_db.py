from database import db, User

def migrate_db():
    db.connect()
    
    # Check if the columns already exist
    cursor = db.execute_sql("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add verification_token column if it doesn't exist
    if 'verification_token' not in columns:
        db.execute_sql("ALTER TABLE users ADD COLUMN verification_token TEXT;")
        print("Added verification_token column")
    
    # Add token_created_at column if it doesn't exist
    if 'token_created_at' not in columns:
        db.execute_sql("ALTER TABLE users ADD COLUMN token_created_at TIMESTAMP;")
        print("Added token_created_at column")
    
    # Add verified_until column if it doesn't exist
    if 'verified_until' not in columns:
        db.execute_sql("ALTER TABLE users ADD COLUMN verified_until TIMESTAMP;")
        print("Added verified_until column")
    
    db.close()
    print("Database migration completed")

if __name__ == "__main__":
    migrate_db()
