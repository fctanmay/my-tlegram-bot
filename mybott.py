import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
import yt_dlp

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Your updated Telegram bot token
TOKEN = "8903792426:AAHFFH8eq7sH_M37eSInUJrgD597OIwgCXE"
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
  os.makedirs(DOWNLOAD_DIR)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await update.message.reply_text(
      "Welcome! Send any Instagram reel or video link here,\nI will download"
      " and send it to you quickly."
  )


async def download_instagram(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
  url = update.message.text.strip()
  if "instagram.com" not in url.lower():
    return

  processing_msg = await update.message.reply_text(
      "⏳ Processing media from Instagram, please wait..."
  )

  ydl_opts = {
      "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
      "format": "best/bestvideo+bestaudio",
      "noplaylist": True,
      "quiet": True,
  }

  file_path = None
  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info_dict = ydl.extract_info(url, download=True)
      file_path = ydl.prepare_filename(info_dict)

    if not file_path or not os.path.exists(file_path):
      raise Exception("Could not retrieve the media file.")

    # Check Telegram file size limit (max 50 MB)
    file_size = os.path.getsize(file_path) / (1024 * 1024)
    if file_size > 50:
      await context.bot.edit_message_text(
          text=(
              "⚠️ The file size is too large (greater than 50MB), so it cannot"
              " be sent via Telegram."
          ),
          chat_id=update.effective_chat.id,
          message_id=processing_msg.message_id,
      )
      return

    with open(file_path, "rb") as media_file:
      await context.bot.send_video(
          chat_id=update.effective_chat.id,
          video=media_file,
          caption="✅ Your Instagram video has been downloaded successfully!",
      )

    await context.bot.delete_message(
        chat_id=update.effective_chat.id, message_id=processing_msg.message_id
    )

  except Exception as e:
    logger.error(f"Download error: {e}")
    error_text = (
        "❌ Sorry, the video could not be downloaded. Please check if the link"
        f" is valid and public.\nError: {str(e)}"
    )
    try:
      await context.bot.edit_message_text(
          text=error_text,
          chat_id=update.effective_chat.id,
          message_id=processing_msg.message_id,
      )
    except Exception:
      await context.bot.send_message(
          chat_id=update.effective_chat.id, text=error_text
      )

  finally:
    if file_path and os.path.exists(file_path):
      try:
        os.remove(file_path)
      except Exception as cleanup_error:
        logger.error(f"Failed to delete file: {cleanup_error}")


def main():
  application = ApplicationBuilder().token(TOKEN).build()

  application.add_handler(CommandHandler("start", start))
  application.add_handler(
      MessageHandler(filters.TEXT & (~filters.COMMAND), download_instagram)
  )

  logger.info("Instagram downloader bot started successfully...")
  application.run_polling()


if __name__ == "__main__":
  main()
