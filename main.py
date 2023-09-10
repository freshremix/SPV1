import logging
import os
import time
import subprocess
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
os.system(f'spotdl --download-ffmpeg')

# Update yt-dlp
try:
    subprocess.run(["yt-dlp", "-U"], check=True)
    logging.info('yt-dlp updated successfully.')
except subprocess.CalledProcessError as e:
    logging.error(f'Failed to update yt-dlp: {e}')

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration settings
class Config:
    def __init__(self):
        self.token = "YOUR_TELEGRAM_BOT_TOKEN"
        self.auth_enabled = False  # Set to True if authentication is required
        self.auth_password = "your_password"  # Set the desired authentication password
        self.auth_users = []  # List of authorized user chat IDs (e.g., [123456789, 987654321])

config = Config()

# Authentication decorator
def authenticate(func):
    def wrapper(update: Update, context: CallbackContext):
        chat_id = update.effective_chat.id
        if config.auth_enabled:
            user_id = update.effective_user.id
            if user_id not in config.auth_users:
                context.bot.send_message(chat_id=chat_id, text="⚠️ Authentication required.")
                return
        return func(update, context)
    return wrapper

# Bot commands
def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text="🎵 Welcome to the Song Downloader Bot! 🎵")

# Download and send a single song
@authenticate
def get_single_song(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    message_id = update.effective_message.message_id
    username = update.effective_chat.username
    logger.info(f'Starting song download. Chat ID: {chat_id}, Message ID: {message_id}, Username: {username}')

    url = update.effective_message.text.strip()

    # Use the /tmp directory for temporary file storage
    download_dir = f"/tmp/.temp{message_id}{chat_id}"
    os.makedirs(download_dir, exist_ok=True)
    os.chdir(download_dir)

    logger.info('Downloading song...')
    context.bot.send_message(chat_id=chat_id, text="🔍 Downloading")

    if url.startswith(("http://", "https://")):
        os.system(f'spotdl download "{url}" --audio slider-kz --threads 8 --format mp3 --bitrate 320k --lyrics genius')

        logger.info('Sending song to user...')
        sent = 0
        files = [file for file in os.listdir(".") if file.endswith(".mp3")]
        if files:
            for file in files:
                try:
                    with open(file, 'rb') as audio_file:
                        context.bot.send_audio(chat_id=chat_id, audio=audio_file, timeout=18000)
                    sent += 1
                    time.sleep(0.3)  # Add a delay of 0.3 seconds between sending each audio file
                except Exception as e:
                    logger.error(f"Error sending audio: {e}")
            logger.info(f'Sent {sent} audio file(s) to user.')
        else:
            context.bot.send_message(chat_id=chat_id, text="❌ Unable to find the requested song.")
            logger.warning('No audio file found after download.')
    else:
        context.bot.send_message(chat_id=chat_id, text="❌ Invalid URL. Please provide a valid song URL.")
        logger.warning('Invalid URL provided.')

    # Change the current working directory back to its original location
    os.chdir('/path/to/original/directory')

# Main function to run the bot
def main():
    updater = Updater(token=config.token, use_context=True)
    dispatcher = updater.dispatcher

    # Register handlers
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    song_handler = MessageHandler(Filters.text & (~Filters.command), get_single_song)
    dispatcher.add_handler(song_handler)

    # Start the bot
    updater.start_polling(poll_interval=0.3)
    logger.info('Bot started')
    updater.idle()

if __name__ == "__main__":
    main()
