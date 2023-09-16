import os
import time
import tempfile
import subprocess
import shutil
from dotenv import dotenv_values
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load Telegram token from .env file
config = dotenv_values(".env")

# Check if TELEGRAM_TOKEN is available in the .env file
if "TELEGRAM_TOKEN" not in config:
    raise ValueError("TELEGRAM_TOKEN not found in .env file")

TELEGRAM_TOKEN = config["TELEGRAM_TOKEN"]

# Define the HTTP proxy
http_proxy = "http://154.58.202.47:1337"

# Main function to run the entire script with the proxy settings
def main_with_proxy():
    # Set the HTTP proxy environment variables
    os.environ["http_proxy"] = http_proxy
    os.environ["https_proxy"] = http_proxy

    main()  # Call the main Telegram bot function

# Function to download a song using spotdl
def download_song(url, temp_dir):
    os.makedirs(temp_dir, exist_ok=True)
    os.chdir(temp_dir)

    try:
        # Download the song from the provided URL using spotdl
        subprocess.run(["spotdl", "download", url, "--threads", "12", "--lyrics", "genius", "--bitrate", "320k"])
    except Exception as e:
        print(f"Error downloading the song: {e}")

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

# Function to handle user messages and download songs
def get_single_song(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    url = update.effective_message.text.strip()

    temp_dir = tempfile.mkdtemp()
    
    download_song(url, temp_dir)
    convert_to_mp3(temp_dir)
    send_song_to_telegram(update, context, temp_dir)
    
    # Clean up the temporary directory
    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    # Run the entire script with the proxy settings
    main_with_proxy()
