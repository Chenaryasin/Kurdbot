import sqlite3, json, os
from flask import Flask, jsonify, request
from flask_cors import CORS
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import threading

# --- بەشی سێرڤەر (Flask) ---
app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('kurd_service.db')
    conn.row_factory = sqlite3.Row
    return conn

# دروستکردنی خشتە ئەگەر نەبێت
conn = get_db_connection()
conn.execute('''CREATE TABLE IF NOT EXISTS professionals 
                (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, job TEXT, exp TEXT, addr TEXT, photo_id TEXT)''')
conn.close()

@app.route('/')
def home():
    return "Server is Running!"

@app.route('/api/professionals', methods=['GET'])
def get_pros():
    conn = get_db_connection()
    pros = conn.execute('SELECT * FROM professionals').fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in pros])

# --- بەشی بۆت (Telegram) ---
TOKEN = '8699282925:AAF5fzggDBXjtJAhwuTNzYwMXEmRAFWro1k'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # لینکی گیتھەبەکەت وەک خۆی دەمێنێتەوە
    web_app = WebAppInfo(url="https://chenaryasin.github.io/Kurdbot/")
    kbd = [[KeyboardButton("کردنەوەی ئەپڵیکەیشن 📱", web_app=web_app)]]
    await update.message.reply_text(
        "بەخێربێیت بۆ وەشانی ئۆنلاینی خزمەتگوزاری کوردستان ✨",
        reply_markup=ReplyKeyboardMarkup(kbd, resize_keyboard=True)
    )

async def handle_web_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = json.loads(update.effective_message.web_app_data.data)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO professionals (name, phone, job, exp, addr) VALUES (?, ?, ?, ?, ?)",
                (data['name'], data['phone'], data['job'], data['exp'], data['addr']))
    last_id = cursor.lastrowid
    conn.commit()
    conn.close()
    context.user_data['editing_id'] = last_id
    await update.message.reply_text(f"✅ کاک {data['name']}، زانیارییەکانت تۆمارکرا. ئێستا وێنەیەک بنێرە:")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = context.user_data.get('editing_id')
    if pid:
        fid = update.message.photo[-1].file_id
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE professionals SET photo_id = ? WHERE id = ?", (fid, pid))
        conn.commit()
        conn.close()
        await update.message.reply_text("✨ وێنەکە پاشکەوت کرا و تۆمارەکەت تەواو بوو!")
        del context.user_data['editing_id']

def run_flask():
    # پۆرتی Render بە شێوەی ئۆتۆماتیکی وەردەگرێت
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def main():
    # ڕاکردنی Flask لە پاشبنەما
    threading.Thread(target=run_flask, daemon=True).start()
    
    # ڕاکردنی بۆت
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_data))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.run_polling()

if __name__ == '__main__':
    main()