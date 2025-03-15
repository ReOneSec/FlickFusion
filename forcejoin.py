import logging
from functools import wraps
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.error import TelegramError, BadRequest
from config import REQUIRED_CHANNELS, ADMIN_IDS
from database import User
import datetime

logger = logging.getLogger(__name__)

async def check_user_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if a user is a member of all required channels.
    
    Args:
        user_id: The user ID to check
        context: The context object
    
    Returns:
        bool: True if user is a member of all channels, False otherwise
    """
    # Check each required channel
    for channel in REQUIRED_CHANNELS:
        channel_id = channel['channel_id']
        try:
            # Get chat member status
            member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            
            # Check if user is not a member
            if member.status not in ['member', 'administrator', 'creator']:
                logger.info(f"User {user_id} is not a member of {channel_id}")
                return False
                
        except (TelegramError, BadRequest) as e:
            logger.error(f"Error checking membership for user {user_id} in channel {channel_id}: {e}")
            # If we can't check, assume they're not a member
            return False
    
    # If we get here, user is a member of all required channels
    logger.info(f"User {user_id} is a member of all required channels")
    return True

async def update_user_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check membership and update the database.
    
    Args:
        user_id: The user ID to check
        context: The context object
    
    Returns:
        bool: True if user is a member of all channels, False otherwise
    """
    # Check if user is a member of all channels
    is_member = await check_user_membership(user_id, context)
    
    # Update user in database
    try:
        user = User.get(User.user_id == user_id)
        user.is_member = is_member
        user.last_checked = datetime.datetime.now()
        user.save()
    except User.DoesNotExist:
        # This shouldn't happen as the user should be created before this function is called
        logger.error(f"User {user_id} not found in database during membership update")
    
    return is_member

async def force_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if user is a member of required channels and prompt to join if not.
    
    Args:
        update: The update object
        context: The context object
    
    Returns:
        bool: True if user is a member of all channels, False otherwise
    """
    user_id = update.effective_user.id
    
    # Skip check for admins
    if user_id in ADMIN_IDS:
        return True
        
    now = datetime.datetime.now()
    
    # Try to get user from database
    try:
        user = User.get(User.user_id == user_id)
        
        # If we checked recently and user is a member, return cached result
        # Only recheck every 30 minutes to reduce API calls
        if user.is_member and (now - user.last_checked).total_seconds() < 1800:
            return True
            
    except User.DoesNotExist:
        # Create new user record
        user = User.create(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name,
            is_member=False,
            last_checked=now
        )
    
    # Check membership and update database
    is_member = await update_user_membership(user_id, context)
    
    if not is_member:
        # User is not a member of all channels, create join buttons
        buttons = []
        for channel in REQUIRED_CHANNELS:
            buttons.append([InlineKeyboardButton(
                f"📢 Join {channel['channel_name']}", 
                url=channel['invite_link']
            )])
        
        # Add a "Check Again" button
        buttons.append([InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")])
        
        # Send message with join buttons
        await update.effective_message.reply_text(
            "⚠️ *You need to join our channel to use this bot!*\n\n"
            "Please join the required channel below, then click the 'I've Joined' button.",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='Markdown'
        )
        return False
    
    return True

def require_membership(func):
    """Decorator to require channel membership before executing a command."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        # Skip membership check for admins
        user_id = update.effective_user.id
        if user_id in ADMIN_IDS:
            return await func(update, context, *args, **kwargs)
        
        # Check membership
        is_member = await force_join(update, context)
        
        # Only proceed if user is a member
        if is_member:
            return await func(update, context, *args, **kwargs)
        # If not a member, force_join has already sent the join message
        return None
    
    return wrapper

async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'I've Joined' button click."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check if user has joined all channels
    is_member = await update_user_membership(user_id, context)
    
    if is_member:
        # User has joined all channels
        await query.edit_message_text(
            "✅ Thank you for joining our channel!\n\n"
            "You can now use all bot features. Type a movie name to request it, "
            "or use /help to see available commands.",
            parse_mode='Markdown'
        )
    else:
        # User has not joined all channels
        buttons = []
        for channel in REQUIRED_CHANNELS:
            buttons.append([InlineKeyboardButton(
                f"📢 Join {channel['channel_name']}", 
                url=channel['invite_link']
            )])
        
        # Add the "Check Again" button
        buttons.append([InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")])
        
        await query.edit_message_text(
            "⚠️ *You still need to join our channel!*\n\n"
            "Please join the required channel below, then click the 'I've Joined' button.",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='Markdown'
        )
