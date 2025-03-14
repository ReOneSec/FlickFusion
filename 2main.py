import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from config import BOT_TOKEN
from database import initialize_db
from adminhandlers import add_movie_handler, list_movies_handler, delete_movie_handler
from userhandlers import handle_movie_request, search_movie

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update, context):
    """Send a welcome message when the command /start is issued."""
    await update.message.reply_text(
        "👋 Hello! I'm your Movie Request Bot.\nMade By @ViperROX\n\n"
        "Simply type a movie title (and optionally the year) to request a movie.\n"
        "Example: `Inception (2010)`\n\n"
        "Use /search to look for available movies.",
        parse_mode='Markdown'
    )

async def help_command(update, context):
    """Send a help message when the command /help is issued."""
    help_text = (
        "🎬 *Movie Bot Commands*\n\n"
        "*For Users:*\n"
        "• Type a movie title to request it (e.g., `Inception (2010)`)\n"
        "• `/search <title>` - Search for movies\n"
        "• `/start` - Get welcome message\n"
        "• `/help` - Show this help message\n\n"
        
        "*For Admins:*\n"
        "• `/addmovie <title>` - Add a new movie\n"
        "• `/listmovies` - List all available movies\n"
        "• `/deletemovie <id>` - Delete a movie by ID"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

def main():
    """Start the bot."""
    # Initialize database
    db = initialize_db()
    
    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search_movie))
    
    # Admin handlers
    application.add_handler(add_movie_handler)
    application.add_handler(list_movies_handler)
    application.add_handler(delete_movie_handler)
    
    # User movie request handler - should be last to catch all messages
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_movie_request
    ))
    
    # Start the Bot
    application.run_polling()
    
    # Close the database connection when done
    db.close()

if __name__ == '__main__':
    main()
  
