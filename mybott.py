import logging
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
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

# Your Telegram bot token
TOKEN = "8903792426:AAGLiKvLR1Lh7Mhx-CtKcXkI0f2uMKT9HlM"
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
  os.makedirs(DOWNLOAD_DIR)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  logger.info(
      f"New /start from User: {user.full_name} (@{user.username}, ID:"
      f" {user.id})"
  )

  # Plain text used to prevent markdown parsing errors from underscores in email
  welcome_text = (
      "✨ Welcome to Universal Downloader Bot!\n\n"
      "Send any YouTube, Facebook, Instagram, or Twitter link, and choose your"
      " preferred quality.\n\n"
      "👑 Developed by: Tanmay Kumar\n"
      "📧 Email: tke3432@gmail.com"
  )
  await update.message.reply_text(welcome_text)


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  url = update.message.text.strip()
  if not url.startswith("http"):
    return

  logger.info(
      f"🔗 Link received from User: {user.full_name} (@{user.username}, ID:"
      f" {user.id}) | URL: {url}"
  )
  context.user_data["target_url"] = url

  keyboard = [
      [
          InlineKeyboardButton("🔥 1080p (Best)", callback_data="qual_best"),
          InlineKeyboardButton("💻 720p (HD)", callback_data="qual_720"),
      ],
      [
          InlineKeyboardButton("📱 480p (Medium)", callback_data="qual_480"),
          InlineKeyboardButton("🎵 Audio (MP3)", callback_data="qual_audio"),
      ],
      [InlineKeyboardButton("🔙 Back / Cancel", callback_data="qual_back")],
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)

  await update.message.reply_text(
      "🎬 Link received successfully!\nPlease select your preferred quality"
      " below:",
      reply_markup=reply_markup,
  )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  user = update.effective_user
  await query.answer()

  data = query.data

  if data == "save_acknowledged":
    await query.answer("✅ Media is ready in your chat!", show_alert=True)
    return

  if data == "qual_back":
    logger.info(
        f"❌ User {user.full_name} (ID: {user.id}) cancelled the operation."
    )
    await query.edit_message_text(
        "❌ Operation cancelled. Send a new link whenever you are ready!"
    )
    return

  url = context.user_data.get("target_url")
  if not url:
    await query.edit_message_text(
        "⚠️ Session expired. Please send the link again."
    )
    return

  logger.info(
      f"⬇️ User {user.full_name} (ID: {user.id}) selected quality option:"
      f" {data} for URL: {url}"
  )
  await query.edit_message_text(
      "⏳ Downloading media... Please wait a moment."
  )

  format_opt = "best"
  is_audio = False

  if data == "qual_best":
    format_opt = "best"
  elif data == "qual_720":
    format_opt = "best[height<=720]/best[height<=1080]/best"
  elif data == "qual_480":
    format_opt = "best[height<=480]/best[height<=720]/best"
  elif data == "qual_audio":
    format_opt = "bestaudio/best"
    is_audio = True

  ydl_opts = {
      "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
      "format": format_opt,
      "noplaylist": True,
      "quiet": True,
  }

  if is_audio:
    ydl_opts["postprocessors"] = [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }]

  file_path = None
  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info_dict = ydl.extract_info(url, download=True)
      file_path = ydl.prepare_filename(info_dict)
      if is_audio:
        file_path = os.path.splitext(file_path)[0] + ".mp3"

    if not file_path or not os.path.exists(file_path):
      raise Exception("Could not retrieve the media file.")

    file_size = os.path.getsize(file_path) / (1024 * 1024)
    if file_size > 50:
      await context.bot.send_message(
          chat_id=query.message.chat_id,
          text=(
              "⚠️ The file size exceeds 50MB, so it cannot be sent via"
              " Telegram."
          ),
      )
      return

    # Add Save Button markup for the sent media
    save_keyboard = [[InlineKeyboardButton("💾 Save / Saved", callback_data="save_acknowledged")]]
    save_markup = InlineKeyboardMarkup(save_keyboard)

    with open(file_path, "rb") as media_file:
      if is_audio:
        await context.bot.send_audio(
            chat_id=query.message.chat_id,
            audio=media_file,
            caption=(
                "🎵 Audio downloaded successfully!\n\n"
                "👑 Developed by: Tanmay Kumar\n"
                "📧 Email: tke3432@gmail.com"
            ),
            reply_markup=save_markup,
        )
      else:
        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=media_file,
            supports_streaming=True,
            caption=(
                "✅ Video downloaded successfully!\n\n"
                "👑 Developed by: Tanmay Kumar\n"
                "📧 Email: tke3432@gmail.com"
            ),
            reply_markup=save_markup,
        )

    logger.info(
        f"✅ Successfully sent media to User: {user.full_name} (ID: {user.id})"
    )

    try:
      await query.message.delete()
    except Exception:
      pass

  except Exception as e:
    logger.error(f"❌ Download error for User {user.id}: {e}")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=f"❌ Download failed. Error: {str(e)}",
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
      MessageHandler(filters.TEXT & (~filters.COMMAND), handle_url)
  )
  application.add_handler(CallbackQueryHandler(button_callback))

  logger.info("Universal Downloader Bot started successfully with Save button & fixes...")
  application.run_polling()


if __name__ == "__main__":
  main()
