import logging
from functools import wraps
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.error import TelegramError, BadRequest
from config import REQUIRED_CHANNELS, ADMIN_IDS
from database import User, db
import datetime
from verification import is_user_verified, create_verification_link


logger = logging.getLogger(__name__)

async def check_user_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> dict:
    """
    Check if a user is a member of all required channels.
    
    Args:
        user_id: The user ID to check
        context: The context object
    
    Returns:
        dict: Results with overall status and per-channel status
    """
    results = {
        'is_member_of_all': True,
        'channels': {}
    }
    
    # Check each required channel
    for channel in REQUIRED_CHANNELS:
        channel_id = channel['channel_id']
        channel_name = channel['channel_name']
        
        try:
            # Get chat member status
            member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            
            # Check if user is a member
            is_member = member.status in ['member', 'administrator', 'creator']
            results['channels'][channel_id] = {
                'name': channel_name,
                'is_member': is_member,
                'status': member.status
            }
            
            # Update overall status
            if not is_member:
                results['is_member_of_all'] = False
                logger.info(f"User {user_id} is not a member of {channel_name} (ID: {channel_id})")
                
        except (TelegramError, BadRequest) as e:
            logger.error(f"Error checking membership for user {user_id} in channel {channel_name}: {e}")
            # If we can't check, assume they're not a member
            results['channels'][channel_id] = {
                'name': channel_name,
                'is_member': False,
                'status': 'error',
                'error': str(e)
            }
            results['is_member_of_all'] = False
    
    if results['is_member_of_all']:
        logger.info(f"User {user_id} is a member of all {len(REQUIRED_CHANNELS)} required channels")
    
    return results

async def update_user_membership(user_id: int, username: str, first_name: str, last_name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check membership and update the database.
    
    Args:
        user_id: The user ID to check
        username: The username
        first_name: The first name
        last_name: The last name
        context: The context object
    
    Returns:
        bool: True if user is a member of all channels, False otherwise
    """
    # Check if user is a member of all channels
    results = await check_user_membership(user_id, context)
    is_member = results['is_member_of_all']
    
    # Ensure database connection is open
    if db.is_closed():
        db.connect()
    
    try:
        # Update user in database
        try:
            user = User.get(User.user_id == user_id)
            user.is_member = is_member
            user.last_checked = datetime.datetime.now()
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            user.save()
        except User.DoesNotExist:
            # Create new user record
            User.create(
                user_id=user_id,
                username=username,
                first_name=first_name or "User",
                last_name=last_name,
                is_member=is_member,
                last_checked=datetime.datetime.now()
            )
    finally:
        # Close the database connection
        if not db.is_closed():
            db.close()
    
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
    
    # Ensure database connection is open
    if db.is_closed():
        db.connect()
    
    try:
        # Try to get user from database
        try:
            user = User.get(User.user_id == user_id)
            
            # If we checked recently and user is a member, return cached result
            # Only recheck every 10 minutes to reduce API calls
            if user.is_member and (now - user.last_checked).total_seconds() < 600:
                return True
                
        except User.DoesNotExist:
            # User will be created in update_user_membership
            pass
    finally:
        # Close the database connection
        if not db.is_closed():
            db.close()
    
    # Check membership and update database
    is_member = await update_user_membership(
        user_id=user_id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name,
        context=context
    )
    
    if not is_member:
        # Get detailed membership status
        results = await check_user_membership(user_id, context)
        
        # User is not a member of all channels, create join buttons
        buttons = []
        
        # Add a button for each channel the user needs to join
        for channel in REQUIRED_CHANNELS:
            channel_id = channel['channel_id']
            channel_info = results['channels'].get(channel_id, {})
            
            # Only show button if user is not a member of this channel
            if not channel_info.get('is_member', False):
                buttons.append([InlineKeyboardButton(
                    f"📢 Join {channel['channel_name']}", 
                    url=channel['invite_link']
                )])
        
        # Add a "Check Again" button
        buttons.append([InlineKeyboardButton("✅ I've Joined All Channels", callback_data="check_membership")])
        
        # Create message text
        channel_count = len([c for c in results['channels'].values() if not c.get('is_member', False)])
        channel_text = "channels" if channel_count > 1 else "channel"
        
        # Create a branded message with FlickFusion style
        try:
            await update.effective_message.reply_photo(
                photo="https://i.ibb.co/N6b3MVpj/1741892600514.jpg",
                caption=(
                    f"🎬 *FlickFusion Requires Channel Membership* 🍿\n\n"
                    f"To access all the amazing movies and features, you need to join our {channel_text} first!\n\n"
                    f"Please join the required {channel_text} below, then click the 'I've Joined All Channels' button."
                ),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send photo message: {e}")
            # Fallback to text-only message
            await update.effective_message.reply_text(
                f"🎬 *FlickFusion Requires Channel Membership* 🍿\n\n"
                f"To access all the amazing movies and features, you need to join our {channel_text} first!\n\n"
                f"Please join the required {channel_text} below, then click the 'I've Joined All Channels' button.",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode='Markdown'
            )
        return False
    
    return True

def require_membership(func):
    """Decorator to require channel membership and verification before executing a command."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Skip membership and verification check for admins
        if user_id in ADMIN_IDS:
            return await func(update, context, *args, **kwargs)
        
        # 1. Check channel membership
        is_member = await force_join(update, context)
        if not is_member:
            # force_join has already sent the join message
            return None
        
        # 2. Check verification status
        if not is_user_verified(user_id):
            # User needs to verify
            verification_link, _ = await create_verification_link(user_id)
            if not verification_link:
                await update.effective_message.reply_text(
                    "❌ *Verification Error* ❌\n\n"
                    "Failed to generate verification link. Please try again later.",
                    parse_mode='Markdown'
                )
                return None

            keyboard = [
                [InlineKeyboardButton("🔐 Verify Account (View Ad)", url=verification_link)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            try:
                await update.effective_message.reply_photo(
                    photo="https://i.ibb.co/N6b3MVpj/1741892600514.jpg",
                    caption=(
                        "🔐 *FlickFusion Verification Required* 🔐\n\n"
                        "To access all features, please click the button below to verify your account.\n\n"
                        "You'll be shown an advertisement. After viewing the ad, you'll be redirected back to FlickFusion.\n"
                        "This verification will be valid for 24 hours."
                    ),
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.error(f"Failed to send photo message: {e}")
                # Fallback to text-only message
                await update.effective_message.reply_text(
                    "🔐 *FlickFusion Verification Required* 🔐\n\n"
                    "To access all features, please click the button below to verify your account.\n\n"
                    "You'll be shown an advertisement. After viewing the ad, you'll be redirected back to FlickFusion.\n"
                    "This verification will be valid for 24 hours.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            return None
            
        # If both membership and verification checks pass, execute the function
        return await func(update, context, *args, **kwargs)
    
    return wrapper


async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'I've Joined All Channels' button click."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check if user has joined all channels
    is_member = await update_user_membership(
        user_id=user_id,
        username=update.effective_user.username,
        first_name=update.effective_user.first_name,
        last_name=update.effective_user.last_name,
        context=context
    )
    
    if is_member:
        # User has joined all channels
        try:
            # Try to edit the caption if it's a photo message
            await query.edit_message_caption(
                caption="*🎬 Welcome to FlickFusion, Movie Lover! 🍿*\n\n"
                "Hey there! I'm *FlickFusion*, your go-to bot for instant movie magic. 🪄 "
                "Need a film? Just drop your request in the group, in this Format \"/search [Movie Name]\".\n\n"
                "*Let's dive into the world of cinema. Sit back, grab popcorn, and enjoy! 🎥*\n\n"
                "*Crafted with ❤️ by @ViperROX.*\n"
                "Have questions? Just type /help or check your channel membership with /status!",
                parse_mode='Markdown'
            )
        except Exception:
            # Fallback to editing text message
            await query.edit_message_text(
                "*🎬 Welcome to FlickFusion, Movie Lover! 🍿*\n\n"
                "Hey there! I'm *FlickFusion*, your go-to bot for instant movie magic. 🪄 "
                "Need a film? Just drop your request in the group, in this Format \"/search [Movie Name]\".\n\n"
                "*Let's dive into the world of cinema. Sit back, grab popcorn, and enjoy! 🎥*\n\n"
                "*Crafted with ❤️ by @ViperROX.*\n"
                "Have questions? Just type /help or check your channel membership with /status!",
                parse_mode='Markdown'
            )
    else:
        # Get detailed membership status
        results = await check_user_membership(user_id, context)
        
        # User has not joined all channels
        buttons = []
        
        # Add a button for each channel the user needs to join
        for channel in REQUIRED_CHANNELS:
            channel_id = channel['channel_id']
            channel_info = results['channels'].get(channel_id, {})
            
            # Only show button if user is not a member of this channel
            if not channel_info.get('is_member', False):
                buttons.append([InlineKeyboardButton(
                    f"📢 Join {channel['channel_name']}", 
                    url=channel['invite_link']
                )])
        
        # Add the "Check Again" button
        buttons.append([InlineKeyboardButton("✅ I've Joined All Channels", callback_data="check_membership")])
        
        # Create message text with specific feedback
        missing_channels = [
            channel['name'] 
            for channel_id, channel in results['channels'].items() 
            if not channel.get('is_member', False)
        ]
        
        missing_text = ", ".join(missing_channels)
        
        try:
            # Try to edit the caption if it's a photo message
            await query.edit_message_caption(
                caption="⚠️ *You still need to join the following channels:*\n"
                f"• {missing_text}\n\n"
                "Please join all required channels, then click the 'I've Joined All Channels' button to access FlickFusion.",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode='Markdown'
            )
        except Exception:
            # Fallback to editing text message
            await query.edit_message_text(
                "⚠️ *You still need to join the following channels:*\n"
                f"• {missing_text}\n\n"
                "Please join all required channels, then click the 'I've Joined All Channels' button to access FlickFusion.",
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode='Markdown'
            )

async def membership_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the user's membership status for all required channels."""
    user_id = update.effective_user.id
    
    # Get membership status for all channels
    results = await check_user_membership(user_id, context)
    
    # Create a status message
    status_lines = ["🎬 *FlickFusion Channel Membership Status*\n"]
    
    for channel in REQUIRED_CHANNELS:
        channel_id = channel['channel_id']
        channel_info = results['channels'].get(channel_id, {})
        
        # Add status emoji
        if channel_info.get('is_member', False):
            status_emoji = "✅"
        else:
            status_emoji = "❌"
            
        status_lines.append(f"{status_emoji} {channel['channel_name']}")
    
    # Add overall status
    status_lines.append("\n*Overall Status:*")
    if results['is_member_of_all']:
        status_lines.append("✅ You have joined all required channels!")
    else:
        status_lines.append("❌ You need to join all channels to use FlickFusion.")
        
        # Add join buttons for channels the user hasn't joined
        buttons = []
        for channel in REQUIRED_CHANNELS:
            channel_id = channel['channel_id']
            channel_info = results['channels'].get(channel_id, {})
            
            if not channel_info.get('is_member', False):
                buttons.append([InlineKeyboardButton(
                    f"📢 Join {channel['channel_name']}", 
                    url=channel['invite_link']
                )])
        
        # Add check button
        buttons.append([InlineKeyboardButton("✅ I've Joined All Channels", callback_data="check_membership")])
        
        # Send message with buttons
        await update.message.reply_text(
            "\n".join(status_lines),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode='Markdown'
        )
        return
    
    # If they've joined all channels, just send the status message
    await update.message.reply_text(
        "\n".join(status_lines),
        parse_mode='Markdown'
    )
