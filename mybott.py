import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import yt_dlp

# 🛠️ Setup logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# 🔑 Bot Configuration & Directories
TOKEN = "8903792426:AAGLiKvLR1Lh7Mhx-CtKcXkI0f2uMKT9HlM"
DOWNLOAD_DIR = "downloads"
COOKIE_FILE = "cookies.txt"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# 🌐 Flask Web Server to keep Render alive 24/7
app = Flask(__name__)

@app.route("/")
def index():
    return "🤖 Universal HD Video & MP3 Downloader Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 👋 Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "✨ **Welcome to Universal Video & MP3 Downloader Bot!** ✨\n\n"
        "📥 Send any video link, and the bot will send you both **HD Video** and **MP3 Audio** automatically! 🚀🎶\n\n"
        "👑 **Developed & Maintained by:** Tanmay Kumar Das\n"
        "📧 **Contact:** tkd3432@gmail.com"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

# 📥 URL Handler (Downloads both HD Video and MP3 Audio)
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.startswith("http"):
        return

    status_msg = await update.message.reply_text(
        "⏳ **Downloading HD Video & Extracting MP3... Please wait.** 🚀🎶",
        parse_mode="Markdown",
    )

    # 1️⃣ Options for HD Video Download
    video_opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "noplaylist": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
    }

    # 2️⃣ Options for MP3 Audio Download
    audio_opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "noplaylist": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }
    }

    if os.path.exists(COOKIE_FILE):
        video_opts["cookiefile"] = COOKIE_FILE
        audio_opts["cookiefile"] = COOKIE_FILE

    video_path = None
    audio_path = None

    try:
        # Download Video
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            info_dict = ydl.extract_info(text, download=True)
            if "entries" in info_dict:
                info_dict = info_dict["entries"][0]
            video_path = ydl.prepare_filename(info_dict)
            if not video_path.endswith('.mp4') and os.path.exists(video_path.rsplit('.', 1)[0] + '.mp4'):
                video_path = video_path.rsplit('.', 1)[0] + '.mp4'

        # Download Audio (MP3)
        with yt_dlp.YoutubeDL(audio_opts) as ydl:
            file_id = info_dict.get("id", "audio")
            audio_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp3")
            # If mp3 doesn't exist from previous cache, extract again
            if not os.path.exists(audio_path):
                ydl.download([text])

        uploader_name = info_dict.get("uploader", "Social Media User")
        title = info_dict.get("title", "Media File")
        download_time = update.message.date.strftime("%Y-%m-%d %H:%M")

        caption = (
            f"✅ **HD Video & MP3 Downloaded Successfully!** 🎉🎶\n\n"
            f"👤 **Uploader/Title:** {uploader_name}\n"
            f"📥 **Downloaded on:** {download_time}\n\n"
            f"👑 **Developed by:** Tanmay Kumar Das\n"
            f"📧 **Email:** tkd3432@gmail.com"
        )

        # Send Video
        with open(video_path, "rb") as vid_file:
            await context.bot.send_video(
                chat_id=update.message.chat_id,
                video=vid_file,
                caption=caption,
                parse_mode="Markdown",
            )

        # Send MP3 Audio
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, "rb") as aud_file:
                await context.bot.send_audio(
                    chat_id=update.message.chat_id,
                    audio=aud_file,
                    caption=f"🎵 **Audio Version (MP3)**\n👑 **Developed by:** Tanmay Kumar Das",
                    parse_mode="Markdown",
                )

        try:
            await status_msg.delete()
        except Exception:
            pass

    except Exception as e:
        await status_msg.edit_text(
            f"❌ **Download Failed!**\n\nError: `{str(e)}`", parse_mode="Markdown"
        )

    finally:
        # 🧹 Clean up local files after sending
        if video_path and os.path.exists(video_path):
            try:
                os.remove(video_path)
            except Exception:
                pass
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass

# 🚀 Main Function
def main():
    threading.Thread(target=run_flask, daemon=True).start()

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_url)
    )

    logger.info("🤖 Bot started successfully with both Video and MP3 auto-download!")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
