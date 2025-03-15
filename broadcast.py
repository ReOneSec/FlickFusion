import logging
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler, 
    MessageHandler, CallbackQueryHandler, filters
)
from telegram.constants import ParseMode
from config import ADMIN_IDS
from database import db, User
from forcejoin import require_membership

# Set up logging
logger = logging.getLogger(__name__)

# Define conversation states
BROADCAST_TYPE, BROADCAST_TEXT, BROADCAST_MEDIA, BROADCAST_CAPTION, BROADCAST_CONFIRM = range(5)

@require_membership
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the broadcast process (admin only)."""
    user_id = update.effective_user.id
    
    # Only allow admins to use this command
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Sorry, only admins can use this command.")
        return ConversationHandler.END
    
    # Create buttons for broadcast type
    keyboard = [
        [InlineKeyboardButton("📝 Text", callback_data="broadcast_type_text")],
        [InlineKeyboardButton("🖼️ Photo", callback_data="broadcast_type_photo")],
        [InlineKeyboardButton("🎬 Video", callback_data="broadcast_type_video")],
        [InlineKeyboardButton("📄 Document", callback_data="broadcast_type_document")],
        [InlineKeyboardButton("🔊 Audio", callback_data="broadcast_type_audio")]
    ]
    
    await update.message.reply_text(
        "📣 *Broadcast Message System*\n\n"
        "Please select the type of content you want to broadcast:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return BROADCAST_TYPE

async def broadcast_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the broadcast type selection."""
    query = update.callback_query
    await query.answer()
    
    # Extract the type from the callback data
    broadcast_type = query.data.split('_')[-1]
    context.user_data['broadcast_type'] = broadcast_type
    
    if broadcast_type == "text":
        await query.edit_message_text(
            "📝 *Text Broadcast*\n\n"
            "Please send the message you want to broadcast to all users.\n"
            "You can include text formatting with Markdown.\n\n"
            "Use /cancel to abort the broadcast.",
            parse_mode=ParseMode.MARKDOWN
        )
        return BROADCAST_TEXT
    else:
        media_type_map = {
            "photo": "photo 📸",
            "video": "video 🎬",
            "document": "document 📄",
            "audio": "audio 🔊"
        }
        media_type = media_type_map.get(broadcast_type, broadcast_type)
        
        await query.edit_message_text(
            f"📣 *{media_type.title()} Broadcast*\n\n"
            f"Please send the {media_type} you want to broadcast.\n"
            "You can include a caption with your media.\n\n"
            "Use /cancel to abort the broadcast.",
            parse_mode=ParseMode.MARKDOWN
        )
        return BROADCAST_MEDIA

async def broadcast_text_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the broadcast text message."""
    # Store the message in context
    context.user_data['broadcast_message'] = update.message.text
    
    # Create confirmation buttons
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="broadcast_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
        ]
    ]
    
    # Ask for confirmation
    await update.message.reply_text(
        "📣 *Broadcast Preview*\n\n"
        f"{update.message.text}\n\n"
        "This message will be sent to all registered users. Are you sure?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return BROADCAST_CONFIRM

async def broadcast_media_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the received media for broadcast."""
    broadcast_type = context.user_data.get('broadcast_type', '')
    
    # Store the appropriate file_id based on media type
    if broadcast_type == "photo" and update.message.photo:
        context.user_data['media_file_id'] = update.message.photo[-1].file_id
    elif broadcast_type == "video" and update.message.video:
        context.user_data['media_file_id'] = update.message.video.file_id
    elif broadcast_type == "document" and update.message.document:
        context.user_data['media_file_id'] = update.message.document.file_id
    elif broadcast_type == "audio" and update.message.audio:
        context.user_data['media_file_id'] = update.message.audio.file_id
    else:
        await update.message.reply_text(
            f"Please send a valid {broadcast_type}. Try again or use /cancel to abort."
        )
        return BROADCAST_MEDIA
    
    # Store the caption if provided
    if update.message.caption:
        context.user_data['broadcast_caption'] = update.message.caption
        return await prepare_broadcast_confirmation(update, context)
    
    # Ask for a caption if none was provided
    await update.message.reply_text(
        "Please send a caption for your media. This will be included with the broadcast.\n"
        "You can use Markdown formatting.\n\n"
        "Send /skip if you don't want to include a caption.",
        parse_mode=ParseMode.MARKDOWN
    )
    return BROADCAST_CAPTION

async def broadcast_caption_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process the caption for media broadcast."""
    if update.message.text != '/skip':
        context.user_data['broadcast_caption'] = update.message.text
    else:
        context.user_data['broadcast_caption'] = ""
    
    return await prepare_broadcast_confirmation(update, context)

async def prepare_broadcast_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prepare the confirmation message for the broadcast."""
    broadcast_type = context.user_data.get('broadcast_type', '')
    
    # Create confirmation buttons
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data="broadcast_confirm"),
            InlineKeyboardButton("❌ Cancel", callback_data="broadcast_cancel")
        ]
    ]
    
    # Send preview based on media type
    try:
        if broadcast_type == "photo":
            file_id = context.user_data.get('media_file_id', '')
            caption = context.user_data.get('broadcast_caption', '')
            
            await update.message.reply_photo(
                photo=file_id,
                caption=f"📣 *Broadcast Preview*\n\n{caption}\n\nThis content will be sent to all registered users. Are you sure?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        elif broadcast_type == "video":
            file_id = context.user_data.get('media_file_id', '')
            caption = context.user_data.get('broadcast_caption', '')
            
            await update.message.reply_video(
                video=file_id,
                caption=f"📣 *Broadcast Preview*\n\n{caption}\n\nThis content will be sent to all registered users. Are you sure?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        elif broadcast_type == "document":
            file_id = context.user_data.get('media_file_id', '')
            caption = context.user_data.get('broadcast_caption', '')
            
            await update.message.reply_document(
                document=file_id,
                caption=f"📣 *Broadcast Preview*\n\n{caption}\n\nThis content will be sent to all registered users. Are you sure?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        elif broadcast_type == "audio":
            file_id = context.user_data.get('media_file_id', '')
            caption = context.user_data.get('broadcast_caption', '')
            
            await update.message.reply_audio(
                audio=file_id,
                caption=f"📣 *Broadcast Preview*\n\n{caption}\n\nThis content will be sent to all registered users. Are you sure?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Error preparing broadcast preview: {e}")
        await update.message.reply_text(
            "Failed to generate preview. Please try again or use /cancel to abort."
        )
        return BROADCAST_MEDIA
    
    return BROADCAST_CONFIRM

async def broadcast_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the broadcast confirmation."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "broadcast_cancel":
        await query.edit_message_text("Broadcast cancelled.")
        return ConversationHandler.END
    
    await query.edit_message_text(
        "📣 *Broadcast Initiated*\n\n"
        "The content is being sent to all users. This may take some time depending on the number of users.\n"
        "You will receive a summary when the broadcast is complete.",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Start the broadcast process
    context.application.create_task(
        send_broadcast(update, context)
    )
    
    return ConversationHandler.END

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send the broadcast content to all users."""
    # Get the broadcast type and content
    broadcast_type = context.user_data.get('broadcast_type', 'text')
    
    # Ensure database connection is open
    need_to_close = False
    if db.is_closed():
        db.connect()
        need_to_close = True
    
    try:
        # Get all users
        users = User.select()
        total_users = users.count()
        
        # Counters for summary
        successful = 0
        failed = 0
        
        # Send the content to each user
        for i, user in enumerate(users, 1):
            try:
                if broadcast_type == "text":
                    message = context.user_data.get('broadcast_message', '')
                    await context.bot.send_message(
                        chat_id=user.user_id,
                        text=f"📣 *ANNOUNCEMENT FROM FLICKFUSION*\n\n{message}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    media_file_id = context.user_data.get('media_file_id', '')
                    caption = context.user_data.get('broadcast_caption', '')
                    
                    full_caption = f"📣 *ANNOUNCEMENT FROM FLICKFUSION*\n\n{caption}" if caption else "📣 *ANNOUNCEMENT FROM FLICKFUSION*"
                    
                    if broadcast_type == "photo":
                        await context.bot.send_photo(
                            chat_id=user.user_id,
                            photo=media_file_id,
                            caption=full_caption,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    elif broadcast_type == "video":
                        await context.bot.send_video(
                            chat_id=user.user_id,
                            video=media_file_id,
                            caption=full_caption,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    elif broadcast_type == "document":
                        await context.bot.send_document(
                            chat_id=user.user_id,
                            document=media_file_id,
                            caption=full_caption,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    elif broadcast_type == "audio":
                        await context.bot.send_audio(
                            chat_id=user.user_id,
                            audio=media_file_id,
                            caption=full_caption,
                            parse_mode=ParseMode.MARKDOWN
                        )
                
                successful += 1
                
                # Log progress every 20 users
                if i % 20 == 0:
                    logger.info(f"Broadcast progress: {i}/{total_users} users processed")
                    
                # Add a small delay to avoid hitting rate limits
                await asyncio.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {user.user_id}: {str(e)}")
                failed += 1
        
        # Get the user ID for sending the summary
        user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
        
        # Send a summary to the admin
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "📣 *Broadcast Complete*\n\n"
                f"✅ Successfully sent: {successful}\n"
                f"❌ Failed: {failed}\n"
                f"📊 Total users: {total_users}"
            ),
            parse_mode=ParseMode.MARKDOWN
        )
        
        logger.info(f"Broadcast completed: {successful} successful, {failed} failed, {total_users} total")
        
    except Exception as e:
        logger.error(f"Error during broadcast: {str(e)}")
        
        # Get the user ID for sending the error message
        user_id = update.effective_user.id if update.effective_user else update.callback_query.from_user.id
        
        # Notify the admin about the error
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Error during broadcast: {str(e)}",
            parse_mode=ParseMode.MARKDOWN
        )
        
    finally:
        # Only close the connection if we opened it
        if need_to_close and not db.is_closed():
            db.close()

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the broadcast process."""
    await update.message.reply_text("Broadcast cancelled.")
    return ConversationHandler.END

# Create the broadcast conversation handler
broadcast_handler = ConversationHandler(
    entry_points=[CommandHandler("broadcast", broadcast_command)],
    states={
        BROADCAST_TYPE: [CallbackQueryHandler(broadcast_type_callback, pattern=r'^broadcast_type_')],
        BROADCAST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_text_received)],
        BROADCAST_MEDIA: [
            MessageHandler(filters.Photo, broadcast_media_received),
            MessageHandler(filters.Video, broadcast_media_received),
            MessageHandler(filters.Document, broadcast_media_received),
            MessageHandler(filters.Audio, broadcast_media_received)
        ],
        BROADCAST_CAPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_caption_received),
            CommandHandler("skip", broadcast_caption_received)
        ],
        BROADCAST_CONFIRM: [CallbackQueryHandler(broadcast_confirm_callback, pattern=r'^broadcast_')]
    },
    fallbacks=[CommandHandler("cancel", cancel_broadcast)],
    per_message=True
)
