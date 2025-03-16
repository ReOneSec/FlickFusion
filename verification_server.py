from flask import Flask, request, redirect
import requests
import logging
from verification import mark_user_verified
from config import BOT_TOKEN, BOT_USERNAME

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/verify')
def verify():
    """Handle verification requests"""
    user_id = request.args.get('user_id')
    token = request.args.get('token')
    
    if not user_id or not token:
        logger.warning(f"Invalid verification request: missing user_id or token")
        return "Invalid verification link", 400
    
    try:
        user_id = int(user_id)
        success = mark_user_verified(user_id, token)
        
        if success:
            # Optionally send a message to the user via Telegram Bot API
            try:
                requests.get(
                    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                    params={
                        "chat_id": user_id,
                        "text": "✅ Verification successful! You can now use FlickFusion for the next 24 hours.",
                        "parse_mode": "Markdown"
                    }
                )
            except Exception as e:
                logger.error(f"Error sending Telegram message: {e}")
            
            return """
            <html>
                <head>
                    <title>FlickFusion Verification Successful</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            text-align: center;
                            margin-top: 50px;
                            background-color: #f5f5f5;
                        }
                        .container {
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                            background-color: white;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }
                        h1 {
                            color: #4CAF50;
                        }
                        .button {
                            display: inline-block;
                            background-color: #4CAF50;
                            color: white;
                            padding: 10px 20px;
                            text-decoration: none;
                            border-radius: 5px;
                            margin-top: 20px;
                            font-weight: bold;
                        }
                        .movie-icon {
                            font-size: 48px;
                            margin-bottom: 20px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="movie-icon">🎬</div>
                        <h1>Verification Successful! ✅</h1>
                        <p>Your FlickFusion account has been successfully verified for the next 24 hours.</p>
                        <p>You can now return to the Telegram bot and enjoy all features.</p>
                        <a class="button" href="https://t.me/""" + BOT_USERNAME + """">Return to FlickFusion</a>
                    </div>
                </body>
            </html>
            """
        else:
            logger.warning(f"Verification failed for user {user_id}")
            return """
            <html>
                <head>
                    <title>FlickFusion Verification Failed</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            text-align: center;
                            margin-top: 50px;
                            background-color: #f5f5f5;
                        }
                        .container {
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                            background-color: white;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }
                        h1 {
                            color: #f44336;
                        }
                        .button {
                            display: inline-block;
                            background-color: #2196F3;
                            color: white;
                            padding: 10px 20px;
                            text-decoration: none;
                            border-radius: 5px;
                            margin-top: 20px;
                            font-weight: bold;
                        }
                        .movie-icon {
                            font-size: 48px;
                            margin-bottom: 20px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="movie-icon">🎬</div>
                        <h1>Verification Failed ❌</h1>
                        <p>Invalid or expired verification token.</p>
                        <p>Please return to FlickFusion and request a new verification link.</p>
                        <a class="button" href="https://t.me/""" + BOT_USERNAME + """">Return to FlickFusion</a>
                    </div>
                </body>
            </html>
            """, 400
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return "An error occurred during verification.", 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
