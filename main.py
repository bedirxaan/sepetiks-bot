import logging
import sqlite3
import random
import requests # Kütüphane yerine doğrudan istek kullanıyoruz
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- WEB SERVER (RENDER İÇİN) ---
def keep_alive():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, BaseHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=keep_alive).start()

# --- AYARLAR ---
GEMINI_API_KEY = "AIzaSyAFgiYV_uK1YBgke7ydF_GSz1zoHSX94wk"
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"
ADMIN_ID = 575544867

# --- LOGLAMA ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- VERİTABANI ---
def init_db():
    conn = sqlite3.connect('sepetiks_users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect('sepetiks_users.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('sepetiks_users.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

# --- ÜRÜN LİSTESİ (WhatsApp Katalog Ürünlerin) ---
PRODUCTS = [
    {"id": 1, "name": "BOSCH Çelik Çaycı", "price": 1350, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 2, "name": "BOSCH LED'li Cam Çaycı", "price": 1100, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 3, "name": "Gold ve Desenli Baharatlık", "price": 1150, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 4, "name": "Kamp Çadırı (12-16-24 Kişilik)", "price": 1899, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 5, "name": "Stanley Tutmalı El Termosu", "price": 999, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 6, "name": "3'lü Polo Valiz Seti", "price": 3000, "cat": "Canta", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 7, "name": "Kilim Sırt Çantası", "price": 400, "cat": "Canta", "url": "https://www.shopier.com/sepetiks04"},
]

# --- YAPAY ZEKA SOHBET (DOĞRUDAN HTTP İSTEĞİ) ---
def ask_gemini_direct(user_message):
    # Senin cURL komutunda çalışan model ve endpoint'i buraya kurduk
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    products_text = "\n".join([f"- {p['name']} ({p['price']} TL)" for p in PRODUCTS])
    
    system_prompt = (
        "Sen Sepetiks Asistanısın. Samimi ve profesyonel bir satış danışmanı gibi davran. "
        f"Şu ürünleri satıyoruz: {products_text}. "
        f"Müşteri Mesajı: {user_message}"
    )

    payload = {
        "contents": [{
            "parts": [{"text": system_prompt}]
        }]
    }

    try:
        response = requests.post(url, json=payload)
        response_json = response.json()
        # Yanıtı ayıkla
        return response_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        logging.error(f"AI Hatası: {e}")
        return "Şu an biraz yoğunum, Hasan Bey size hemen yardımcı olacak. 🌸"

# --- TELEGRAM FONKSİYONLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)
    welcome_text = f"🌿 Merhaba {user.first_name}! Sepetiks AI Asistanı hazır. Bana dilediğini sorabilirsin!"
    keyboard = [[InlineKeyboardButton("🛍 Ürünleri Gör", callback_data='catalog')], [InlineKeyboardButton("🌐 Mağaza", url='https://www.shopier.com/sepetiks04')]]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    # Kütüphane kullanmadan doğrudan istek atıyoruz
    ai_response = ask_gemini_direct(text)
    
    await update.message.reply_text(ai_response)
    
    if user.id != ADMIN_ID:
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🤖 Sohbet: {user.first_name}\nSoru: {text}\nCevap: {ai_response}")
        except: pass

def main():
    init_db()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Sepetiks AI Bot (HTTP Mode) Aktif!")
    application.run_polling()

if __name__ == '__main__':
    main()
    
