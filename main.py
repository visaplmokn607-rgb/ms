import os
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# جلب البيانات من قسم Secrets
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('REFRESH_TOKEN')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# دالة للحصول على Access Token جديد من قوقل
def get_access_token():
    url = "https://oauth2.googleapis.com/token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, data=payload)
    return response.json().get('access_token')

# دالة إرسال طلب فتح الإنجاز إلى خوادم قوقل
def unlock_achievement(achievement_id):
    access_token = get_access_token()
    url = f"https://games.googleapis.com/games/v1/achievements/{achievement_id}/unlock"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers)
    return response.json()

# أمر البدء في تيليجرام /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # قائمة الألعاب والإنجازات (وضع معرفات الإنجازات الخاصة بكل لعبة)
    keyboard = [
        [InlineKeyboardButton("Fruit Ninja (50)", callback_data='ACHIEVEMENT_ID_1')],
        [InlineKeyboardButton("Gossip Harbor", callback_data='ACHIEVEMENT_ID_2')],
        [InlineKeyboardButton("Angry Birds 2", callback_data='ACHIEVEMENT_ID_3')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("إختر اللعبة أو المهمة لإكمال الإنجازات فوراً:", reply_markup=reply_markup)

# التعامل مع الضغط على الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    achievement_id = query.data
    await query.edit_message_text(text="جاري إرسال طلب الأداء لخوادم Google Play...")
    
    # تنفيذ الفتح سحابياً
    result = unlock_achievement(achievement_id)
    
    if result.get("newlyUnlocked") or result.get("kind") == "games#achievementUnlockResponse":
        await query.edit_message_text(text=" تم إكمال الإنجاز بنجاح في أقل من 3 ثوانٍ!")
    else:
        await query.edit_message_text(text=" حدث خطأ أو أن الإنجاز مكتمل سابقاً.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("البوت يعمل الآن سحابياً...")
    app.run_polling()
