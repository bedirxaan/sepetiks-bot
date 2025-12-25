import logging
import sqlite3
import threading
import difflib
import random
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- WEB SERVER (RENDER İÇİN) ---
def keep_alive():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, BaseHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=keep_alive).start()

# --- AYARLAR ---
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"
ADMIN_ID = 575544867
SHOP_URL = "https://www.shopier.com/sepetiks04"
WHATSAPP = "https://wa.me/905555555555" # Numaranı buraya yaz

# --- VERİTABANI YÖNETİCİSİ ---
def init_db():
    conn = sqlite3.connect('sepetiks_pro.db', check_same_thread=False)
    c = conn.cursor()
    
    # Tabloları Oluştur
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, first_name TEXT, join_date TEXT, is_banned INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER, stock INTEGER, description TEXT, category TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS cart 
                 (user_id INTEGER, product_id INTEGER, quantity INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS coupons 
                 (code TEXT PRIMARY KEY, discount INTEGER)''')

    # Başlangıç Verilerini Ekle (Eğer boşsa)
    c.execute('SELECT count(*) FROM products')
    if c.fetchone()[0] == 0:
        initial_products = [
            ("Polo 3'lü Valiz Seti", 3000, 50, "Kırılmaz ABS, 360° Tekerlek, 3'lü Set", "canta"),
            ("BOSCH Çelik Çaycı", 1350, 20, "Paslanmaz çelik, ikili ısıtma, tasarruflu", "mutfak"),
            ("Kamp Çadırı (12 Kişilik)", 1899, 10, "Su geçirmez, devasa kamp çadırı", "outdoor"),
            ("Stanley Termos", 999, 100, "24 saat koruma garantili", "outdoor"),
            ("Ortopedik Terlik", 350, 200, "Anatomik taban, rahat kullanım", "giyim"),
            ("Gold Baharatlık", 1150, 30, "Porselen ve gold detaylı lüks set", "mutfak"),
            ("Sumall El Feneri", 1650, 15, "1km menzilli şarjlı fener", "outdoor")
        ]
        c.executemany('INSERT INTO products (name, price, stock, description, category) VALUES (?,?,?,?,?)', initial_products)
        
        c.execute("INSERT OR IGNORE INTO coupons VALUES ('SEPETIKS10', 10)")
        c.execute("INSERT OR IGNORE INTO coupons VALUES ('HOSGELDIN', 5)")
        
        conn.commit()
    return conn

# Veritabanını Başlat
db = init_db()

# --- YARDIMCI FONKSİYONLAR ---
def get_product_by_fuzzy(query):
    cursor = db.cursor()
    cursor.execute("SELECT name FROM products")
    all_names = [r[0] for r in cursor.fetchall()]
    
    # Yazım hatası toleransı (Fuzzy Search)
    matches = difflib.get_close_matches(query, all_names, n=1, cutoff=0.5)
    
    if matches:
        cursor.execute("SELECT * FROM products WHERE name = ?", (matches[0],))
        return cursor.fetchone()
    return None

def get_cart_total(user_id):
    cursor = db.cursor()
    cursor.execute('''SELECT p.price, c.quantity FROM cart c 
                      JOIN products p ON c.product_id = p.id 
                      WHERE c.user_id = ?''', (user_id,))
    items = cursor.fetchall()
    return sum(item[0] * item[1] for item in items)

# --- KLAVYELER ---
def main_menu():
    kb = [
        [InlineKeyboardButton("🛍 Tüm Ürünler", callback_data="all_prod"), InlineKeyboardButton("🔥 Günün Fırsatı", callback_data="deal_day")],
        [InlineKeyboardButton("🛒 Sepetim", callback_data="my_cart"), InlineKeyboardButton("🎟 Kupon", callback_data="coupon_menu")],
        [InlineKeyboardButton("📦 Kargo Takip", callback_data="track"), InlineKeyboardButton("🆘 Canlı Destek", callback_data="support")],
        [InlineKeyboardButton("🌐 Web Sitesi", url=SHOP_URL)]
    ]
    return InlineKeyboardMarkup(kb)

def admin_menu():
    kb = [
        [InlineKeyboardButton("📢 Duyuru Yap", callback_data="adm_broadcast")],
        [InlineKeyboardButton("👥 Kullanıcı Sayısı", callback_data="adm_stats")],
        [InlineKeyboardButton("➕ Stok Ekle", callback_data="adm_stock")]
    ]
    return InlineKeyboardMarkup(kb)

# --- TEMEL KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor = db.cursor()
    
    # Kullanıcıyı Kaydet
    cursor.execute("INSERT OR IGNORE INTO users (user_id, first_name, join_date, is_banned) VALUES (?, ?, ?, 0)", 
                   (user.id, user.first_name, str(datetime.now())))
    db.commit()
    
    # Ban Kontrolü
    cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user.id,))
    if cursor.fetchone()[0] == 1:
        await update.message.reply_text("⛔ Üzgünüm, bu mağazadan engellendiniz.")
        return

    welcome = (
        f"🌿 **Merhaba {user.first_name}!**\n"
        "Sepetiks Profesyonel Asistanına hoş geldin.\n\n"
        "🔎 **Ürün mü arıyorsun?** Adını yazman yeterli (Örn: 'voliz' yazsan bile anlarım!).\n"
        "👇 Veya menüden seçim yap:"
    )
    await update.message.reply_text(welcome, reply_markup=main_menu(), parse_mode='Markdown')

# --- MESAJ YAKALAYICI (BEYİN) ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    text = update.message.text
    user_id = update.effective_user.id
    
    # Admin Paneli Girişi
    if text == "/admin" and user_id == ADMIN_ID:
        await update.message.reply_text("🔑 **Admin Paneli**", reply_markup=admin_menu())
        return

    # Destek Talebi
    if text.startswith("/destek"):
        msg = text.replace("/destek", "").strip()
        if msg:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🆘 **YENİ DESTEK TALEBİ**\n👤: {update.effective_user.first_name}\n📝: {msg}")
            await update.message.reply_text("✅ Mesajınız yetkiliye iletildi.")
        else:
            await update.message.reply_text("Lütfen mesajınızı `/destek [mesajınız]` şeklinde yazın.")
        return

    # Akıllı Ürün Arama
    product = get_product_by_fuzzy(text)
    
    if product:
        pid, name, price, stock, desc, cat = product
        
        # Stok Durumu
        stock_msg = "🟢 Stokta Var" if stock > 0 else "🔴 Tükendi"
        
        reply = (
            f"✨ **{name}**\n"
            f"📂 Kategori: {cat.upper()}\n"
            f"📝 {desc}\n\n"
            f"💰 **Fiyat:** {price} TL\n"
            f"📦 Durum: {stock_msg} ({stock} adet)"
        )
        
        kb = [[InlineKeyboardButton("➕ Sepete Ekle", callback_data=f"add_{pid}")], [InlineKeyboardButton("Satın Al (Web)", url=SHOP_URL)]]
        await update.message.reply_text(reply, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        
    else:
        # Anlaşılmadıysa
        await update.message.reply_text(
            "🔍 Aradığınızı tam bulamadım.\n"
            "- Ürün adı yazabilir (Örn: Çaycı, Termos)\n"
            "- Destek için `/destek` yazabilirsin.",
            reply_markup=main_menu()
        )

# --- BUTON İŞLEMLERİ ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    await query.answer()
    
    cursor = db.cursor()

    # Ürünleri Listele
    if data == "all_prod":
        cursor.execute("SELECT name, price FROM products")
        prods = cursor.fetchall()
        text = "📦 **ÜRÜN KATALOĞU**\n\n"
        for p in prods:
            text += f"▪️ {p[0]} - {p[1]} TL\n"
        await query.edit_message_text(text, reply_markup=main_menu(), parse_mode='Markdown')

    # Sepete Ekle
    elif data.startswith("add_"):
        pid = int(data.split("_")[1])
        cursor.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)", (user_id, pid))
        db.commit()
        await query.edit_message_text("✅ Ürün sepete eklendi!", reply_markup=main_menu())

    # Sepeti Göster
    elif data == "my_cart":
        cursor.execute('''SELECT p.name, p.price, c.quantity, c.product_id FROM cart c 
                          JOIN products p ON c.product_id = p.id 
                          WHERE c.user_id = ?''', (user_id,))
        items = cursor.fetchall()
        
        if not items:
            await query.edit_message_text("🛒 Sepetin boş.", reply_markup=main_menu())
            return
            
        total = 0
        text = "🛒 **SEPETİNİZ**\n\n"
        for item in items:
            text += f"▫️ {item[0]} (x{item[2]}) - {item[1]*item[2]} TL\n"
            total += item[1] * item[2]
            
        text += f"\n💰 **TOPLAM:** {total} TL"
        kb = [[InlineKeyboardButton("💳 Satın Al", url=SHOP_URL)], [InlineKeyboardButton("🗑 Temizle", callback_data="clear_cart")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    # Sepeti Temizle
    elif data == "clear_cart":
        cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        db.commit()
        await query.edit_message_text("🗑 Sepet boşaltıldı.", reply_markup=main_menu())

    # Günün Fırsatı
    elif data == "deal_day":
        cursor.execute("SELECT * FROM products ORDER BY RANDOM() LIMIT 1")
        p = cursor.fetchone()
        new_price = int(p[2] * 0.90) # %10 İndirim
        text = f"🔥 **GÜNÜN FIRSATI** 🔥\n\n**{p[1]}**\n~~{p[2]} TL~~ yerine sadece **{new_price} TL**!\n\n⏳ Bu fırsat 24 saat geçerli."
        kb = [[InlineKeyboardButton("Hemen Kap", url=SHOP_URL)]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    # Canlı Destek / İletişim
    elif data == "support":
        text = f"🆘 **Canlı Destek**\n\nBizimle iletişime geçmek için:\n📞 WhatsApp: {WHATSAPP}\n\nVeya buraya `/destek sorunuz` yazarak mesaj bırakabilirsiniz."
        await query.edit_message_text(text, reply_markup=main_menu(), parse_mode='Markdown')

    # Admin: İstatistik
    elif data == "adm_stats":
        if user_id != ADMIN_ID: return
        cursor.execute("SELECT count(*) FROM users")
        u_count = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM products")
        p_count = cursor.fetchone()[0]
        await query.edit_message_text(f"📊 **İstatistikler**\n\n👥 Kullanıcı: {u_count}\n📦 Ürün: {p_count}", reply_markup=admin_menu())

# --- ADMIN KOMUTU: DUYURU ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("⚠️ Mesaj yazmadın.")
        return
    
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    
    await update.message.reply_text(f"📢 {len(users)} kişiye gönderiliyor...")
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=f"📢 **DUYURU**\n\n{msg}")
        except: pass
    await update.message.reply_text("✅ Tamamlandı.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("duyuru", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("✅ Sepetiks PRO MAX (SQLite Sürümü) Aktif!")
    app.run_polling()

if __name__ == '__main__':
    main()
        
