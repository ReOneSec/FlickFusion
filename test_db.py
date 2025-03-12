# test_db.py
from database import initialize_db, db, Movie

try:
    db = initialize_db()
    print(f"Database connection successful: {db}")
    
    # Attempt to create a test record
    test_movie = Movie.create(
        title="Test Movie",
        year=2023,
        description="Test description",
        message_id=99999,
        added_by=12345
    )
    print(f"Test record created with ID: {test_movie.id}")
    
    # Clean up the test record
    test_movie.delete_instance()
    print("Test record deleted successfully")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if not db.is_closed():
        db.close()
        print("Database connection closed")
