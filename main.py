import logging
import sqlite3
import requests
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- WEB SERVER (RENDER'I UYANIK TUTAR) ---
def keep_alive():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, BaseHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=keep_alive).start()

# --- AYARLAR ---
GEMINI_API_KEY = "AIzaSyAFgiYV_uK1YBgke7ydF_GSz1zoHSX94wk"
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"
ADMIN_ID = 575544867

# --- VERİTABANI ---
def init_db():
    conn = sqlite3.connect('sepetiks_users.db')
    conn.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT)')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect('sepetiks_users.db')
    conn.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    conn.close()

# --- ÜRÜN KATALOĞU (RESİMLERDEN GÜNCELLENDİ) ---
#
PRODUCTS = [
    {"name": "3'lü Polo Valiz Seti", "price": 3000},
    {"name": "BOSCH Çelik Çaycı", "price": 1350},
    {"name": "BOSCH LED'li Cam Çaycı", "price": 1100},
    {"name": "Kamp Çadırı (12-16-24 Kişilik)", "price": 1899},
    {"name": "Travel Pot 4 LT Termos", "price": 1799},
    {"name": "Stanley Tutmalı Termos", "price": 999},
    {"name": "Vicalina Çelik Çaydanlık", "price": 1650},
    {"name": "Sumall Sun El Feneri", "price": 1650},
    {"name": "Colombia Taktik Kemer", "price": 299}
]

# --- YAPAY ZEKA SOHBET ---
def ask_gemini_direct(user_message):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    products_text = "\n".join([f"- {p['name']} ({p['price']} TL)" for p in PRODUCTS])
    
    prompt = (
        "Sen Sepetiks Mağaza Asistanısın. Samimi ve enerjik bir dille konuş. "
        f"Ürün listemiz: {products_text}. "
        "Müşteriye sadece bu ürünlerle ilgili bilgi ver ve ikna edici ol."
    )

    payload = {"contents": [{"parts": [{"text": f"{prompt}\n\nMüşteri Sorusu: {user_message}"}]}]}

    try:
        response = requests.post(url, json=payload, timeout=15)
        res_json = response.json()
        # Eğer hata varsa direkt hatayı döndür ki görelim
        if response.status_code != 200:
            return f"⚠️ Teknik Hata ({response.status_code}): {response.text[:50]}"
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"⚠️ Bağlantı Hatası: {str(e)}"

# --- TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_user.id, update.effective_user.username)
    await update.message.reply_text("🌿 Merhaba! Ben Sepetiks AI Asistanı. Ürünlerimiz hakkında dilediğini sorabilirsin!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    ai_response = ask_gemini_direct(update.message.text)
    await update.message.reply_text(ai_response)
    
    if update.message.from_user.id != ADMIN_ID:
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"👤 {update.message.from_user.first_name}: {update.message.text}\n🤖: {ai_response}")
        except: pass

def main():
    init_db()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
