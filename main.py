import logging
import sqlite3
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- WEB SERVER (RENDER İÇİN UYANDIRMA SERVİSİ) ---
def keep_alive():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, BaseHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=keep_alive).start()

# --- AYARLAR ---
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"
ADMIN_ID = 575544867  # Hasan Sabbah ID ✅

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

# --- GERÇEK ÜRÜN LİSTESİ (Katalogdan Çekilenler) ---
# Not: Özel ürün linkleri olmadığı için ana mağaza linki eklendi.
# İstersen url kısımlarına o ürünün direkt linkini yapıştırabilirsin.
PRODUCTS = [
    # Mutfak & Züccaciye
    {"id": 1, "name": "BOSCH Çelik Çaycı", "price": 1350, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 2, "name": "BOSCH LED'li Cam Çaycı", "price": 1100, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 3, "name": "Gold ve Desenli Baharatlık", "price": 1150, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 4, "name": "6'lı Porselen Çay Tabağı", "price": 200, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 5, "name": "6'lı Meşrubat Bardağı Seti", "price": 300, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 6, "name": "Çatal Bıçak Seti", "price": 1000, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 7, "name": "Kahve ve Baharat Öğütücü", "price": 350, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 8, "name": "3'lü Altın ve Gümüş Tepsi", "price": 1200, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 9, "name": "Vicalina Çelik Çaydanlık", "price": 1650, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 10, "name": "Bosch Çelik Kahve Makinesi", "price": 1999, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 11, "name": "Bosch Blender Seti", "price": 1500, "cat": "Mutfak", "url": "https://www.shopier.com/sepetiks04"},

    # Outdoor & Kamp & Termos
    {"id": 12, "name": "Kamp Çadırı (12-16-24 Kişilik)", "price": 1899, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 13, "name": "Unique 1 LT Çelik Termos", "price": 850, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 14, "name": "Travel Pot 4 LT Termos", "price": 1799, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 15, "name": "Sumall Çantalı El Feneri", "price": 1650, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 16, "name": "Cup Vacuum Filtreli Termos", "price": 599, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 17, "name": "Stanley Tutmalı El Termosu", "price": 999, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 18, "name": "Stanley El Termosu", "price": 700, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 19, "name": "Colombia Taktik Kemer", "price": 299, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},

    # Çanta & Seyahat & Diğer
    {"id": 20, "name": "3'lü Polo Valiz Seti", "price": 3000, "cat": "Canta", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 21, "name": "Kilim Sırt Çantası", "price": 400, "cat": "Canta", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 22, "name": "3'lü Set Hasır Çanta", "price": 300, "cat": "Canta", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 23, "name": "Yüksek Tabanlı Ortopedik Terlik", "price": 350, "cat": "Canta", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 24, "name": "Goldbaft Çift Kişilik Battaniye", "price": 850, "cat": "Ev", "url": "https://www.shopier.com/sepetiks04"},
]

# --- ANA MENÜ FONKSİYONU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)
    
    welcome_text = (
        f"🌿 **Hoş Geldin {user.first_name}!**\n\n"
        "Sepetiks'in WhatsApp kataloğundaki en özel ürünler artık burada.\n"
        "Kamp malzemelerinden mutfak setlerine kadar her şeyi inceleyebilirsin."
    )
    
    keyboard = [
        [InlineKeyboardButton("🛍 Tüm Ürünleri Gör", callback_data='catalog_start')],
        [InlineKeyboardButton("🔥 Günün Fırsatı", callback_data='random_item'), InlineKeyboardButton("🔍 Ürün Ara", callback_data='search_mode')],
        [InlineKeyboardButton("📞 Canlı Destek", callback_data='support_mode'), InlineKeyboardButton("🌐 Shopier Mağazamız", url='https://www.shopier.com/sepetiks04')]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# --- BUTON YÖNETİMİ ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # 1. KATEGORİ SEÇİM EKRANI (YENİ KATEGORİLER)
    if data == 'catalog_start':
        keyboard = [
            [InlineKeyboardButton("🏕 Outdoor & Kamp & Termos", callback_data='show_Outdoor')],
            [InlineKeyboardButton("☕ Mutfak & Züccaciye", callback_data='show_Mutfak')],
            [InlineKeyboardButton("🎒 Çanta & Seyahat", callback_data='show_Canta')],
            [InlineKeyboardButton("🏠 Ev Tekstili", callback_data='show_Ev')],
            [InlineKeyboardButton("🔙 Ana Menü", callback_data='main_menu')]
        ]
        await query.edit_message_text("📂 **Hangi kategoriyi incelemek istersin?**", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    # 2. ÜRÜNLERİ LİSTELEME
    elif data.startswith('show_'):
        category = data.split('_')[1]
        filtered_products = [p for p in PRODUCTS if p['cat'] == category]
        
        if not filtered_products:
            await query.edit_message_text("😔 Bu kategoride şu an ürün görüntülenemiyor.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data='catalog_start')]]))
            return

        text = f"✨ **{category} Ürünleri**\n"
        keyboard = []
        for p in filtered_products:
            text += f"\n🔸 {p['name']} — {p['price']}₺"
            # Shopier linkine yönlendirir
            keyboard.append([InlineKeyboardButton(f"🛒 {p['name']}", url=p['url'])])
        
        keyboard.append([InlineKeyboardButton("🔙 Kategoriler", callback_data='catalog_start')])
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    # 3. GÜNÜN FIRSATI
    elif data == 'random_item':
        item = random.choice(PRODUCTS)
        text = f"🎲 **Günün Şanslı Ürünü!** \n\n🔥 *{item['name']}*\n💰 Fiyat: {item['price']}₺\n\nBu fırsatı kaçırma!"
        keyboard = [[InlineKeyboardButton("Hemen İncele", url=item['url']), InlineKeyboardButton("🔙 Ana Menü", callback_data='main_menu')]]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    # 4. DİĞER MODLAR
    elif data == 'search_mode':
        await query.edit_message_text("🔍 **Arama Modu**\n\nAradığın ürünün ismini (örneğin: 'termos' veya 'çaycı') yazıp gönder, hemen bulayım.", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 İptal", callback_data='main_menu')]]))

    elif data == 'support_mode':
        await query.edit_message_text("📞 **Canlı Destek**\n\nSorunu veya sipariş notunu buraya yaz, doğrudan Hasan Sabbah'a ileteceğim.", 
                                      reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Vazgeç", callback_data='main_menu')]]))

    elif data == 'main_menu':
        await start(update, context)

# --- MESAJ YAKALAYICI ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user = update.message.from_user
    
    # ADMİN DEĞİLSE -> MESAJI İLET
    if user.id != ADMIN_ID:
        try:
            msg_to_admin = f"📩 **Müşteri Mesajı!**\n\n👤: {user.first_name} (@{user.username})\n💬: {update.message.text}"
            await context.bot.send_message(chat_id=ADMIN_ID, text=msg_to_admin)
            
            found = any(p['name'].lower() in text for p in PRODUCTS)
            if not found:
                await update.message.reply_text("Mesajın alındı, en kısa sürede dönüş yapacağız. 🌸")
        except:
            pass

    # ÜRÜN ARAMA FONKSİYONU
    found_products = [p for p in PRODUCTS if text in p['name'].lower()]
    if found_products:
        reply = "🔍 **İşte bulduğum ürünler:**\n"
        keyboard = []
        for p in found_products:
            reply += f"\n🌿 {p['name']} - {p['price']}₺"
            keyboard.append([InlineKeyboardButton(f"İncele: {p['name']}", url=p['url'])])
        
        await update.message.reply_text(reply, reply_markup=InlineKeyboardMarkup(keyboard))

# --- DUYURU (BROADCAST) ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("❌ Kullanım: `/duyuru Mesajınız`")
        return

    message = " ".join(context.args)
    conn = sqlite3.connect('sepetiks_users.db')
    users = conn.execute('SELECT user_id FROM users').fetchall()
    conn.close()

    count = 0
    await update.message.reply_text(f"📢 Gönderim başlıyor... ({len(users)} kişi)")
    for u in users:
        try:
            if u[0] != ADMIN_ID:
                await context.bot.send_message(chat_id=u[0], text=f"🔔 **SEPETİKS DUYURU**\n\n{message}", parse_mode='Markdown')
                count += 1
        except:
            pass
    await update.message.reply_text(f"✅ Mesaj {count} kişiye başarıyla iletildi.")

# --- MAIN ---
def main():
    init_db()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("duyuru", broadcast))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Sepetiks Bot (Katalog Sürümü) Aktif!")
    application.run_polling()

if __name__ == '__main__':
    main()
    
