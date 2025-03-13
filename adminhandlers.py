from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import ADMIN_IDS, CHANNEL_ID
from database import Movie
from utils import parse_movie_title, is_admin
from peewee import IntegrityError

# Conversation states
TITLE, DESCRIPTION, MESSAGE_ID, CONFIRM = range(4)

async def start_add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the add movie conversation."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id, ADMIN_IDS):
        await update.message.reply_text("Sorry, only admins can use this command.")
        return ConversationHandler.END
    
    # Check if we have movie details already
    args = context.args
    if args:
        movie_text = ' '.join(args)
        title, year = parse_movie_title(movie_text)
        context.user_data['movie_title'] = title
        context.user_data['movie_year'] = year
        
        await update.message.reply_text(
            f"Adding movie: *{title}*" + (f" ({year})" if year else "") + 
            "\n\nPlease provide a brief description of the movie, or send /skip to skip this step.",
            parse_mode='Markdown'
        )
        return DESCRIPTION
    
    await update.message.reply_text(
        "Please send the movie title with optional year in parentheses.\n"
        "Example: `The Matrix (1999)`",
        parse_mode='Markdown'
    )
    return TITLE

async def title_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the movie title."""
    title, year = parse_movie_title(update.message.text)
    context.user_data['movie_title'] = title
    context.user_data['movie_year'] = year
    
    await update.message.reply_text(
        f"Adding movie: *{title}*" + (f" ({year})" if year else "") + 
        "\n\nPlease provide a brief description of the movie, or send /skip to skip this step.",
        parse_mode='Markdown'
    )
    return DESCRIPTION

async def description_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the movie description."""
    if update.message.text != '/skip':
        context.user_data['movie_description'] = update.message.text
    else:
        context.user_data['movie_description'] = None
    
    await update.message.reply_text(
        "Now, please send the message ID from the channel that contains this movie.\n"
        "You can get this by forwarding the message to @getidsbot or using the 'Copy Message ID' option."
    )
    return MESSAGE_ID

async def message_id_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the message ID."""
    try:
        message_id = int(update.message.text.strip())
        context.user_data['message_id'] = message_id
        
        # Try to verify the message exists in the channel
        try:
            message = await context.bot.forward_message(
                chat_id=update.effective_chat.id,
                from_chat_id=CHANNEL_ID,
                message_id=message_id
            )
            await message.delete()  # Delete the forwarded message to keep chat clean
            
            # Show confirmation
            title = context.user_data['movie_title']
            year = context.user_data.get('movie_year')
            year_str = f" ({year})" if year else ""
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Confirm", callback_data="confirm_add"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_add")
                ]
            ]
            
            await update.message.reply_text(
                f"Ready to add *{title}*{year_str} to the database.\n\n"
                f"Message ID: `{message_id}`\n"
                f"Description: {context.user_data.get('movie_description', 'None')}\n\n"
                "Is this correct?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return CONFIRM
            
        except Exception as e:
            await update.message.reply_text(
                f"Error: Could not find message with ID {message_id} in the channel.\n"
                "Please check the ID and try again, or use /cancel to abort."
            )
            return MESSAGE_ID
            
    except ValueError:
        await update.message.reply_text(
            "Please provide a valid numeric message ID, or use /cancel to abort."
        )
        return MESSAGE_ID

async def confirm_add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and save the movie to the database."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_add":
        await query.edit_message_text("Movie addition cancelled.")
        return ConversationHandler.END
    
    # Debug information
    title = context.user_data['movie_title']
    year = context.user_data.get('movie_year')
    message_id = context.user_data['message_id']
    user_id = update.effective_user.id
    
    # Log details for debugging
    logging.info(f"Adding movie: '{title}' ({year}) with message_id={message_id}, added_by={user_id}")
    
    # Add movie to database
    try:
        movie = Movie.create(
            title=title,
            year=year,
            description=context.user_data.get('movie_description'),
            message_id=message_id,
            added_by=user_id
        )
        
        await query.edit_message_text(
            f"✅ Movie *{movie.title}*" + (f" ({movie.year})" if movie.year else "") + 
            " has been successfully added to the database!",
            parse_mode='Markdown'
        )
        
    except IntegrityError as e:
        logging.error(f"IntegrityError adding movie: {str(e)}")
        await query.edit_message_text(
            "Error: This movie or message ID already exists in the database."
        )
    except Exception as e:
        # Comprehensive error handling
        error_message = str(e)
        logging.error(f"Error adding movie: {error_message}")
        
        # Provide a user-friendly error message
        if "out of range" in error_message.lower():
            await query.edit_message_text(
                "Error: One of the values (likely the message ID) is too large for the database. "
                "Please contact the administrator to fix this issue."
            )
        else:
            await query.edit_message_text(
                f"Error adding movie: {error_message}\n"
                "Please try again or contact the administrator."
            )
    
    return ConversationHandler.END


async def cancel_add_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the add movie conversation."""
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

async def list_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all movies in the database."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id, ADMIN_IDS):
        await update.message.reply_text("Sorry, only admins can use this command.")
        return
    
    movies = Movie.select().order_by(Movie.title)
    
    if not movies:
        await update.message.reply_text("No movies in the database yet.")
        return
    
    movie_list = []
    for movie in movies:
        year_str = f" ({movie.year})" if movie.year else ""
        movie_list.append(f"• {movie.title}{year_str} - ID: {movie.id}")
    
    # Split into chunks if the list is too long
    chunks = [movie_list[i:i+50] for i in range(0, len(movie_list), 50)]
    
    for i, chunk in enumerate(chunks):
        header = "🎬 *Movie Database*" if i == 0 else f"*Movie Database (continued {i+1}/{len(chunks)})*"
        message = header + "\n\n" + "\n".join(chunk)
        await update.message.reply_text(message, parse_mode='Markdown')

async def delete_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a movie by ID."""
    user_id = update.effective_user.id
    
    if not is_admin(user_id, ADMIN_IDS):
        await update.message.reply_text("Sorry, only admins can use this command.")
        return
    
    args = context.args
    if not args or not args[0].isdigit():
        await update.message.reply_text("Please provide a valid movie ID: `/deletemovie <id>`", parse_mode='Markdown')
        return
    
    movie_id = int(args[0])
    
    try:
        movie = Movie.get_by_id(movie_id)
        title = movie.title
        year = movie.year
        movie.delete_instance()
        
        year_str = f" ({year})" if year else ""
        await update.message.reply_text(f"Movie *{title}*{year_str} has been deleted.", parse_mode='Markdown')
    
    except Movie.DoesNotExist:
        await update.message.reply_text(f"No movie found with ID {movie_id}.")

# Create the conversation handler for adding movies
add_movie_handler = ConversationHandler(
    entry_points=[CommandHandler("addmovie", start_add_movie)],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title_received)],
        DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, description_received),
            CommandHandler("skip", description_received)
        ],
        MESSAGE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, message_id_received)],
        CONFIRM: [CallbackQueryHandler(confirm_add_movie, pattern=r"^(confirm_add|cancel_add)$")]
    },
    fallbacks=[CommandHandler("cancel", cancel_add_movie)]
)

# Other admin handlers
list_movies_handler = CommandHandler("listmovies", list_movies)
delete_movie_handler = CommandHandler("deletemovie", delete_movie)
      
