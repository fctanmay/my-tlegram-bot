import logging
import os
import telebot
import yt_dlp

# লগিং সেটআপ
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# আপনার টেলিগ্রাম বট টোকেন
TOKEN = "8903792426:AAFOtHIB965Wi-immu0AU6ngZlisbWOd6ZU"

# মাল্টি-থ্রেডিং এনাবল করা হয়েছে যাতে একাধিক ইউজার একসাথে ব্যবহার করতে পারেন
bot = telebot.TeleBot(TOKEN, threaded=True)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
  os.makedirs(DOWNLOAD_DIR)


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
  welcome_text = (
      "স্বাগতম! ইনস্টাগ্রামের যেকোনো রিল বা ভিডিওর লিঙ্ক এখানে পাঠান,\nআমি"
      " সেটি দ্রুত ডাউনলোড করে আপনার কাছে পাঠিয়ে দেবো।"
  )
  bot.reply_to(message, welcome_text)


@bot.message_handler(
    func=lambda message: message.text
    and ("instagram.com" in message.text.lower())
)
def download_instagram_media(message):
  url = message.text.strip()
  processing_msg = bot.reply_to(
      message,
      "⏳ ইনস্টাগ্রাম থেকে মিডিয়া প্রসেস করা হচ্ছে, অনুগ্রহ করে অপেক্ষা"
      " করুন...",
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
      raise Exception("মিডিয়া ফাইলটি সংগ্রহ করা যায়নি।")

    # টেলিগ্রামের ফাইল সাইজ লিমিট চেক (সর্বোচ্চ ৫০ এমবি)
    file_size = os.path.getsize(file_path) / (1024 * 1024)
    if file_size > 50:
      bot.edit_message_text(
          "⚠️ ফাইলটির সাইজ অনেক বড় (৫০ এমবির বেশি), তাই টেলিগ্রামের মাধ্যমে"
          " পাঠানো সম্ভব হচ্ছে না।",
          message.chat.id,
          processing_msg.message_id,
      )
      return

    with open(file_path, "rb") as media_file:
      bot.send_video(
          message.chat.id,
          media_file,
          caption="✅ আপনার ইনস্টাগ্রাম ভিডিও সফলভাবে ডাউনলোড করা হয়েছে!",
      )

    bot.delete_message(message.chat.id, processing_msg.message_id)

  except Exception as e:
    logger.error(f"ডাউনলোড ত্রুটি: {e}")
    error_text = (
        "❌ দুঃখিত, ভিডিওটি ডাউনলোড করা সম্ভব হয়নি। লিঙ্কটি সঠিক ও পাবলিক কি"
        f" না তা যাচাই করুন।\nত্রুটি: {str(e)}"
    )
    try:
      bot.edit_message_text(
          error_text, message.chat.id, processing_msg.message_id
      )
    except Exception:
      bot.send_message(message.chat.id, error_text)

  finally:
    # সার্ভার ফাঁকা রাখতে ফাইল ডিলিট নিশ্চিত করা
    if file_path and os.path.exists(file_path):
      try:
        os.remove(file_path)
      except Exception as cleanup_error:
        logger.error(f"ফাইল মুছতে সমস্যা হয়েছে: {cleanup_error}")


if __name__ == "__main__":
  logger.info("ইনস্টাগ্রাম ডাউনলোডার বট সফলভাবে চালু হয়েছে...")
  bot.infinity_polling()
