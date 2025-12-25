import logging
import sqlite3
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- KİŞİSEL AYARLARIN ---
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"
ADMIN_ID = 575544867  # Hasan Sabbah ID'si eklendi ✅

# --- LOGLAMA (Hata Takibi İçin) ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- VERİTABANI (Müşteri Listesi) ---
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

# --- ÜRÜN LİSTESİ (Burayı İstediğin Gibi Çoğaltabilirsin) ---
PRODUCTS = [
    {"id": 1, "name": "El Yapımı Seramik Kase", "price": 120, "cat": "Dekor", "url": "https://shopier.com/sepetiks04"},
    {"id": 2, "name": "Doğal Taş Bileklik", "price": 85, "cat": "Aksesuar", "url": "https://shopier.com/sepetiks04"},
    {"id": 3, "name": "Kürt Deq Motifli Saat", "price": 450, "cat": "Saat", "url": "https://shopier.com/sepetiks04"},
    {"id": 4, "name": "Minimalist Vazo", "price": 200, "cat": "Dekor", "url": "https://shopier.com/sepetiks04"},
]

# --- KOMUT FONKSİYONLARI ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username) # Müşteriyi kaydet
    
    welcome_text = f"👋 Merhaba {user.first_name}! \n\nBen Sepetiks Asistanı. Sana özel el yapımı ürünlerimizi keşfetmek için hazırım. Ne yapmak istersin?"
    
    # Ana Menü Butonları
    keyboard = [
        [InlineKeyboardButton("🛍 Ürünleri İncele", callback_data='catalog')],
        [InlineKeyboardButton("🎲 Günün Fırsatı", callback_data='random_item'), InlineKeyboardButton("🎁 İndirim Kodu", callback_data='promo')],
        [InlineKeyboardButton("🔍 Ürün Ara", callback_data='search_info'), InlineKeyboardButton("📞 Canlı Destek", callback_data='support')],
        [InlineKeyboardButton("🌐 Web Sitemiz", url='https://sepetiks.com')]
    ]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard))

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'catalog':
        keyboard = [
            [InlineKeyboardButton("🏠 Dekorasyon", callback_data='cat_Dekor')],
            [InlineKeyboardButton("⌚ Saat & Aksesuar", callback_data='cat_Aksesuar')],
            [InlineKeyboardButton("🔙 Ana Menü", callback_data='main_menu')]
        ]
        await query.edit_message_text("📂 Hangi kategoriyi gezmek istersin?", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('cat_'):
        category = query.data.split('_')[1]
        filtered = [p for p in PRODUCTS if p['cat'] == category or category == "Aksesuar"]
        
        text = f"✨ *{category} Koleksiyonu:*\n"
        keyboard = []
        for p in filtered:
            text += f"\n▫️ {p['name']} - {p['price']}₺"
            keyboard.append([InlineKeyboardButton(f"🛒 {p['name']} Satın Al", url=p['url'])])
        
        keyboard.append([InlineKeyboardButton("🔙 Geri Dön", callback_data='catalog')])
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'random_item':
        item = random.choice(PRODUCTS)
        text = f"🎲 *Şansına Bu Çıktı!* \n\n🔥 *{item['name']}*\n💰 Fiyat: {item['price']}₺\n\nBu ürünü kaçırma!"
        keyboard = [[InlineKeyboardButton("Hemen Al", url=item['url']), InlineKeyboardButton("🔙 Ana Menü", callback_data='main_menu')]]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'promo':
        codes = ["SEPETIKS10", "YAZ2025", "OZELMUSTERI"]
        selected = random.choice(codes)
        await query.edit_message_text(f"🎁 İndirim Kodun Hazır!\n\n`{selected}`\n\n(Shopier ödeme ekranında kullanabilirsin.)", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Ana Menü", callback_data='main_menu')]]))

    elif query.data == 'search_info':
        await query.edit_message_text("🔍 Aramak istediğin ürünü (örneğin: 'saat') direkt buraya yaz, hemen bulayım.")

    elif query.data == 'support':
        await query.edit_message_text("📞 *Canlı Destek*\n\nBuraya yazdığın mesajlar doğrudan Hasan Sabbah'a iletilecektir. Sorunu yazabilirsin.", parse_mode='Markdown')

    elif query.data == 'main_menu':
        await start(update, context)

# --- MESAJ YAKALAYICI VE YÖNLENDİRİCİ ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    
    # Eğer mesajı atan SEN değilsen (Müşteriyse), mesaj sana gelsin
    if user_id != ADMIN_ID:
        try:
            admin_text = f"📩 *YENİ MÜŞTERİ MESAJI*\n\n👤 Kimden: {user_name} (ID: `{user_id}`)\n💬 Mesaj: {update.message.text}"
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode='Markdown')
            
            # Otomatik cevap verelim ki müşteri boşlukta hissetmesin
            # (Eğer ürün aramıyorsa sadece destek mesajıysa)
            if not any(p['name'].lower() in text for p in PRODUCTS):
                await update.message.reply_text("Mesajın yetkiliye iletildi, en kısa sürede dönüş yapacağız. ✅")
        except Exception as e:
            print(f"Hata: {e}")

    # Eğer mesaj içinde ürün adı geçiyorsa otomatik link ver
    found_products = [p for p in PRODUCTS if text in p['name'].lower()]
    if found_products:
        reply = "🔍 *Bunu mu aradın?*\n"
        for p in found_products:
            reply += f"🔹 {p['name']} - {p['price']}₺\n👉 Link: {p['url']}\n"
        await update.message.reply_text(reply)

# --- ADMIN DUYURU SİSTEMİ (BROADCAST) ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    # Güvenlik Kontrolü: Sadece SEN kullanabilirsin
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu komutu kullanmaya yetkiniz yok.")
        return 

    if not context.args:
        await update.message.reply_text("Kullanım: `/duyuru Mesajınız` şeklinde yazmalısın.")
        return

    message = " ".join(context.args)
    
    # Veritabanındaki herkesi çek
    conn = sqlite3.connect('sepetiks_users.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    conn.close()

    sent_count = 0
    await update.message.reply_text(f"📢 Duyuru gönderimi başladı... ({len(users)} kişi)")
    
    for u in users:
        try:
            # Kendine tekrar atmasın
            if u[0] != ADMIN_ID:
                await context.bot.send_message(chat_id=u[0], text=f"🔔 *SEPETİKS DUYURU*\n\n{message}", parse_mode='Markdown')
                sent_count += 1
        except:
            pass # Kullanıcı botu engellediyse hata vermez, geçer
    
    await update.message.reply_text(f"✅ İşlem Tamam! Mesaj {sent_count} kişiye ulaştı.")

# --- ANA MOTOR ---
def main():
    init_db() # Veritabanını kur
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("duyuru", broadcast))
    application.add_handler(CallbackQueryHandler(menu_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Sepetiks Botu Başarıyla Çalıştı! Telegram'a girip deneyebilirsin.")
    application.run_polling()

if __name__ == '__main__':
    main()
  
