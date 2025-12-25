import os  # Sistemin gizli ayarlarına erişmek için
import requests
import sqlite3
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# --- WEB SERVER (RENDER İÇİN) ---
def keep_alive():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, BaseHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=keep_alive).start()

# --- GİZLİ AYARLAR ---
# Şifreyi Render dashboard'da girdiğin isimle (Key) buradan çekiyoruz
GROQ_API_KEY = os.environ.get("GROQ_API_KEY") 
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"

def ask_llama(user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "Sen Sepetiks asistanısın. Samimi ve nazik bir dille ürünleri tanıt."},
            {"role": "user", "content": user_message}
        ]
    }
    try:
        response = requests.post(url, json=payload, timeout=15)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"⚠️ Bir bağlantı sorunu oluştu, lütfen tekrar deneyin."

async def handle_message(update, context):
    ai_response = ask_llama(update.message.text)
    await update.message.reply_text(ai_response)

def main():
    if not GROQ_API_KEY:
        print("HATA: API Anahtarı Environment Variables kısmında bulunamadı!")
        return

    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == '__main__':
    main()
        
