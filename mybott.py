import os
import telebot
import yt_dlp

TOKEN = "8903792426:AAFOtHIB965Wi-immu0AU6ngZlisbWOd6ZU"
bot = telebot.TeleBot(TOKEN)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
  os.makedirs(DOWNLOAD_DIR)


@bot.message_handler(commands=["start", "help"])
def send_welcome(message):
  welcome_text = (
      "স্বাগতম! ইনস্টাগ্রামের যেকোনো রিল, ভিডিও বা পোস্টের লিঙ্ক এখানে পাঠান,"
      " আমি তা ডাউনলোড করে পাঠিয়ে দেবো।"
  )
  bot.reply_to(message, welcome_text)


@bot.message_handler(
    func=lambda message: message.text
    and ("instagram.com" in message.text.lower())
)
def download_instagram_media(message):
  url = message.text.strip()
  processing_msg = bot.reply_to(
      message, "ইনস্টাগ্রাম থেকে মিডিয়া প্রসেস করা হচ্ছে, একটু অপেক্ষা করুন..."
  )

  ydl_opts = {
      "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
      "format": "best",
      "quiet": True,
  }

  try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
      info_dict = ydl.extract_info(url, download=True)
      file_path = ydl.prepare_filename(info_dict)

    with open(file_path, "rb") as video_file:
      bot.send_video(
          message.chat.id,
          video_file,
          caption="আপনার ইনস্টাগ্রাম ভিডিও সফলভাবে ডাউনলোড হয়েছে!",
      )

    bot.delete_message(message.chat.id, processing_msg.message_id)

    if os.path.exists(file_path):
      os.remove(file_path)

  except Exception as e:
    error_text = (
        "দুঃখিত, ভিডিওটি ডাউনলোড করা সম্ভব হয়নি। লিঙ্কটি সঠিক কি না এবং পাবলিক"
        f" কি না তা চেক করুন।\nত্রুটি: {str(e)}"
    )
    bot.edit_message_text(
        error_text, message.chat.id, processing_msg.message_id
    )


if __name__ == "__main__":
  print("ইনস্টাগ্রাম ডাউনলোডার বট সফলভাবে চালু হয়েছে...")
  bot.infinity_polling()
    
