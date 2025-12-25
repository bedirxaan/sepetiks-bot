import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- WEB SERVER (RENDER'I AYAKTA TUTAR) ---
def keep_alive():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, BaseHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=keep_alive).start()

# --- AYARLAR ---
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"
ADMIN_ID = 575544867
SHOP_URL = "https://www.shopier.com/sepetiks04"

# --- DEVESA ÜRÜN VERİ TABANI ---
#
SEPETIKS_DB = {
    "valiz": {
        "title": "🧳 Polo 3'lü Valiz Seti",
        "price": "3000 TL",
        "desc": "Kırılmaz ABS gövde, 360 derece döner tekerlekler. Kabin, Orta ve Büyük boy set halindedir.",
        "link": SHOP_URL
    },
    "çaycı": {
        "title": "☕ BOSCH Çay Makineleri",
        "price": "Çelik: 1350 TL / LED Cam: 1100 TL",
        "desc": "Otomatik kapanma, susuz çalışma emniyeti ve sıcak tutma özelliği mevcuttur.",
        "link": SHOP_URL
    },
    "çadır": {
        "title": "🏕 Kamp Çadırı (Devesa Boy)",
        "price": "1899 TL",
        "desc": "12, 16 ve 24 kişilik seçenekler. Su geçirmez kumaş ve kolay kurulum.",
        "link": SHOP_URL
    },
    "termos": {
        "title": "🥤 Termos Çeşitlerimiz",
        "price": "999 TL'den başlayan fiyatlarla",
        "desc": "- Stanley Tutmalı: 999 TL\n- Travel Pot 4 LT: 1799 TL\n- Unique 1 LT: 850 TL\n- Cup Vacuum: 599 TL",
        "link": SHOP_URL
    },
    "baharat": {
        "title": "🧂 Gold & Desenli Baharatlık",
        "price": "1150 TL",
        "desc": "Mutfağınıza şıklık katacak lüks tasarım baharatlık seti.",
        "link": SHOP_URL
    },
    "terlik": {
        "title": "👡 Ortopedik Terlik",
        "price": "350 TL",
        "desc": "Yüksek tabanlı, konforlu ve günlük kullanıma uygundur.",
        "link": SHOP_URL
    },
    "battaniye": {
        "title": "🛌 Goldbaft Battaniye",
        "price": "850 TL",
        "desc": "Yumuşacık dokusuyla çift kişilik lüks battaniye.",
        "link": SHOP_URL
    },
    "fener": {
        "title": "🔦 Sumall Sun El Feneri",
        "price": "1650 TL",
        "desc": "Çantalı set, yüksek lümenli ve outdoor şartlarına dayanıklı.",
        "link": SHOP_URL
    }
}

# --- YARDIMCI CEVAPLAR ---
SUPPORT = {
    "kargo": "🚚 **Kargo Bilgisi:** Siparişleriniz 24 saat içinde hazırlanır. Türkiye'nin her yerine 2-4 iş günü içinde teslim edilir.",
    "ödeme": "💳 **Ödeme Seçenekleri:** Shopier üzerinden Kredi Kartı (Taksit imkanı) veya Havale/EFT ile ödeme yapabilirsiniz.",
    "güven": "🛡️ **Güvenli mi?** Sepetiks olarak Shopier altyapısını kullanıyoruz. Ödemeleriniz 256-bit SSL ile korunmaktadır.",
    "iade": "🔄 **İade/Değişim:** Kullanılmamış ürünlerde 14 gün içinde değişim hakkınız mevcuttur."
}

# --- ANA MENÜ BUTONLARI ---
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛍 Tüm Ürünler", callback_data='all_products')],
        [InlineKeyboardButton("🏕 Kamp & Outdoor", callback_data='cat_outdoor')],
        [InlineKeyboardButton("☕ Mutfak Grubu", callback_data='cat_mutfak')],
        [InlineKeyboardButton("❓ Sık Sorulanlar", callback_data='faq')],
        [InlineKeyboardButton("🌐 Mağazaya Git", url=SHOP_URL)]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- BOT KOMUTLARI ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"🌿 **Merhaba {user_name}! Sepetiks AI Asistanına Hoş Geldin.**\n\n"
        "Sana nasıl yardımcı olabilirim? Aşağıdaki menüden bir kategori seçebilir "
        "veya merak ettiğin ürünü (örneğin: 'valiz', 'termos') direkt yazabilirsin."
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(), parse_mode='Markdown')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'all_products':
        text = "📦 **Sepetiks Popüler Ürünler:**\n\n"
        for k, v in SEPETIKS_DB.items():
            text += f"🔹 {v['title']} - {v['price']}\n"
        text += f"\nDetaylar için: {SHOP_URL}"
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode='Markdown')

    elif query.data == 'cat_outdoor':
        text = "🏕 **Outdoor Ürünlerimiz:**\n\n- Kamp Çadırı: 1899 TL\n- Stanley Termos: 999 TL\n- El Feneri Seti: 1650 TL"
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode='Markdown')

    elif query.data == 'faq':
        text = "❓ **Sıkça Sorulan Sorular:**\n\n- Kargo kaç gün?\n- Ödeme nasıl yapılır?\n- Güvenilir mi?\n\nMerak ettiğin konuyu yazabilirsin!"
        await query.edit_message_text(text, reply_markup=main_menu_keyboard(), parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text.lower()
    found = False

    # 1. Ürün Veritabanı Taraması
    for key, data in SEPETIKS_DB.items():
        if key in user_msg:
            reply = (
                f"✨ **{data['title']}**\n\n"
                f"💰 **Fiyat:** {data['price']}\n"
                f"📝 **Özellikler:** {data['desc']}\n\n"
                f"👇 Hemen Satın Al:\n{data['link']}"
            )
            await update.message.reply_text(reply, parse_mode='Markdown')
            found = True
            break

    # 2. Destek Veritabanı Taraması
    if not found:
        for key, text in SUPPORT.items():
            if key in user_msg:
                await update.message.reply_text(text, parse_mode='Markdown')
                found = True
                break

    # 3. Hiçbir şey bulunamazsa
    if not found:
        fail_text = (
            "Anlayamadım ama size yardımcı olmak isterim! 😊\n\n"
            "Şu kelimelerden birini yazarsanız size detaylı bilgi verebilirim:\n"
            "**Valiz, Çaycı, Çadır, Termos, Terlik, Baharatlık, Kargo, Ödeme**"
        )
        await update.message.reply_text(fail_text, parse_mode='Markdown', reply_markup=main_menu_keyboard())

    # 4. Admin Bilgilendirme
    if update.effective_user.id != ADMIN_ID:
        try:
            log_text = f"👤 {update.effective_user.first_name}: {update.message.text}"
            await context.bot.send_message(chat_id=ADMIN_ID, text=log_text)
        except: pass

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Sepetiks Profesyonel Botu Yayında!")
    application.run_polling()

if __name__ == '__main__':
    main()
