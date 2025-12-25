import logging
import sqlite3
import requests
import json
import os
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
# Senin paylaştığın Groq API Anahtarı
GROQ_API_KEY = "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"
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"
ADMIN_ID = 575544867

# --- ÜRÜN LİSTESİ (KATALOG GÖRSELLERİNDEN) ---
#
PRODUCTS = [
    {"name": "3'lü Polo Valiz Seti", "price": 3000},
    {"name": "BOSCH Çelik Çaycı", "price": 1350},
    {"name": "BOSCH LED'li Cam Çaycı", "price": 1100},
    {"name": "Kamp Çadırı (12-16-24 Kişilik)", "price": 1899},
    {"name": "Unique 1 LT Çelik Termos", "price": 850},
    {"name": "Stanley Tutmalı Termos", "price": 999},
    {"name": "Vicalina Çelik Çaydanlık", "price": 1650},
    {"name": "Sumall Sun El Feneri", "price": 1650},
    {"name": "Colombia Taktik Kemer", "price": 299},
    {"name": "Gold ve Desenli Baharatlık", "price": 1150},
    {"name": "6'lı Porselen Desenli Çay Tabağı", "price": 200},
    {"name": "6'lı Meşrubat Seti", "price": 300},
    {"name": "Çatal Bıçak Seti", "price": 1000},
    {"name": "Travel Pot 4 LT Termos", "price": 1799},
    {"name": "Kahve ve Baharat Öğütücü", "price": 350},
    {"name": "3'lü Altın ve Gümüş Tepsi", "price": 1200},
    {"name": "Goldbaft Battaniye", "price": 850},
    {"name": "Cup Vacuum Filtreli Termos", "price": 599},
    {"name": "Bosch Çelik Kahve Makinesi", "price": 1999},
    {"name": "Bosch Blender Seti", "price": 1500},
    {"name": "Stanley El Termosu", "price": 700},
    {"name": "Yüksek Tabanlı Ortopedik Terlik", "price": 350}
]

# --- YAPAY ZEKA SOHBET (GROQ) ---
def ask_llama(user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    prod_list = "\n".join([f"- {p['name']} ({p['price']} TL)" for p in PRODUCTS])
    
    system_prompt = (
        "Sen Sepetiks Mağaza Asistanısın. Müşterilerle samimi, enerjik ve profesyonel konuş. "
        "Müşteriye 'Brem' deme, daha kurumsal ama sıcak bir dil kullan. "
        f"Ürün kataloğumuz şudur: {prod_list}. "
        "Soruları bu ürünlere dayanarak yanıtla. Eğer ürün bizde yoksa benzerini öner. "
        "Satın almak isterlerse 'Shopier linkimizden güvenle alabilirsiniz' de."
    )

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"⚠️ Teknik bir aksaklık (Hata: {response.status_code}). Hasan Bey size yardımcı olacak."
    except Exception as e:
        return "⚠️ Bağlantı kurulamadı. Lütfen az sonra tekrar deneyin."

# --- TELEGRAM FONKSİYONLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = f"🌿 Merhaba {update.effective_user.first_name}! Sepetiks'in akıllı asistanıyım. Sana bugün hangi ürünümüz hakkında bilgi verebilirim?"
    await update.message.reply_text(welcome)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    ai_response = ask_llama(update.message.text)
    await update.message.reply_text(ai_response)
    
    # Raporlama (Sana bildirim gelir)
    if update.message.from_user.id != ADMIN_ID:
        try:
            log_text = f"👤 {update.message.from_user.first_name}: {update.message.text}\n🤖: {ai_response}"
            await context.bot.send_message(chat_id=ADMIN_ID, text=log_text)
        except: pass

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
