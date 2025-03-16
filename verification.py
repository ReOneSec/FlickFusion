import secrets
import string
import requests
import logging
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import db, User
from config import ADMIN_IDS, MODIJI_API_TOKEN, BOT_USERNAME

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def generate_token(length=32):
    """Generate a secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

async def create_verification_link(user_id):
    """Create a verification link using ModiJiURL API"""
    # Check if API token is available
    if not MODIJI_API_TOKEN:
        logger.error("ModiJiURL API token not found in environment variables!")
        return None, None
        
    # Generate a unique token
    token = generate_token()
    
    # Create the destination URL with token and user_id
    # This URL will direct back to the bot with a start parameter
    destination_url = f"https://t.me/{BOT_USERNAME}?start=verify_{token}_{user_id}"
    
    # Call ModiJiURL API
    api_url = f"https://api.modijiurl.com/api?api={MODIJI_API_TOKEN}&url={destination_url}"
    
    try:
        response = requests.get(api_url)
        data = response.json()
        
        if data["status"] == "success":
            # Store the token in the database
            try:
                # Ensure database connection is open
                need_to_close = False
                if db.is_closed():
                    db.connect()
                    need_to_close = True
                
                # Update user's verification token
                try:
                    user = User.get(User.user_id == user_id)
                    user.verification_token = token
                    user.token_created_at = datetime.datetime.now()
                    user.save()
                except User.DoesNotExist:
                    # Create a new user record if it doesn't exist
                    User.create(
                        user_id=user_id,
                        first_name="User",  # Default value
                        verification_token=token,
                        token_created_at=datetime.datetime.now()
                    )
                
                logger.info(f"Created verification link for user {user_id}")
                return data["shortenedUrl"], token
                
            except Exception as e:
                logger.error(f"Database error storing verification token: {e}")
                return None, None
            finally:
                # Only close the connection if we opened it
                if need_to_close and not db.is_closed():
                    db.close()
        else:
            logger.error(f"API Error: {data}")
            return None, None
    except Exception as e:
        logger.error(f"Error creating verification link: {e}")
        return None, None

def is_user_verified(user_id):
    """Check if a user is verified"""
    try:
        # No verification needed for admins
        if user_id in ADMIN_IDS:
            return True
            
        # Ensure database connection is open
        need_to_close = False
        if db.is_closed():
            db.connect()
            need_to_close = True
        
        # Get user verification status
        try:
            user = User.get(User.user_id == user_id)
            
            # Check if verification is valid
            if not user.verified_until:
                return False
            
            return datetime.datetime.now() < user.verified_until
            
        except User.DoesNotExist:
            return False
            
    except Exception as e:
        logger.error(f"Error checking user verification: {e}")
        return False
    finally:
        # Only close the connection if we opened it
        if need_to_close and not db.is_closed():
            db.close()

def verify_token(user_id, token):
    """Mark a user as verified if the token matches"""
    try:
        # Ensure database connection is open
        need_to_close = False
        if db.is_closed():
            db.connect()
            need_to_close = True
        
        try:
            user = User.get(User.user_id == user_id)
            
            # Check if token matches
            if user.verification_token != token:
                logger.warning(f"Invalid verification token for user {user_id}")
                return False
            
            # Check if token is not too old (optional, for extra security)
            if user.token_created_at:
                token_age = datetime.datetime.now() - user.token_created_at
                if token_age.total_seconds() > 3600:  # 1 hour expiry
                    logger.warning(f"Expired verification token for user {user_id}")
                    return False
            
            # Update user's verified_until timestamp (24 hours from now)
            user.verified_until = datetime.datetime.now() + datetime.timedelta(hours=24)
            user.save()
            
            logger.info(f"User {user_id} successfully verified")
            return True
            
        except User.DoesNotExist:
            logger.warning(f"User {user_id} not found during verification")
            return False
            
    except Exception as e:
        logger.error(f"Error marking user as verified: {e}")
        return False
    finally:
        # Only close the connection if we opened it
        if need_to_close and not db.is_closed():
            db.close()

def get_verification_status(user_id):
    """Get the verification status and time remaining for a user"""
    try:
        # No verification needed for admins
        if user_id in ADMIN_IDS:
            return {
                "is_verified": True,
                "admin_override": True,
                "time_remaining": None
            }
            
        # Ensure database connection is open
        need_to_close = False
        if db.is_closed():
            db.connect()
            need_to_close = True
        
        try:
            user = User.get(User.user_id == user_id)
            
            # Check if verification is valid
            is_verified = False
            time_remaining = None
            
            if user.verified_until:
                now = datetime.datetime.now()
                if now < user.verified_until:
                    is_verified = True
                    time_remaining = user.verified_until - now
            
            return {
                "is_verified": is_verified,
                "admin_override": False,
                "time_remaining": time_remaining
            }
            
        except User.DoesNotExist:
            return {
                "is_verified": False,
                "admin_override": False,
                "time_remaining": None
            }
            
    except Exception as e:
        logger.error(f"Error getting verification status: {e}")
        return {
            "is_verified": False,
            "admin_override": False,
            "time_remaining": None,
            "error": str(e)
        }
    finally:
        # Only close the connection if we opened it
        if need_to_close and not db.is_closed():
            db.close()

async def verify_token_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the verify_token callback when user clicks the verify button"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Check if already verified
    status = get_verification_status(user_id)
    if status["is_verified"]:
        # Already verified
        if status["admin_override"]:
            await query.edit_message_text(
                "✅ *Verification not required* ✅\n\n"
                "As an admin, you don't need to verify your account.",
                parse_mode='Markdown'
            )
        else:
            # Calculate time remaining
            hours, remainder = divmod(status["time_remaining"].seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            await query.edit_message_text(
                f"✅ *Already Verified* ✅\n\n"
                f"Your verification is valid for another {hours} hours and {minutes} minutes.",
                parse_mode='Markdown'
            )
        return
    
    # Generate verification link
    verification_link, _ = await create_verification_link(user_id)
    
    if not verification_link:
        await query.edit_message_text(
            "❌ *Verification Error* ❌\n\n"
            "Failed to generate verification link. Please try again later.",
            parse_mode='Markdown'
        )
        return
    
    # Create inline keyboard with verification link
    keyboard = [
        [InlineKeyboardButton("🔐 Verify Account", url=verification_link)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔐 *Account Verification* 🔐\n\n"
        "Please click the button below to verify your account.\n\n"
        "You'll be shown an advertisement. After viewing the ad, you'll be redirected back to FlickFusion.\n"
        "This verification will be valid for 24 hours.",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /verify command"""
    user_id = update.effective_user.id
    
    # Check if already verified
    status = get_verification_status(user_id)
    if status["is_verified"]:
        # Already verified
        if status["admin_override"]:
            await update.message.reply_text(
                "✅ *Verification not required* ✅\n\n"
                "As an admin, you don't need to verify your account.",
                parse_mode='Markdown'
            )
        else:
            # Calculate time remaining
            hours, remainder = divmod(status["time_remaining"].seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            await update.message.reply_text(
                f"✅ *Already Verified* ✅\n\n"
                f"Your verification is valid for another {hours} hours and {minutes} minutes.",
                parse_mode='Markdown'
            )
        return
    
    # Generate verification link
    verification_link, _ = await create_verification_link(user_id)
    
    if not verification_link:
        await update.message.reply_text(
            "❌ *Verification Error* ❌\n\n"
            "Failed to generate verification link. Please try again later.",
            parse_mode='Markdown'
        )
        return
    
    # Create inline keyboard with verification link
    keyboard = [
        [InlineKeyboardButton("🔐 Verify Account", url=verification_link)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await update.message.reply_photo(
            photo="https://i.ibb.co/N6b3MVpj/1741892600514.jpg",
            caption=(
                "🔐 *FlickFusion Verification Required* 🔐\n\n"
                "To access all features, please click the button below to verify your account.\n\n"
                "You'll be shown an advertisement. After viewing the ad, you'll be redirected back to FlickFusion.\n"
                "This verification will be valid for 24 hours."
            ),
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Failed to send photo message: {e}")
        # Fallback to text-only message
        await update.message.reply_text(
            "🔐 *FlickFusion Verification Required* 🔐\n\n"
            "To access all features, please click the button below to verify your account.\n\n"
            "You'll be shown an advertisement. After viewing the ad, you'll be redirected back to FlickFusion.\n"
            "This verification will be valid for 24 hours.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def verification_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the user's verification status"""
    user_id = update.effective_user.id
    
    # Get verification status
    status = get_verification_status(user_id)
    
    if status["is_verified"]:
        if status["admin_override"]:
            await update.message.reply_text(
                "✅ *Verification Status: Active* ✅\n\n"
                "As an admin, you don't need to verify your account.",
                parse_mode='Markdown'
            )
        else:
            # Calculate time remaining
            hours, remainder = divmod(status["time_remaining"].seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            await update.message.reply_text(
                "✅ *Verification Status: Active* ✅\n\n"
                f"Your verification is valid for another {hours} hours and {minutes} minutes.",
                parse_mode='Markdown'
            )
    else:
        # Create verification button
        keyboard = [
            [InlineKeyboardButton("Verify Now", callback_data="verify_token")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "❌ *Verification Status: Required* ❌\n\n"
            "You need to view an ad to verify your account and use this bot.\n"
            "Please click the button below to start the verification process.",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
