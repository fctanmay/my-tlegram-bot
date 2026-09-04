import os
import logging
import threading
import subprocess
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
    return "🤖 Universal HD Video, Tagged Video & MP3 Downloader Bot is Running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# 👋 Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_msg = (
        "✨ **Welcome to Universal Downloader Bot!** ✨\n\n"
        "📥 Send any video link, and the bot will send:\n"
        "1️⃣ **Original HD Video**\n"
        "2️⃣ **Custom Video with Uploader Name Written on it** 🏷️\n"
        "3️⃣ **MP3 Audio File** 🎶\n\n"
        "👑 **Developed & Maintained by:** Tanmay Kumar Das\n"
        "📧 **Contact:** tkd3432@gmail.com"
    )
    await update.message.reply_text(welcome_msg, parse_mode="Markdown")

# 🏷️ Function to burn uploader name onto the video using FFmpeg watermark
def add_uploader_watermark(input_video, output_video, uploader_name):
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if not os.path.exists(font_path):
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        
        if os.path.exists(font_path):
            text_filter = f"drawtext=text='Uploader: {uploader_name}':fontfile={font_path}:fontsize=24:fontcolor=white:box=1:boxcolor=black@0.6:x=20:y=20"
        else:
            text_filter = f"drawtext=text='Uploader: {uploader_name}':fontsize=24:fontcolor=white:box=1:boxcolor=black@0.6:x=20:y=20"

        cmd = [
            "ffmpeg", "-y", "-i", input_video,
            "-vf", text_filter,
            "-codec:a", "copy", output_video
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except Exception as e:
        logger.error(f"Watermark generation error: {e}")
        return False

# 📥 URL Handler (Direct Processing without restrictions)
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text.startswith("http"):
        return

    status_msg = await update.message.reply_text(
        "⏳ **Processing Media & Generating Tagged Video... Please wait.** 🚀🏷️🎶",
        parse_mode="Markdown",
    )

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

    if os.path.exists(COOKIE_FILE):
        video_opts["cookiefile"] = COOKIE_FILE

    video_path = None
    tagged_video_path = None
    audio_path = None

    try:
        # 1️⃣ Download Original Video
        with yt_dlp.YoutubeDL(video_opts) as ydl:
            info_dict = ydl.extract_info(text, download=True)
            if "entries" in info_dict:
                info_dict = info_dict["entries"][0]
            
            video_path = ydl.prepare_filename(info_dict)
            if not video_path.endswith('.mp4') and os.path.exists(video_path.rsplit('.', 1)[0] + '.mp4'):
                video_path = video_path.rsplit('.', 1)[0] + '.mp4'

        file_id = info_dict.get("id", "media")
        uploader_name = info_dict.get("uploader", "Social Media User")
        download_time = update.message.date.strftime("%Y-%m-%d %H:%M")

        # 2️⃣ Create Tagged Video with Uploader Name Watermark
        tagged_video_path = os.path.join(DOWNLOAD_DIR, f"{file_id}_tagged.mp4")
        watermark_success = add_uploader_watermark(video_path, tagged_video_path, uploader_name)
        if not watermark_success:
            tagged_video_path = None

        # 3️⃣ Extract MP3 Audio
        audio_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp3")
        audio_opts = {
            "outtmpl": os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s"),
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
            "noplaylist": True,
        }
        if os.path.exists(COOKIE_FILE):
            audio_opts["cookiefile"] = COOKIE_FILE

        with yt_dlp.YoutubeDL(audio_opts) as ydl_audio:
            ydl_audio.download([text])

        caption = (
            f"✅ **Media & Custom Tagged Video Generated!** 🎉🏷️🎶\n\n"
            f"👤 **Uploader:** {uploader_name}\n"
            f"📥 **Downloaded on:** {download_time}\n\n"
            f"👑 **Developed by:** Tanmay Kumar Das\n"
            f"📧 **Email:** tkd3432@gmail.com"
        )

        # Send Original HD Video
        if video_path and os.path.exists(video_path):
            with open(video_path, "rb") as vid_file:
                await context.bot.send_video(
                    chat_id=update.message.chat_id,
                    video=vid_file,
                    caption=caption,
                    parse_mode="Markdown",
                )

        # Send Tagged Video (With Uploader Name Watermark on it)
        if tagged_video_path and os.path.exists(tagged_video_path):
            with open(tagged_video_path, "rb") as tag_file:
                await context.bot.send_video(
                    chat_id=update.message.chat_id,
                    video=tag_file,
                    caption=f"🏷️ **Custom Video with Uploader Name Watermark:** `{uploader_name}`\n👑 **Developed by:** Tanmay Kumar Das",
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
        for p in [video_path, tagged_video_path, audio_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
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

    logger.info("🤖 Bot started successfully without any channel restrictions!")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
