import os
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REFRESH_TOKEN = os.environ.get('REFRESH_TOKEN')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# قائمة المعرفات الحقيقية الخاصة بـ Angry Birds
ANGRY_BIRDS_IDS = [
    "CgkI0_f0z_QKEAIQIg"
]

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

def unlock_achievement(achievement_id):
    access_token = get_access_token()
    url = f"https://games.googleapis.com/games/v1/achievements/{achievement_id}/unlock"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers)
    return response.json()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("إكمال إنجاز Angry Birds 2", callback_data='UNLOCK_ANGRY_BIRDS')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر اللعبة لإكمال إنجازاتها سحابياً:", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'UNLOCK_ANGRY_BIRDS':
        await query.edit_message_text(text="جاري إرسال طلب الإنجاز إلى Google Play...")
        
        unlocked_count = 0
        for ach_id in ANGRY_BIRDS_IDS:
            res = unlock_achievement(ach_id)
            if res.get("newlyUnlocked") or res.get("kind") == "games#achievementUnlockResponse":
                unlocked_count += 1
                
        if unlocked_count > 0:
            await query.edit_message_text(text=f"تم إكمال العملية بنجاح! تم فتح ({unlocked_count}) إنجاز جديد على حسابك.")
        else:
            await query.edit_message_text(text="تم الاتصال بالخادم، والإنجاز إما مكتمل سابقاً على هذا الحساب أو مستوفى بالكامل.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("البوت يعمل الآن...")
    app.run_polling()
