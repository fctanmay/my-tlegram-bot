import logging
import os
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
  return "🤖 Universal Telegram Downloader Bot is Running 24/7!"


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# 👋 Start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  welcome_msg = (
      "✨ **Welcome to Universal Downloader Bot!** ✨\n\n"
      "📥 Send any video or media link directly to download it instantly.\n\n"
      "👑 **Developed & Maintained by:** Tanmay Kumar\n"
      "📧 **Contact:** tke3432@gmail.com"
  )
  await update.message.reply_text(welcome_msg, parse_mode="Markdown")


# 📥 URL Handler & Downloader
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
  text = update.message.text.strip()

  if not text.startswith("http"):
    return

  status_msg = await update.message.reply_text(
      "⏳ **Downloading your media... Please wait a moment.** 🚀",
      parse_mode="Markdown",
  )

  ydl_opts = {
      "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
      "format": "best",
      "quiet": True,
  }
  if os.path.exists(COOKIE_FILE):
    ydl_opts["cookiefile"] = COOKIE_FILE

  file_path = None
  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info_dict = ydl.extract_info(text, download=True)
      if "entries" in info_dict:
        info_dict = info_dict["entries"][0]
      file_path = ydl.prepare_filename(info_dict)

    # 📊 Formatted Caption with Details & Credits
    uploader_name = info_dict.get("uploader", "Unknown")
    upload_date = info_dict.get("upload_date", "N/A")
    download_time = update.message.date.strftime("%Y-%m-%d %H:%M")

    caption = (
        f"✅ **Download Completed Successfully!** 🎉\n\n"
        f"👤 **Uploader:** {uploader_name}\n"
        f"📅 **Upload Date:** {upload_date}\n"
        f"📥 **Downloaded on:** {download_time}\n\n"
        f"👑 **Developed by:** Tanmay Kumar\n"
        f"📧 **Email:** tke3432@gmail.com"
    )

    with open(file_path, "rb") as media_file:
      await context.bot.send_video(
          chat_id=update.message.chat_id,
          video=media_file,
          caption=caption,
          parse_mode="Markdown",
      )

    # Delete the temporary status message
    try:
      await status_msg.delete()
    except Exception:
      pass

  except Exception as e:
    await status_msg.edit_text(
        f"❌ **Download Failed!**\n\nError: `{str(e)}`", parse_mode="Markdown"
    )

  finally:
    # 🧹 Clean up local file after sending
    if file_path and os.path.exists(file_path):
      try:
        os.remove(file_path)
      except Exception:
        pass


# 🚀 Main Function to Run Bot and Web Server
def main():
  # Start Flask in background thread
  threading.Thread(target=run_flask, daemon=True).start()

  # Build Telegram Bot Application
  application = ApplicationBuilder().token(TOKEN).build()

  application.add_handler(CommandHandler("start", start))
  application.add_handler(
      MessageHandler(filters.TEXT & (~filters.COMMAND), handle_url)
  )

  logger.info("🤖 Bot started successfully with full styling and credits!")
  application.run_polling()


if __name__ == "__main__":
  main()
