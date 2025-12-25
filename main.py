import logging
import sqlite3
import requests
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- WEB SERVER (RENDER İÇİN) ---
def keep_alive():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, BaseHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=keep_alive).start()

# --- AYARLAR ---
# Yeni çalışan API Key'in
GEMINI_API_KEY = "AIzaSyAFgiYV_uK1YBgke7ydF_GSz1zoHSX94wk"
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"
ADMIN_ID = 575544867

# --- ÜRÜN LİSTESİ (TÜM KATALOG GÖRSELLERİNDEN) ---
#
PRODUCTS = [
    {"name": "3'lü Polo Valiz Seti", "price": 3000},
    {"name": "Kilim Sırt Çantası", "price": 400},
    {"name": "3'lü Set Hasır Çanta", "price": 300},
    {"name": "Yüksek Tabanlı Ortopedik Terlik", "price": 350},
    {"name": "Gold ve Desenli Baharatlık", "price": 1150},
    {"name": "Kamp Çadırı (12-16-24 Kişilik)", "price": 1899},
    {"name": "BOSCH Çelik Çaycı", "price": 1350},
    {"name": "BOSCH LED'li Cam Çaycı", "price": 1100},
    {"name": "6'lı Porselen Desenli Çay Tabağı", "price": 200},
    {"name": "Unique 1 LT Çelik Termos", "price": 850},
    {"name": "6'lı Meşrubat Seti", "price": 300},
    {"name": "Çatal Bıçak Seti", "price": 1000},
    {"name": "Travel Pot 4 LT Termos", "price": 1799},
    {"name": "Kahve ve Baharat Öğütücü", "price": 350},
    {"name": "3'lü Altın ve Gümüş Tepsi", "price": 1200},
    {"name": "Goldbaft Battaniye", "price": 850},
    {"name": "Sumall Sun El Feneri", "price": 1650},
    {"name": "Cup Vacuum Filtreli Termos", "price": 599},
    {"name": "Vicalina Çelik Çaydanlık", "price": 1650},
    {"name": "Bosch Çelik Kahve Makinesi", "price": 1999},
    {"name": "Colombia Taktik Kemer", "price": 299},
    {"name": "Stanley Tutmalı Termos", "price": 999},
    {"name": "Bosch Blender Seti", "price": 1500},
    {"name": "Stanley El Termosu", "price": 700}
]

# --- YAPAY ZEKA SOHBET ---
def ask_gemini_direct(user_message):
    # API sürümünü v1 yaptık ve headers ekledik (Daha kararlı)
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
    headers = {"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY}
    
    prod_list = "\n".join([f"- {p['name']} ({p['price']} TL)" for p in PRODUCTS])
    
    prompt = (
        "Sen Sepetiks Mağaza Asistanısın. Enerjik, samimi ve nazik bir satış danışmanı gibi davran. "
        f"Ürün kataloğumuz şudur: {prod_list}. "
        "Müşterinin sorularına bu ürünleri överek cevap ver ve ikna et."
    )

    payload = {"contents": [{"parts": [{"text": f"{prompt}\n\nMüşteri: {user_message}"}]}]}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        res_json = response.json()
        if response.status_code != 200:
            return f"⚠️ Teknik Hata ({response.status_code}): {response.text[:100]}"
        return res_json['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"⚠️ Bağlantı Hatası: {str(e)}"

# --- TELEGRAM ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = f"🌿 Merhaba {update.effective_user.first_name}! Sepetiks'in akıllı asistanı hizmetinizde. Hangi ürünümüzü merak ediyorsunuz?"
    await update.message.reply_text(welcome)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    ai_response = ask_gemini_direct(update.message.text)
    await update.message.reply_text(ai_response)
    
    if update.message.from_user.id != ADMIN_ID:
        try:
            log = f"👤 {update.message.from_user.first_name}: {update.message.text}\n🤖: {ai_response}"
            await context.bot.send_message(chat_id=ADMIN_ID, text=log)
        except: pass

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
