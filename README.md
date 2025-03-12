# FlickFusion

Telegram Movie Request Bot Implementation Guide
Project Overview
The Telegram Movie Request Bot is designed to streamline movie sharing by automatically forwarding movies from a private channel to authorized groups based on user requests. This bot maintains a database of movies with their corresponding message IDs, allowing users to request movies by title and year while giving admins tools to manage the movie collection.

Core Architecture:

Bot listens for user requests in authorized groups
Parses movie titles and years from user messages
Searches the database for matching movies
Forwards the corresponding message from the private channel to the group
Provides admin commands for managing the movie database
Project Structure
telegram-movie-bot/  
├── main.py # Entry point and bot initialization

├── config.py # Configuration management

├── database.py # Database models and connection

├── adminhandlers.py    # Admin command handlers

├── userhandlers.py     # User request handlers

├── utils.py            # Utility functions

├── requirements.txt    # Dependencies

├── .env                # Environment variables

└── movies.db           # SQLite database (auto-generated)

# Environment Setup
Requirements
Create a requirements.txt file with the following dependencies:

```python-telegram-bot==20.3```
```peewee==3.16.0```
```python-dotenv==1.0.0```

Environment Variables
Create a .env file with the following configuration:

CopyBOT_TOKEN=your_bot_token
ADMIN_ID=your_user_id,another_admin_id  # Comma-separated for multiple admins
CHANNEL_ID=your_channel_id
AUTH_GRP=authorised_group_id,another_group_id  # Comma-separated for multiple groups
DATABASE_URL=sql-databases.url  # Optional, defaults to local SQLite
