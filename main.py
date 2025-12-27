import logging
import threading
import difflib
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- WEB SERVER (RENDER İÇİN ZORUNLU) ---
def keep_alive():
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, BaseHTTPRequestHandler)
    print("✅ Web Server Başlatıldı (Port 8080)")
    httpd.serve_forever()

threading.Thread(target=keep_alive).start()

# --- AYARLAR ---
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"
ADMIN_ID = 575544867
SHOP_URL = "https://www.shopier.com/sepetiks04"
WHATSAPP = "https://wa.me/905555555555" 

# --- RAM VERİTABANI (ASLA ÇÖKMEZ) ---
# Bot yeniden başlayınca sıfırlanır ama Render'da en stabil çalışan yöntem budur.
USERS = set() # Kullanıcı ID'leri
CART = {}     # Sepetler {user_id: [product_obj, ...]}
BANNED = set() # Banlılar

# --- ÜRÜN KATALOĞU ---
#
PRODUCTS = [
    {"id": 1, "name": "Polo 3'lü Valiz Seti", "price": 3000, "stock": 50, "desc": "Kırılmaz ABS, 360° Tekerlek, 3'lü Set", "cat": "canta"},
    {"id": 2, "name": "BOSCH Çelik Çaycı", "price": 1350, "stock": 20, "desc": "Paslanmaz çelik, ikili ısıtma", "cat": "mutfak"},
    {"id": 3, "name": "Kamp Çadırı (12 Kişilik)", "price": 1899, "stock": 10, "desc": "Su geçirmez devasa çadır", "cat": "outdoor"},
    {"id": 4, "name": "Stanley Termos", "price": 999, "stock": 100, "desc": "24 saat koruma garantili", "cat": "outdoor"},
    {"id": 5, "name": "Ortopedik Terlik", "price": 350, "stock": 200, "desc": "Anatomik taban rahatlık", "cat": "giyim"},
    {"id": 6, "name": "Gold Baharatlık", "price": 1150, "stock": 30, "desc": "Porselen lüks set", "cat": "mutfak"},
    {"id": 7, "name": "Sumall El Feneri", "price": 1650, "stock": 15, "desc": "1km menzilli şarjlı", "cat": "outdoor"}
]

# --- YARDIMCI FONKSİYONLAR ---
def find_product(query):
    # Tüm ürün isimlerini listele
    names = [p['name'] for p in PRODUCTS]
    # Yazım hatasına rağmen en yakın sonucu bul (Fuzzy Search)
    matches = difflib.get_close_matches(query, names, n=1, cutoff=0.4)
    
    if matches:
        for p in PRODUCTS:
            if p['name'] == matches[0]:
                return p
    # İsimde geçiyorsa da bul (Örn: "çay" yazınca "Çaycı"yı bul)
    for p in PRODUCTS:
        if query.lower() in p['name'].lower():
            return p
    return None

def get_cart_total(user_id):
    items = CART.get(user_id, [])
    return sum(item['price'] for item in items)

# --- KLAVYELER ---
def main_menu():
    kb = [
        [InlineKeyboardButton("🛍 Ürünleri Gör", callback_data="all_prod"), InlineKeyboardButton("🔥 Fırsat", callback_data="deal")],
        [InlineKeyboardButton("🛒 Sepetim", callback_data="my_cart"), InlineKeyboardButton("📦 Kargo", callback_data="track")],
        [InlineKeyboardButton("🆘 Destek", callback_data="support"), InlineKeyboardButton("🌐 Web Site", url=SHOP_URL)]
    ]
    return InlineKeyboardMarkup(kb)

def admin_menu():
    kb = [
        [InlineKeyboardButton("📢 Duyuru Yap", callback_data="adm_broadcast")],
        [InlineKeyboardButton("📊 İstatistik", callback_data="adm_stats")]
    ]
    return InlineKeyboardMarkup(kb)

# --- KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.add(user.id)
    
    if user.id in BANNED:
        await update.message.reply_text("⛔ Engellendiniz.")
        return

    welcome = (
        f"🌿 **Merhaba {user.first_name}!**\n"
        "Sepetiks Profesyonel Asistanı hazır.\n\n"
        "🔎 **Ne aramıştınız?** (Örn: 'valiz', 'termos', 'çaycı')\n"
        "👇 Veya menüden seçin:"
    )
    await update.message.reply_text(welcome, reply_markup=main_menu(), parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    text = update.message.text
    user_id = update.effective_user.id

    # Admin Paneli
    if text == "/admin" and user_id == ADMIN_ID:
        await update.message.reply_text("🔑 **Yönetici Paneli**", reply_markup=admin_menu())
        return

    # Destek Mesajı
    if text.startswith("/destek"):
        msg = text.replace("/destek", "").strip()
        if msg:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🆘 **DESTEK TALEBİ**\n👤: {update.effective_user.first_name}\n📝: {msg}")
            await update.message.reply_text("✅ Mesajınız iletildi.")
        else:
            await update.message.reply_text("Lütfen `/destek mesajınız` şeklinde yazın.")
        return

    # Ürün Arama
    product = find_product(text)
    
    if product:
        status = "🟢 Stokta Var" if product['stock'] > 0 else "🔴 Tükendi"
        reply = (
            f"✨ **{product['name']}**\n"
            f"📂 Kategori: {product['cat'].upper()}\n"
            f"📝 {product['desc']}\n\n"
            f"💰 **Fiyat:** {product['price']} TL\n"
            f"📦 Durum: {status}"
        )
        kb = [[InlineKeyboardButton("➕ Sepete Ekle", callback_data=f"add_{product['id']}")], [InlineKeyboardButton("Satın Al", url=SHOP_URL)]]
        await update.message.reply_text(reply, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
    else:
        await update.message.reply_text(
            "🤔 Tam anlayamadım. Ürün adını yazabilir veya menüyü kullanabilirsin.",
            reply_markup=main_menu()
        )

# --- BUTONLAR ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    await query.answer()

    # Ürün Listeleme
    if data == "all_prod":
        text = "📦 **KATALOG**\n\n"
        for p in PRODUCTS:
            text += f"▪️ {p['name']} - {p['price']} TL\n"
        await query.edit_message_text(text, reply_markup=main_menu(), parse_mode='Markdown')

    # Sepete Ekle
    elif data.startswith("add_"):
        pid = int(data.split("_")[1])
        # Ürünü bul
        prod = next((p for p in PRODUCTS if p['id'] == pid), None)
        if prod:
            if user_id not in CART: CART[user_id] = []
            CART[user_id].append(prod)
            await query.edit_message_text(f"✅ **{prod['name']}** sepete atıldı!", reply_markup=main_menu(), parse_mode='Markdown')

    # Sepetim
    elif data == "my_cart":
        items = CART.get(user_id, [])
        if not items:
            await query.edit_message_text("🛒 Sepetin boş.", reply_markup=main_menu())
            return
        
        total = sum(i['price'] for i in items)
        text = "🛒 **SEPETİNİZ**\n\n"
        for i in items:
            text += f"▫️ {i['name']} - {i['price']} TL\n"
        text += f"\n💰 **TOPLAM:** {total} TL"
        
        kb = [[InlineKeyboardButton("💳 Satın Al", url=SHOP_URL)], [InlineKeyboardButton("🗑 Boşalt", callback_data="clear")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    # Sepet Temizle
    elif data == "clear":
        CART[user_id] = []
        await query.edit_message_text("🗑 Sepet temizlendi.", reply_markup=main_menu())

    # Fırsat
    elif data == "deal":
        import random
        p = random.choice(PRODUCTS)
        new_price = int(p['price'] * 0.9)
        text = f"🔥 **GÜNÜN FIRSATI** 🔥\n\n**{p['name']}**\n~~{p['price']} TL~~ yerine **{new_price} TL**!"
        kb = [[InlineKeyboardButton("Kaçırma", url=SHOP_URL)]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    # Destek
    elif data == "support":
        text = f"🆘 **İletişim**\n📞 WhatsApp: {WHATSAPP}\n\nMesaj bırakmak için: `/destek mesajınız`"
        await query.edit_message_text(text, reply_markup=main_menu(), parse_mode='Markdown')
        
    # Kargo
    elif data == "track":
        tarih = (datetime.now() + timedelta(days=2)).strftime("%d.%m.%Y")
        await query.edit_message_text(f"🚚 Siparişleriniz **{tarih}** tarihinde kargoya verilir.", reply_markup=main_menu(), parse_mode='Markdown')

    # Admin Stats
    elif data == "adm_stats":
        if user_id != ADMIN_ID: return
        await query.edit_message_text(f"📊 **Durum:**\n👥 Kullanıcı: {len(USERS)}\n📦 Ürün: {len(PRODUCTS)}", reply_markup=admin_menu())

# --- DUYURU ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("⚠️ Mesaj yaz.")
        return
    
    count = 0
    await update.message.reply_text(f"📢 {len(USERS)} kişiye gönderiliyor...")
    for uid in USERS:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 **DUYURU**\n\n{msg}")
            count += 1
        except: pass
    await update.message.reply_text(f"✅ {count} kişiye gitti.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("duyuru", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("✅ Sepetiks RAM Modu (Stabil) Aktif!")
    app.run_polling()

if __name__ == '__main__':
    main()
