import os
import glob
import logging
import tempfile
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# /start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ **Ultimate Social Media Downloader Bot**\n\n"
        "Send me any link from **Instagram, Facebook, Twitter/X, TikTok, YouTube, Pinterest, Reddit**, etc.\n\n"
        "📸 **Photos & Multi-Slide Posts (Carousels) Supported**\n"
        "🎥 **HD Videos & Reels Supported**"
    )

# Universal Media Downloader Handler
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    # Check if input is a valid URL
    if not url.startswith(("http://", "https://")):
        return

    status_msg = await update.message.reply_text("⏳ Processing link & extracting media...")

    # Temporary directory for clean file management
    with tempfile.TemporaryDirectory() as temp_dir:
        output_template = os.path.join(temp_dir, "%(id)s_%(autonumber)s.%(ext)s")

        # yt-dlp configuration for photos & videos
        ydl_opts = {
            'outtmpl': output_template,
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
            'max_filesize': 50 * 1024 * 1024,  # 50 MB Telegram Bot limit
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Get all downloaded media files in order
            downloaded_files = sorted(glob.glob(os.path.join(temp_dir, "*")))

            if not downloaded_files:
                await status_msg.edit_text(
                    "❌ Could not download media.\n\n"
                    "Please ensure the post is public and the link is valid."
                )
                return

            await status_msg.edit_text(f"📤 Uploading {len(downloaded_files)} file(s)...")

            # Detect file type and send appropriately
            for file_path in downloaded_files:
                ext = os.path.splitext(file_path)[1].lower()

                with open(file_path, 'rb') as media_file:
                    if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        await update.message.reply_photo(photo=media_file)
                    elif ext in ['.mp4', '.mkv', '.webm', '.mov']:
                        await update.message.reply_video(video=media_file)
                    elif ext in ['.mp3', '.m4a', '.wav', '.opus']:
                        await update.message.reply_audio(audio=media_file)
                    else:
                        await update.message.reply_document(document=media_file)

            await status_msg.delete()

        except Exception as e:
            await status_msg.edit_text(f"❌ Error processing media: {str(e)}")

def main():
    # Replace with your Telegram Bot Token from @BotFather
    TOKEN = '8903792426:AAEYx8yR7LMKh3OOy0Nm7ebc7eO7njBK-V4'

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_media))

    print("🤖 All-in-One Downloader Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()