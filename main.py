import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes
from config import BOT_TOKEN
from database import initialize_db
from adminhandlers import add_movie_handler, list_movies_handler, delete_movie_handler
from userhandlers import handle_movie_request, search_movie

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)  # Fixed: Changed from 'name' to '__name__'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message with image when the command /start is issued."""
    chat_id = update.effective_chat.id
    
    # Send welcome image with caption
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo="https://i.ibb.co/N6b3MVpj/1741892600514.jpg",
            caption=(
                "**🎬 Welcome to FlickFusion, Movie Lover! 🍿**\n\n"
                "Hey there! I'm **FlickFusion**, your go-to bot for instant movie magic. 🪄 "
                "Need a film? Just drop your request in the group, in this Format \"/search [Movie Name]\".\n\n"
                "__**Let's dive into the world of cinema. Sit back, grab popcorn, and enjoy! 🎥**__\n\n"
                "**Crafted with ❤️ by @ViperROX.**\n"
                "Have questions? Just type /help !"
            ),
            parse_mode='Markdown'
        )
        logger.info(f"Sent welcome message and image to chat ID: {chat_id}")
    except Exception as e:
        # Fallback to text-only message if image fails
        logger.error(f"Failed to send welcome image: {str(e)}")
        await update.message.reply_text(
            "🎬 Welcome to FlickFusion, Movie Lover! 🍿\n\n"
            "Hey there! I'm FlickFusion, your go-to bot for instant movie magic. 🪄 "
            "Need a film? Just drop your request in the group, in this Format \"/search [Movie Name]\".\n\n"
            "Let's dive into the world of cinema. Sit back, grab popcorn, and enjoy! 🎥\n\n"
            "Crafted with ❤️ by @ViperROX.\n"
            "Have questions? Just type /help !",
            parse_mode='Markdown'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a styled help message when the command /help is issued."""
    help_text = (
        "🎬 *FlickFusion Help Guide* 🍿\n\n"
        "*For Movie Lovers:*\n"
        "• `/search [movie title]` - Find movies by title\n"
        "• `/get <title> [year]` - Get a specific movie\n"
        "• `/get` - Get a random movie\n"
        "• Type a movie title to request it (e.g., `Inception (2010)`)\n"
        "• `/start` - See the welcome message\n"
        "• `/help` - Show this help guide\n\n"
        
        "*For Admins:*\n"
        "• `/addmovie [title]` - Add a new movie\n"
        "• `/listmovies` - See all available movies\n"
        "• `/deletemovie [id]` - Remove a movie\n\n"
        
        "🎯 *Pro Tip:* For the best results when searching, include the movie's year if you know it!\n"
        "Example: `/search Inception 2010`\n\n"
        
        "Need more help? Contact @ViperROX or @Reyazsk "
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

if __name__ == '__main__':  # Fixed: Changed from 'name' to '__name__'
    main()
