import os
import time
import tempfile
import subprocess
import shutil
import requests  # Import the requests library
from dotenv import dotenv_values
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load Telegram token from .env file
config = dotenv_values(".env")

# Check if TELEGRAM_TOKEN is available in the .env file
if "TELEGRAM_TOKEN" not in config:
    raise ValueError("TELEGRAM_TOKEN not found in .env file")

TELEGRAM_TOKEN = config["TELEGRAM_TOKEN"]

# Function to search for songs on your VLESS network
def search_for_songs(query):
    # Replace with your logic to search for songs on your VLESS network
    # You may make an HTTP request to your network's API to get song URLs
    # For this example, we simulate a search and return sample URLs.
    sample_song_urls = [
        "https://example.com/song1.mp3",
        "https://example.com/song2.mp3",
    ]
    return sample_song_urls

# Function to download a song using spotdl through a VLESS proxy
def download_song_through_proxy(url, temp_dir):
    os.makedirs(temp_dir, exist_ok=True)
    os.chdir(temp_dir)

    try:
        # Use curl with a VLESS proxy to download the song from the provided URL
        proxy_uri = "vless://6d377d38-328c-41e2-b76a-62498a647065@n8n.io:8880?security=&fp=random&type=ws&path=/?ed%3D2048&host=vip.vip-7e7.workers.dev&encryption=none#vip.vip-7e7.workers.dev-HTTP"
        subprocess.run(["curl", "-x", proxy_uri, "-o", "song.mp3", url])
    except Exception as e:
        print(f"Error downloading the song through the VLESS proxy: {e}")

    os.chdir("..")

# Function to convert audio files to MP3 with 320kbps using FFmpeg
def convert_to_mp3(temp_dir):
    os.chdir(temp_dir)
    for file in os.listdir("."):
        if file.endswith(".opus"):
            output_file = file.replace(".opus", ".mp3")
            subprocess.run(["ffmpeg", "-i", file, "-b:a", "320k", output_file])
            os.remove(file)
    os.chdir("..")

# Function to send a song to Telegram
def send_song_to_telegram(update, context, temp_dir):
    chat_id = update.effective_chat.id
    temp_files = [file for file in os.listdir(temp_dir) if file.endswith(".mp3")]

    if not temp_files:
        context.bot.send_message(chat_id=chat_id, text="❌ Unable to find the requested song.")
        return

    for file in temp_files:
        try:
            with open(os.path.join(temp_dir, file), "rb") as audio_file:
                context.bot.send_audio(chat_id=chat_id, audio=audio_file, timeout=18000)
        except Exception as e:
            print(f"Error sending audio: {e}")

# Function to handle the /start command
def start(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    context.bot.send_message(chat_id=chat_id, text="🎵 Welcome to the Song Downloader Bot! 🎵")

# Function to handle user messages and download songs through a VLESS proxy
def get_single_song(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    query = update.effective_message.text.strip()
    
    # Search for songs based on the user's query
    song_urls = search_for_songs(query)

    if not song_urls:
        context.bot.send_message(chat_id=chat_id, text="❌ No songs found for the given query.")
        return

    temp_dir = tempfile.mkdtemp()
    
    # Download and send each song found
    for url in song_urls:
        download_song_through_proxy(url, temp_dir)
        convert_to_mp3(temp_dir)
        send_song_to_telegram(update, context, temp_dir)
    
    # Clean up the temporary directory
    shutil.rmtree(temp_dir)

def main():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Handlers
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    song_handler = MessageHandler(Filters.text & (~Filters.command), get_single_song)
    dispatcher.add_handler(song_handler)

    # Start the bot
    updater.start_polling(poll_interval=0.3)
    updater.idle()

if __name__ == "__main__":
    main()
