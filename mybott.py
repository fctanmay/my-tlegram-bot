import os
import glob
import logging
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Your Instagram Profile URL
INSTAGRAM_PROFILE_URL = "https://www.instagram.com/beatking_tanmay?igsh=bDgxMzZrcjluZzlo"

# Inline Keyboard for Instagram Follow Request
def get_follow_keyboard():
    keyboard = [
        [InlineKeyboardButton("👉 Follow on Instagram 👈", url=INSTAGRAM_PROFILE_URL)],
        [InlineKeyboardButton("✅ I Have Followed", callback_data="check_follow")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Main Menu / Help / About Keyboard
def get_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("💡 Help", callback_data="help_menu"),
         InlineKeyboardButton("ℹ️ About", callback_data="about_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['is_following'] = False  # Reset follow status
    
    welcome_text = (
        "⚠️ **Action Required To Use Bot!**\n\n"
        "To unlock and use this Media Downloader Bot, please follow our Instagram page first.\n\n"
        "1️⃣ Click **Follow on Instagram** below.\n"
        "2️⃣ After following, click **I Have Followed** to start downloading!"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_follow_keyboard(), parse_mode='Markdown')

# /help Command Handler
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **How to Use Bot:**\n\n"
        "1️⃣ First, make sure you follow our Instagram page.\n"
        "2️⃣ Send any public video or media link (Instagram, YouTube, Facebook, etc.).\n"
        "3️⃣ **Video Quality & Limit:** Best quality up to **720p / 1080p** (Recommended video length: **under 10-15 minutes** for fast downloading).\n"
        "4️⃣ Wait a few seconds while the bot fetches and uploads the video for you!"
    )
    await update.message.reply_text(help_text, reply_markup=get_menu_keyboard(), parse_mode='Markdown')

# /about Command Handler
async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        "🤖 **About This Bot:**\n\n"
        "This is an automated high-speed media downloader bot designed to fetch your favourite videos seamlessly.\n\n"
        "👨‍💻 **Developer:** Tanmay Kumar Das\n"
        "📧 **Contact:** tkd3432@gmail.com\n"
        "🚀 **Powered by:** Python & yt-dlp"
    )
    await update.message.reply_text(about_text, reply_markup=get_menu_keyboard(), parse_mode='Markdown')

# Button Click Handler (For Follow & Menu clicks)
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_follow":
        context.user_data['is_following'] = True
        
        success_text = (
            "⚡ **Thank you for following!**\n\n"
            "🎬 **Media Downloader Bot is now UNLOCKED!**\n\n"
            "📌 **How to use:**\n"
            "Just copy & paste any video URL here to download.\n"
            "(Tip: Send videos under 10-15 mins for faster processing!)\n\n"
            "👨‍💻 **Developer:** Tanmay Kumar Das\n"
            "📧 **Contact:** tkd3432@gmail.com"
        )
        await query.edit_message_text(text=success_text, reply_markup=get_menu_keyboard(), parse_mode='Markdown')

    elif query.data == "help_menu":
        help_text = (
            "📖 **How to Use Bot:**\n\n"
            "1️⃣ Send any public video link.\n"
            "2️⃣ **Video Limit:** Best performance for videos **under 10-15 minutes**.\n"
            "3️⃣ Quality: HD/Best available."
        )
        await query.message.reply_text(help_text, reply_markup=get_menu_keyboard(), parse_mode='Markdown')

    elif query.data == "about_menu":
        about_text = (
            "ℹ️ **Bot Information:**\n\n"
            "Automated Video Downloader Bot.\n"
            "👨‍💻 **Developer:** Tanmay Kumar Das\n"
            "📧 **Contact:** tkd3432@gmail.com"
        )
        await query.message.reply_text(about_text, reply_markup=get_menu_keyboard(), parse_mode='Markdown')

# Media Downloader Handler
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if user clicked "I Have Followed"
    if not context.user_data.get('is_following', False):
        alert_text = (
            "🔒 **Bot is Locked!**\n\n"
            "You must follow our Instagram page to use this bot.\n"
            "Click the button below to follow and unlock!"
        )
        await update.message.reply_text(alert_text, reply_markup=get_follow_keyboard(), parse_mode='Markdown')
        return

    url = update.message.text.strip()
    status_message = await update.message.reply_text("⏳ Processing your link, please wait...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        ydl_opts = {
            'outtmpl': os.path.join(tmp_dir, '%(title)s.%(ext)s'),
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            downloaded_files = glob.glob(os.path.join(tmp_dir, '*'))
            if not downloaded_files:
                await status_message.edit_text("❌ Failed to download media. Please check if the link is correct.")
                return

            video_file = downloaded_files[0]
            
            file_size_mb = os.path.getsize(video_file) / (1024 * 1024)
            if file_size_mb > 50:
                await status_message.edit_text("⚠️ **File is too large!**\n\nThe video size exceeds Telegram's limit (50MB). Please try downloading a shorter video (under 10-15 mins).")
                return

            await status_message.edit_text("📤 Uploading your video...")

            with open(video_file, 'rb') as vf:
                await update.message.reply_video(video=vf)

            await status_message.delete()

        except Exception as e:
            logging.error(f"Error during download: {e}")
            await status_message.edit_text("❌ Something went wrong! Make sure the link is public, valid, and the video is not too long.")

def main():
    TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        return

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))

    application.run_polling()

if __name__ == "__main__":
    main()
