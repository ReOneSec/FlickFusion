import logging
import datetime
import asyncio
import time
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes, CallbackQueryHandler
from config import BOT_TOKEN, ADMIN_IDS
from database import db, initialize_db, User
from adminhandlers import add_movie_handler, list_movies_handler, delete_movie_handler
from userhandlers import handle_movie_request, search_movie, get_movie, get_movie_callback
from forcejoin import require_membership, check_membership_callback, membership_status
from broadcast import broadcast_handler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Add this global variable for uptime tracking
START_TIME = time.time()

@require_membership
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome message with image when the command /start is issued."""
    chat_id = update.effective_chat.id
    
    # Send welcome image with caption
    try:
        await context.bot.send_photo(
            chat_id=chat_id,
            photo="https://i.ibb.co/N6b3MVpj/1741892600514.jpg",
            caption=(
                "*🎬 Welcome to FlickFusion, Movie Lover! 🍿*\n\n"
                "Hey there! I'm *FlickFusion*, your go-to bot for instant movie magic. 🪄 "
                "Need a film? Just drop your request in the group, in this Format \"/search [Movie Name]\".\n\n"
                "*Let's dive into the world of cinema. Sit back, grab popcorn, and enjoy! 🎥*\n\n"
                "*Crafted with ❤️ by @ViperROX.*\n"
                "Have questions? Just type /help or check your channel membership with /status!"
            ),
            parse_mode='Markdown'
        )
        logger.info(f"Sent welcome message and image to chat ID: {chat_id}")
    except Exception as e:
        # Fallback to text-only message if image fails
        logger.error(f"Failed to send welcome image: {str(e)}")
        await update.message.reply_text(
            "*🎬 Welcome to FlickFusion, Movie Lover! 🍿*\n\n"
            "Hey there! I'm *FlickFusion*, your go-to bot for instant movie magic. 🪄 "
            "Need a film? Just drop your request in the group, in this Format \"/search [Movie Name]\".\n\n"
            "*Let's dive into the world of cinema. Sit back, grab popcorn, and enjoy! 🎥*\n\n"
            "*Crafted with ❤️ by @ViperROX.*\n"
            "Have questions? Just type /help or check your channel membership with /status!",
            parse_mode='Markdown'
        )

@require_membership
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a styled help message when the command /help is issued."""
    help_text = (
        "🎬 *FlickFusion Help Guide* 🍿\n\n"
        "*For Movie Lovers:*\n"
        "• `/start` - See the welcome message\n"
        "• `/search [movie title]` - Find movies by title\n"
        "• `/get <title> [year]` - Get a specific movie\n"
        "• `/get` - Get a random movie\n"
        "• `/stat` - View bot statistics\n"
        "• `/status` - Check your channel membership status\n"
        "• Type a movie title to request it (e.g., `Inception (2010)`)\n"
        "• `/help` - Show this help guide\n\n"
        
        "*For Admins:*\n"
        "• `/addmovie [title]` - Add a new movie\n"
        "• `/listmovies` - See all available movies\n"
        "• `/deletemovie [id]` - Remove a movie\n"
        "• `/checkmemberships` - Manually check user memberships\n"
        "• `/stat` - View detailed bot statistics\n\n"
        "• `/broadcast` - Send a message to all users\n\n"
        
        "🎯 *Pro Tip:* For the best results when searching, include the movie's year if you know it!\n"
        "Example: `/search Inception 2010`\n\n"
        
        "Need more help?\nContact @ViperROX or @Reyazsk "
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def check_all_memberships(context: ContextTypes.DEFAULT_TYPE):
    """Periodic job to check membership status of all users."""
    from forcejoin import check_user_membership
    from database import db, User
    
    logger.info("Running periodic membership check")
    
    # Get all users who were last checked more than 24 hours ago
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    
    # Check if connection is already open, and if not, open it
    need_to_close = False
    if db.is_closed():
        db.connect()
        need_to_close = True
    
    try:
        users = User.select().where(User.last_checked < yesterday)
        
        count = 0
        for user in users:
            try:
                # Skip admins
                if user.user_id in ADMIN_IDS:
                    continue
                    
                # Check membership
                results = await check_user_membership(user.user_id, context)
                is_member = results['is_member_of_all']
                
                # Update user status
                user.is_member = is_member
                user.last_checked = datetime.datetime.now()
                user.save()
                
                count += 1
                if count % 10 == 0:  # Log progress every 10 users
                    logger.info(f"Checked {count} users so far")
                
            except Exception as e:
                logger.error(f"Error checking user {user.user_id}: {e}")
        
        logger.info(f"Completed periodic membership check for {count} users")
    
    except Exception as e:
        logger.error(f"Error during periodic membership check: {e}")
    finally:
        # Only close the connection if we opened it
        if need_to_close and not db.is_closed():
            db.close()

async def check_memberships_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manual command to check all memberships (admin only)."""
    user_id = update.effective_user.id
    
    # Only allow admins to run this command
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Sorry, only admins can use this command.")
        return
    
    await update.message.reply_text("Starting membership check for all users. This may take some time...")
    
    # Run the check
    await check_all_memberships(context)
    
    await update.message.reply_text("Membership check completed!")

@require_membership
async def stat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display bot statistics with different views for admins and regular users."""
    from database import db, Movie, RequestLog, User
    from peewee import fn
    import datetime
    
    # Check if this is an admin request (for detailed stats)
    user_id = update.effective_user.id
    is_admin = user_id in ADMIN_IDS
    
    try:
        # Ensure database connection is open
        need_to_close = False
        if db.is_closed():
            db.connect()
            need_to_close = True
            
        # Basic statistics everyone can see
        total_movies = Movie.select().count()
        total_requests = RequestLog.select().count()
        total_users = User.select().count()
        
        # Create statistics message
        stats_message = [
            "📊 *FlickFusion Bot Statistics* 📊\n",
            f"🎬 *Total Movies:* {total_movies}",
            f"🔍 *Total Requests:* {total_requests}",
            f"👥 *Registered Users:* {total_users}"
        ]
        
        # Add more detailed statistics for admins
        if is_admin:
            # Calculate active users in the last 30 days
            thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
            active_users = (RequestLog
                          .select(RequestLog.user_id)
                          .distinct()
                          .where(RequestLog.request_time > thirty_days_ago)
                          .count())
            
            # Get the top 5 most requested movies
            top_movies = (Movie
                          .select(Movie, fn.COUNT(RequestLog.id).alias('request_count'))
                          .join(RequestLog)
                          .group_by(Movie.id)
                          .order_by(fn.COUNT(RequestLog.id).desc())
                          .limit(5))
            
            # Get user membership statistics
            member_users = User.select().where(User.is_member == True).count()
            non_member_users = total_users - member_users
            
            # Add admin statistics to the message
            stats_message.append("\n*Admin Statistics:*")
            stats_message.append(f"👤 *Active Users (30 days):* {active_users}")
            stats_message.append(f"✅ *Users in Channels:* {member_users}")
            stats_message.append(f"❌ *Users Not in Channels:* {non_member_users}")
            
            # Add top movies section
            if top_movies.count() > 0:
                stats_message.append("\n*Top Requested Movies:*")
                for i, movie in enumerate(top_movies, 1):
                    year_str = f" ({movie.year})" if movie.year else ""
                    stats_message.append(f"{i}. *{movie.title}*{year_str} - {movie.request_count} requests")
            
            # Add system statistics
            stats_message.append("\n*System Statistics:*")
            stats_message.append(f"⏱️ *Uptime:* {get_uptime()}")
        
        # Send the statistics message
        await update.message.reply_text(
            "\n".join(stats_message),
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error generating statistics: {str(e)}")
        await update.message.reply_text(
            "Sorry, an error occurred while generating statistics. Please try again later."
        )
    finally:
        # Only close the connection if we opened it
        if need_to_close and not db.is_closed():
            db.close()

# Helper function for uptime calculation
def get_uptime():
    """Get the bot's uptime in a human-readable format."""
    uptime_seconds = int(time.time() - START_TIME)
    
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    
    return " ".join(parts)

# Error handler for the application
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors in the dispatcher."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # Send a message to the user if it's a user-initiated update
    if update and hasattr(update, 'effective_chat') and update.effective_chat:
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, an error occurred while processing your request. Please try again later."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {str(e)}")



# Async function for post_init
async def initialize_job_queue(app):
    """Async function for post_init that returns None but satisfies the awaitable requirement."""
    return None

def main():
    """Start the bot."""
    # Initialize database
    initialize_db()
    
    try:
        # Create the Application with explicit JobQueue initialization using an async function
        application = Application.builder().token(BOT_TOKEN).post_init(initialize_job_queue).build()
        
        # Register the error handler
        application.add_error_handler(error_handler)
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("search", search_movie))
        application.add_handler(CommandHandler("get", get_movie))
        application.add_handler(CommandHandler("status", membership_status))
        application.add_handler(CommandHandler("stat", stat_command))
        application.add_handler(CommandHandler("checkmemberships", check_memberships_command))
        
        # Add the broadcast handler
        application.add_handler(broadcast_handler)
        
        # Add callback handlers
        application.add_handler(CallbackQueryHandler(get_movie_callback, pattern=r'^get_movie_'))
        application.add_handler(CallbackQueryHandler(check_membership_callback, pattern=r'^check_membership$'))
        
        # Admin handlers
        application.add_handler(add_movie_handler)
        application.add_handler(list_movies_handler)
        application.add_handler(delete_movie_handler)
        
        # Set up periodic membership check with proper error handling
        if hasattr(application, 'job_queue') and application.job_queue is not None:
            application.job_queue.run_repeating(check_all_memberships, interval=86400, first=10)
            logger.info("Scheduled periodic membership checks every 24 hours")
        else:
            logger.warning("JobQueue not available. Periodic membership checks will not run automatically.")
            logger.info("Added /checkmemberships command for manual membership verification")
        
        # User movie request handler - should be last to catch all messages
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, handle_movie_request
        ))
        
        # Start the Bot
        logger.info("Starting FlickFusion bot")
        application.run_polling()
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        # Close the database connection when done
        if not db.is_closed():
            db.close()

if __name__ == '__main__':
    main()
