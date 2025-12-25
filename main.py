import logging
import sqlite3
import random
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import google.generativeai as genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- WEB SERVER (RENDER İÇİN UYANDIRMA SERVİSİ) ---
def keep_alive():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, BaseHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=keep_alive).start()

# --- AYARLAR (HEPSİ EKLENDİ) ---
# 1. Senin verdiğin Google AI Anahtarı:
GEMINI_API_KEY = "AIzaSyCLwhvKMUD1cSfCZVApnljEvv2jM1m0V_M"

# 2. Bot Tokenin:
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"

# 3. Senin Admin ID'n:
ADMIN_ID = 575544867

# --- YAPAY ZEKA AYARLARI ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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

# --- GÜNCEL ÜRÜN LİSTESİ ---
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
    # Outdoor & Kamp
    {"id": 12, "name": "Kamp Çadırı (12-16-24 Kişilik)", "price": 1899, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 13, "name": "Unique 1 LT Çelik Termos", "price": 850, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 14, "name": "Travel Pot 4 LT Termos", "price": 1799, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 15, "name": "Sumall Çantalı El Feneri", "price": 1650, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 16, "name": "Cup Vacuum Filtreli Termos", "price": 599, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 17, "name": "Stanley Tutmalı El Termosu", "price": 999, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 18, "name": "Stanley El Termosu", "price": 700, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 19, "name": "Colombia Taktik Kemer", "price": 299, "cat": "Outdoor", "url": "https://www.shopier.com/sepetiks04"},
    # Çanta & Ev
    {"id": 20, "name": "3'lü Polo Valiz Seti", "price": 3000, "cat": "Canta", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 21, "name": "Kilim Sırt Çantası", "price": 400, "cat": "Canta", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 22, "name": "3'lü Set Hasır Çanta", "price": 300, "cat": "Canta", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 23, "name": "Yüksek Tabanlı Ortopedik Terlik", "price": 350, "cat": "Canta", "url": "https://www.shopier.com/sepetiks04"},
    {"id": 24, "name": "Goldbaft Çift Kişilik Battaniye", "price": 850, "cat": "Ev", "url": "https://www.shopier.com/sepetiks04"},
]

# --- YAPAY ZEKA SOHBET FONKSİYONU ---
async def ask_gemini(user_message):
    # Ürün listesini metne döküyoruz ki yapay zeka ne sattığımızı bilsin
    products_text = "\n".join([f"- {p['name']} ({p['price']} TL) [Kategori: {p['cat']}]" for p in PRODUCTS])
    
    system_prompt = f"""
    Sen 'Sepetiks Asistan' adında, Sepetiks.com (Shopier) mağazasının yapay zeka satış danışmanısın.
    
    GÖREVLERİN VE KURALLARIN:
    1. Müşteriyle samimi, sıcak ama profesyonel bir dille konuş ("Siz" hitabı kullan, çok samimi olursa "Sen" diyebilirsin).
    2. Amacın ürünleri tanıtmak, özelliklerini övmek ve müşteriyi SATIN ALMAYA ikna etmek.
    3. Sadece aşağıdaki 'MAĞAZA ÜRÜNLERİ' listesinde olan ürünleri satabilirsin. Listede olmayan bir şey sorulursa nazikçe "Maalesef stoklarımızda yok ama şuna bakabilirsiniz..." diyerek elindekini öner.
    4. Fiyat sorulursa listeden bakıp söyle. Pazarlık yapma.
    5. Müşteri 'nasıl alırım' derse "Size gönderdiğim linkten Shopier güvencesiyle alabilirsiniz" de.
    6. Kısa ve net cevaplar ver, destan yazma. Emoji kullan 🌿🎒🏕️.
    
    MAĞAZA ÜRÜNLERİ:
    {products_text}
    
    MAĞAZA LİNKİ: https://www.shopier.com/sepetiks04
    
    Müşterinin Mesajı: {user_message}
    """
    
    try:
        response = model.generate_content(system_prompt)
        return response.text
    except Exception as e:
        return "Şu an çok yoğunum, Hasan Bey size hemen dönecektir. 🌸"

# --- OTOMATİK ÜRÜN ÖNERİSİ (ZAMANLAYICI) ---
async def send_auto_recommendation(context: ContextTypes.DEFAULT_TYPE):
    users = get_all_users()
    if not users:
        return

    item = random.choice(PRODUCTS)
    # AI ile cazip bir tanıtım metni yazdıralım
    try:
        promo_text = model.generate_content(f"Bu ürünü ({item['name']}) müşterilere anlık bildirim olarak göndereceğim. Kısa, etkileyici, emoji kullanan, harekete geçirici 2 cümlelik bir tanıtım yaz. Fiyatı: {item['price']} TL.").text
    except:
        promo_text = f"🌟 **Sizin İçin Seçtik!**\n\n{item['name']} stoklarımızda.\nFiyat: {item['price']}₺"

    msg = f"🔔 **Sepetiks Öneriyor**\n\n{promo_text}\n\n👇 Hemen İncele:"
    
    keyboard = [[InlineKeyboardButton("🛒 Ürüne Git", url=item['url'])]]
    
    count = 0
    for user_id in users:
        try:
            # Kendine atmasın, sadece müşterilere
            if user_id != ADMIN_ID:
                await context.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
                count += 1
        except:
            pass
    print(f"⏰ Otomatik öneri {count} kişiye gönderildi.")

# --- ANA MENÜ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username)
    
    welcome_text = (
        f"🌿 **Merhaba {user.first_name}!**\n\n"
        "Ben Sepetiks'in yapay zeka asistanıyım. 🤖\n"
        "Bana ürünler hakkında dilediğini sorabilirsin, seninle sohbet edebilirim veya sana en uygun ürünü önerebilirim.\n\n"
        "Hadi başlayalım, ne yapmak istersin?"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛍 Ürün Katalogu", callback_data='catalog_start')],
        [InlineKeyboardButton("🎲 Bana Tavsiye Ver", callback_data='random_item')],
        [InlineKeyboardButton("🌐 Mağazaya Git", url='https://www.shopier.com/sepetiks04')]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# --- BUTON İŞLEMLERİ ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'catalog_start':
        keyboard = [
            [InlineKeyboardButton("🏕 Outdoor & Kamp", callback_data='show_Outdoor')],
            [InlineKeyboardButton("☕ Mutfak & Züccaciye", callback_data='show_Mutfak')],
            [InlineKeyboardButton("🎒 Çanta & Seyahat", callback_data='show_Canta')],
            [InlineKeyboardButton("🏠 Ev Tekstili", callback_data='show_Ev')],
            [InlineKeyboardButton("🔙 Sohbet", callback_data='main_menu')]
        ]
        await query.edit_message_text("📂 **Hangi kategoriyi merak ediyorsun?**", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith('show_'):
        category = data.split('_')[1]
        filtered = [p for p in PRODUCTS if p['cat'] == category]
        
        if not filtered:
             await query.edit_message_text("Bu kategoride ürün kalmadı.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Geri", callback_data='catalog_start')]]))
             return

        text = f"✨ **{category} Ürünlerimiz**\n"
        keyboard = []
        for p in filtered:
            text += f"\n🔸 {p['name']} — {p['price']}₺"
            keyboard.append([InlineKeyboardButton(f"🛒 {p['name']}", url=p['url'])])
        keyboard.append([InlineKeyboardButton("🔙 Geri", callback_data='catalog_start')])
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'random_item':
        # Yapay zeka ile kullanıcıya özel yorumlu öneri
        item = random.choice(PRODUCTS)
        # Buton tıklandığında bekletme mesajı verelim
        await query.edit_message_text("🤔 **Senin için en iyisini düşünüyorum...**")
        
        ai_comment = await ask_gemini(f"Müşteriye şu ürünü önerdim: {item['name']}. Sadece bu ürün hakkında harika, kısa bir cümle söyle.")
        
        text = f"🎲 **Bence buna bayılacaksın!** \n\n🔥 *{item['name']}*\n💰 {item['price']}₺\n\n🤖 **Asistan Yorumu:**\n_{ai_comment}_"
        keyboard = [[InlineKeyboardButton("İncele", url=item['url']), InlineKeyboardButton("🔙 Ana Menü", callback_data='main_menu')]]
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == 'main_menu':
        await start(update, context)

# --- MESAJ YAKALAYICI (AI SOHBET) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.message.from_user
    
    # 1. Admin (Sen) yazıyorsan AI cevap vermesin (komutlar için)
    if user.id == ADMIN_ID:
        pass 
    
    # 2. Müşteri yazıyorsa -> YAPAY ZEKA DEVREYE GİRER
    else:
        # "Yazıyor..." efekti verelim
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        # Yapay zekaya sor
        ai_response = await ask_gemini(text)
        
        # Cevabı gönder
        await update.message.reply_text(ai_response)
        
        # Sana rapor geç
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🤖 **Bot Sohbet Ediyor!**\n\n👤 {user.first_name}: {text}\n🤖 Bot: {ai_response}")
        except:
            pass

# --- DUYURU ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if not context.args: return
    
    msg = " ".join(context.args)
    users = get_all_users()
    count = 0
    await update.message.reply_text(f"📢 Gönderim başlıyor... ({len(users)} kişi)")
    
    for u in users:
        try:
            if u != ADMIN_ID: 
                await context.bot.send_message(chat_id=u, text=f"📢 **DUYURU:**\n{msg}")
                count += 1
        except: pass
    await update.message.reply_text(f"✅ Mesaj {count} kişiye gönderildi.")

# --- MAIN ---
def main():
    init_db()
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("duyuru", broadcast))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # AI Sohbet Modülü
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # OTOMATİK ÖNERİ SİSTEMİ (JobQueue)
    if application.job_queue:
        # Her 14400 saniyede bir (4 Saatte Bir) çalışır.
        application.job_queue.run_repeating(send_auto_recommendation, interval=14400, first=60)
        print("⏰ Otomatik ürün önericisi kuruldu (4 saatte bir).")

    print("🤖 Sepetiks Yapay Zeka Asistanı Aktif!")
    application.run_polling()

if __name__ == '__main__':
    main()
