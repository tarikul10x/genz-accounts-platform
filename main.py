import logging
import threading
import time
from app import app

# Configure logging to prevent bot startup issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def start_telegram_bot():
    """Start Telegram bot in background thread with error handling"""
    try:
        # Small delay to ensure Flask app is ready
        time.sleep(2)
        
        from telegram_bot import start_bot
        logger.info("Starting Telegram bot...")
        start_bot()
    except Exception as e:
        logger.error(f"Failed to start Telegram bot: {e}")
        # Don't let bot failure crash the web app

if __name__ == '__main__':
    # Start Telegram bot in a separate daemon thread
    bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    bot_thread.start()
    logger.info("Started Telegram bot thread")
    
    # Start Flask app
    logger.info("Starting Flask web application on port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
