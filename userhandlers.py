import logging
from telegram import Update
from telegram.ext import ContextTypes
from database import Movie, RequestLog
from utils import parse_movie_title, is_authorized_group, format_movie_info
from config import CHANNEL_ID, AUTH_GROUPS
from peewee import DoesNotExist

async def handle_movie_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user movie requests by title."""
    # Check if message is from an authorized group
    chat_id = update.effective_chat.id
    if not is_authorized_group(chat_id, AUTH_GROUPS):
        return
    
    # Parse the movie title and year
    title, year = parse_movie_title(update.message.text)
    
    try:
        # Ensure database connection is open
        if db.is_closed():
            db.connect()
            
        # Try to find the movie in the database
        query = Movie.select()
        
        # If we have a year, use it for more precise matching
        if year:
            movie = query.where(
                (Movie.title.contains(title)) & (Movie.year == year)
            ).get()
        else:
            # Otherwise just search by title
            movie = query.where(Movie.title.contains(title)).get()
        
        # Forward the movie from the channel
        await context.bot.forward_message(
            chat_id=update.effective_chat.id,
            from_chat_id=CHANNEL_ID,
            message_id=movie.message_id
        )
        
        # Log the request
        RequestLog.create(
            user_id=update.effective_user.id,
            movie_id=movie.id,
            group_id=update.effective_chat.id
        )
        
    except DoesNotExist:
        # If the movie wasn't found, let the user know
        await update.message.reply_text(
            f"Sorry, I couldn't find the movie '{title}'" + (f" ({year})" if year else "") + 
            " in my database. Please check the title or try another movie."
        )
    finally:
        # Close the database connection to prevent connection leaks
        if not db.is_closed():
            db.close()

async def search_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for movies in the database."""
    if not context.args:
        await update.message.reply_text(
            "Please provide a search term: `/search movie title`",
            parse_mode='Markdown'
        )
        return
    
    search_term = ' '.join(context.args)
    
    # Search for movies that match the search term
    movies = Movie.select().where(Movie.title.contains(search_term)).limit(10)
    
    if not movies:
        await update.message.reply_text(f"No movies found matching '{search_term}'.")
        return
    
    # Create a formatted list of found movies
    results = [f"🎬 *Search Results for '{search_term}'*\n"]
    
    for movie in movies:
        year_str = f" ({movie.year})" if movie.year else ""
        results.append(f"• *{movie.title}*{year_str}")
    
    await update.message.reply_text("\n".join(results), parse_mode='Markdown')
