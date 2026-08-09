from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "I am alive!"

def run():
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

import glob
import logging
import tempfile
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Configuration with Direct Telegram Bot Token
BOT_TOKEN = "8903792426:AAFOtHIB965Wi-immu0AU6ngZlisbWOd6ZU"
INSTAGRAM_PROFILE_URL = "https://www.instagram.com/beatking_tanmay?igsh=bDgxMzZrcjluZzlo"

def get_follow_keyboard():
    keyboard = [
        [InlineKeyboardButton("👉 Follow on Instagram 👈", url=INSTAGRAM_PROFILE_URL)],
        [InlineKeyboardButton("✅ I Have Followed", callback_data="check_follow")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💡 Help", callback_data="help_menu"),
         InlineKeyboardButton("ℹ️ About", callback_data="about_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['is_following'] = False
    welcome_text = (
        "⚠️ **Action Required To Use Bot!**\n\n"
        "To unlock and use this Media Downloader Bot, please follow our Instagram page first.\n\n"
        "1️⃣ Click **Follow on Instagram** below.\n"
        "2️⃣ After following, click **I Have Followed** to start downloading!"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_follow_keyboard(), parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **How to Use Bot:**\n\n"
        "1️⃣ Send any public video link.\n"
        "2️⃣ **Video Limit:** Recommended for videos **under 10-15 minutes**.\n"
        "3️⃣ Quality: Best available HD."
    )
    await update.message.reply_text(help_text, reply_markup=get_menu_keyboard(), parse_mode='Markdown')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "🤖 **About This Bot:**\n\n"
        "Automated High-Speed Media Downloader Bot.\n\n"
        "👨‍💻 **Developer:** Tanmay Kumar Das\n"
        "📧 **Contact:** tkd3432@gmail.com"
    )
    await update.message.reply_text(about_text, reply_markup=get_menu_keyboard(), parse_mode='Markdown')

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_follow":
        context.user_data['is_following'] = True
        success_text = (
            "⚡ **Thank you for following!**\n\n"
            "🎬 **Media Downloader Bot is now UNLOCKED!**\n\n"
            "📌 **How to use:**\n"
            "Just copy & paste any video URL here to download.\n\n"
            "👨‍💻 **Developer:** Tanmay Kumar Das\n"
            "📧 **Contact:** tkd3432@gmail.com"
        )
        await query.edit_message_text(text=success_text, reply_markup=get_menu_keyboard(), parse_mode='Markdown')

    elif query.data == "help_menu":
        help_text = "📖 **Send any public video URL to start downloading!**"
        await query.message.reply_text(help_text, reply_markup=get_menu_keyboard(), parse_mode='Markdown')

    elif query.data == "about_menu":
        about_text = "ℹ️ **Developer:** Tanmay Kumar Das\n📧 **Contact:** tkd3432@gmail.com"
        await query.message.reply_text(about_text, reply_markup=get_menu_keyboard(), parse_mode='Markdown')

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('is_following', False):
        alert_text = (
            "🔒 **Bot is Locked!**\n\n"
            "You must follow our Instagram page to use this bot."
        )
        await update.message.reply_text(alert_text, reply_markup=get_follow_keyboard(), parse_mode='Markdown')
        return

    url = update.message.text.strip()
    status_message = await update.message.reply_text("⏳ Processing your link, please wait...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        ydl_opts = {
            'outtmpl': os.path.join(tmp_dir, '%(id)s.%(ext)s'),
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=True)

            # Extracting Details (Uploader, Date, Location)
            uploader = info_dict.get('uploader') or info_dict.get('uploader_id') or 'Unknown Creator'
            
            raw_date = info_dict.get('upload_date')
            if raw_date:
                upload_date = datetime.strptime(raw_date, '%Y%m%d').strftime('%d %b %Y')
            else:
                upload_date = 'N/A'

            location = info_dict.get('location') or info_dict.get('location_tag') or 'Not Specified'

            # Caption Format
            caption_text = (
                f"🎬 **Media Downloaded Successfully!**\n\n"
                f"👤 **Uploaded By:** {uploader}\n"
                f"📅 **Upload Date:** {upload_date}\n"
                f"📍 **Location:** {location}\n\n"
                f"👨‍💻 **Bot Developer:** Tanmay Kumar Das"
            )

            downloaded_files = glob.glob(os.path.join(tmp_dir, '*'))
            if not downloaded_files:
                await status_message.edit_text("❌ Failed to download media. Please check the link.")
                return

            video_file = downloaded_files[0]
            
            file_size_mb = os.path.getsize(video_file) / (1024 * 1024)
            if file_size_mb > 50:
                await status_message.edit_text("⚠️ **File exceeds Telegram's 50MB limit.** Try a shorter video.")
                return

            await status_message.edit_text("📤 Uploading your video...")

            with open(video_file, 'rb') as vf:
                await update.message.reply_video(video=vf, caption=caption_text, parse_mode='Markdown')

            await status_message.delete()

        except Exception as e:
            logging.error(f"Error during download: {e}")
            await status_message.edit_text("❌ Failed to download. Ensure the link is public and valid.")

def main():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or BOT_TOKEN

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))

    application.run_polling()

if __name__ == "__main__":
    keep_alive()  # Runs the Flask server to prevent Render timeouts
    main()
