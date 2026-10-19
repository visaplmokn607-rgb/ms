import os
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# ذاكرة مؤقتة لحفظ توكن كل مستخدم
user_tokens = {}

# أمر Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # إذا كان الحساب مربوطاً سابقاً
    if user_id in user_tokens:
        keyboard = [[InlineKeyboardButton("إكمال إنجاز Angry Birds 2", callback_data='UNLOCK')]]
        await update.message.reply_text("حسابك مربوط بنجاح! اختر اللعبة:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        # إنشاء رابط تسجيل الدخول المباشر
        auth_url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={CLIENT_ID}&"
            f"redirect_uri=https://developers.google.com/oauthplayground&"
            f"response_type=code&"
            f"scope=https://www.googleapis.com/auth/games&"
            f"access_type=offline&prompt=consent"
        )
        keyboard = [[InlineKeyboardButton("🔑 تسجيل الدخول بحساب قوقل", url=auth_url)]]
        await update.message.reply_text(
            "أهلاً بك! لربط حسابك وإكمال الإنجازات:\n\n"
            "1️⃣ اضغط على زر التسجيل أدناه واختر حساب قوقل.\n"
            "2️⃣ وافق على الصلاحيات وانسخ كود التفويض (Authorization Code).\n"
            "3️⃣ أرسل الكود هنا في الرسائل مباشرة.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# استقبال الكود وتحويله لـ Refresh Token تلقائياً
async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    user_id = update.effective_user.id
    
    # طلب التوكن من قوقل
    url = "https://oauth2.googleapis.com/token"
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': 'https://developers.google.com/oauthplayground'
    }
    res = requests.post(url, data=payload).json()
    
    if 'refresh_token' in res:
        user_tokens[user_id] = res['refresh_token']
        keyboard = [[InlineKeyboardButton("🎯 إكمال إنجاز Angry Birds 2", callback_data='UNLOCK')]]
        await update.message.reply_text(
            "تم ربط حسابك بنجاح! اضغط الزر أدناه لإكمال الإنجاز فوراً:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query_msg = "الكود غير صالح أو تم استخدامه سابقاً. أرسل /start واضغط على الرابط مجدداً."
        await update.message.reply_text(query_msg)

# معالجة ضغط زر الإنجاز
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    refresh_token = user_tokens.get(user_id)
    if not refresh_token:
        await query.edit_message_text("يرجى إرسال /start وتسجيل الدخول أولاً.")
        return

    # تجديد Access Token للحساب
    token_res = requests.post("https://oauth2.googleapis.com/token", data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }).json()
    
    access_token = token_res.get('access_token')
    if not access_token:
        await query.edit_message_text("فشل الاتصال بحساب قوقل. أرسل /start لإعادة تسجيل الدخول.")
        return

    # إرسال طلب فتح الإنجاز
    ach_id = "CgkI0_f0z_QKEAIQIg"
    unlock_res = requests.post(
        f"https://games.googleapis.com/games/v1/achievements/{ach_id}/unlock",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    if unlock_res.get("newlyUnlocked") or unlock_res.get("kind") == "games#achievementUnlockResponse":
        await query.edit_message_text("تم إكمال العملية بنجاح! تم فتح الإنجاز على حسابك.")
    else:
        await query.edit_message_text("تم الاتصال بالخادم: الإنجاز مكتمل سابقاً أو مستوفى بالكامل.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("البوت يعمل الآن...")
    app.run_polling()
