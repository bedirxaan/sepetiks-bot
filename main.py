import logging
import threading
import os
import difflib
import random
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- WEB SERVER (RENDER İÇİN OTOMATİK PORT AYARI) ---
# Bu kısım UptimeRobot'un 'Down' hatası vermesini engeller.
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Sepetiks Bot 7/24 Aktif!")

def keep_alive():
    # Render'ın atadığı portu otomatik bulur
    port = int(os.environ.get("PORT", 10000))
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"✅ Web Server Başlatıldı. Port: {port}")
    httpd.serve_forever()

# Server'ı arka planda başlat
threading.Thread(target=keep_alive, daemon=True).start()

# --- AYARLAR (LÜTFEN BURAYI DOLDURUN) ---
TOKEN = "8400134709:AAFIXgPcCdBySd71X_oP8d8JTtJFGvpN7P8"
ADMIN_ID = 575544867
GENEL_SHOPIER_LINK = "https://www.shopier.com/sepetiks04"

# Google İşletme Profilinden Alınan Bilgiler
WHATSAPP_LINK = "https://wa.me/905XXXXXXXXXX" # Google profilinizdeki numarayı buraya yazın (Örn: 90532...)
ADRES_BILGISI = "Kale Sok., No:4/1, Çiftepınar Mah., Doğubayazıt, Ağrı" 
GOOGLE_MAPS_LINK = "https://share.google/EO5YjvHx72pWShl6e" # Sizin verdiğiniz link
CALISMA_SAATLERI = "Her Gün: 09:00 - 20:00"

# --- RAM VERİTABANI (HIZLI VE HATASIZ) ---
USERS = set()
CART = {}
BANNED = set()

# --- DETAYLI ÜRÜN KATALOĞU ---
# NOT: 'link' kısımlarına Shopier mağazanızdaki o ürüne ait özel linki yapıştırın.
PRODUCTS = [
    {
        "id": 1, 
        "name": "Polo 3'lü Valiz Seti", 
        "price": 3000, 
        "stock": 50, 
        "desc": "Kırılmaz ABS gövde, 360° Döner Tekerlek, Şifreli Kilit. (Kabin+Orta+Büyük)", 
        "cat": "canta",
        "link": "https://www.shopier.com/sepetiks04/polo-valiz-linki" # Buraya ürünün kendi linkini yapıştırın
    },
    {
        "id": 2, 
        "name": "BOSCH Çelik Çaycı", 
        "price": 1350, 
        "stock": 20, 
        "desc": "Paslanmaz çelik, ikili ısıtma sistemi, enerji tasarruflu, 1.8L kapasite.", 
        "cat": "mutfak",
        "link": "https://www.shopier.com/sepetiks04/bosch-cayci-linki"
    },
    {
        "id": 3, 
        "name": "Kamp Çadırı (12 Kişilik)", 
        "price": 1899, 
        "stock": 10, 
        "desc": "Su geçirmez kumaş, sineklikli pencereler, kolay kurulum.", 
        "cat": "outdoor",
        "link": "https://www.shopier.com/sepetiks04/kamp-cadiri-linki"
    },
    {
        "id": 4, 
        "name": "Stanley Tutmalı Termos", 
        "price": 999, 
        "stock": 100, 
        "desc": "24 saat sıcak/soğuk koruma, ömür boyu garanti, paslanmaz çelik.", 
        "cat": "outdoor",
        "link": "https://www.shopier.com/sepetiks04/stanley-termos-linki"
    },
    {
        "id": 5, 
        "name": "Ortopedik Terlik", 
        "price": 350, 
        "stock": 200, 
        "desc": "Yüksek taban, anatomik yapı, gün boyu konfor sağlar.", 
        "cat": "giyim",
        "link": "https://www.shopier.com/sepetiks04/terlik-linki"
    },
    {
        "id": 6, 
        "name": "Gold Baharatlık Seti", 
        "price": 1150, 
        "stock": 30, 
        "desc": "Porselen ve gold detaylı, standlı lüks baharat takımı.", 
        "cat": "mutfak",
        "link": "https://www.shopier.com/sepetiks04/baharatlik-linki"
    },
    {
        "id": 7, 
        "name": "Sumall El Feneri", 
        "price": 1650, 
        "stock": 15, 
        "desc": "1km menzilli, şarjlı, powerbank özellikli profesyonel fener.", 
        "cat": "outdoor",
        "link": "https://www.shopier.com/sepetiks04/fener-linki"
    }
]

# --- AKILLI ARAMA FONKSİYONU ---
def find_product(query):
    # 1. Tam eşleşme veya benzerlik (Fuzzy Search)
    matches = difflib.get_close_matches(query, [p['name'] for p in PRODUCTS], n=1, cutoff=0.4)
    if matches:
        return next((p for p in PRODUCTS if p['name'] == matches[0]), None)
    
    # 2. İçinde geçiyorsa (Örn: "çay" yazınca "Çaycı"yı bul)
    for p in PRODUCTS:
        if query.lower() in p['name'].lower():
            return p
    return None

# --- MENÜ TASARIMLARI ---
def main_menu():
    kb = [
        [InlineKeyboardButton("🛍 Tüm Ürünler", callback_data="all_prod"), InlineKeyboardButton("🔥 Fırsat Ürünü", callback_data="deal")],
        [InlineKeyboardButton("🛒 Sepetim", callback_data="my_cart"), InlineKeyboardButton("📦 Kargo Takip", callback_data="track")],
        [InlineKeyboardButton("📍 Adres & Konum", callback_data="location"), InlineKeyboardButton("📞 İletişim", callback_data="contact")],
        [InlineKeyboardButton("🌐 Shopier Mağazası", url=GENEL_SHOPIER_LINK)]
    ]
    return InlineKeyboardMarkup(kb)

def admin_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Duyuru Yap", callback_data="adm_broadcast")]])

# --- TEMEL KOMUTLAR ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.add(user.id)
    
    if user.id in BANNED:
        await update.message.reply_text("⛔ Mağazadan engellendiniz.")
        return

    welcome_text = (
        f"🌿 **Merhaba {user.first_name}!**\n\n"
        "**Sepetiks Doğubayazıt Asistanına Hoş Geldin.**\n"
        "Size nasıl yardımcı olabilirim?\n\n"
        "🔍 **Ürün Arama:** 'Valiz', 'Çaycı', 'Termos' yazabilirsin.\n"
        "👇 **Veya menüden seçebilirsin:**"
    )
    await update.message.reply_text(welcome_text, reply_markup=main_menu(), parse_mode='Markdown')

# --- MESAJ YAKALAYICI ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    text = update.message.text
    user_id = update.effective_user.id

    # Admin Paneli
    if text == "/admin" and user_id == ADMIN_ID:
        await update.message.reply_text("🔑 **Yönetici Paneli**", reply_markup=admin_menu())
        return

    # Destek Talebi
    if text.startswith("/destek"):
        msg = text.replace("/destek", "").strip()
        if msg:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"🆘 **DESTEK TALEBİ**\n👤: {update.effective_user.first_name}\n📝: {msg}")
            await update.message.reply_text("✅ Mesajınız yetkiliye iletildi, size dönüş yapılacaktır.")
        else:
            await update.message.reply_text("Lütfen mesajınızı `/destek [mesajınız]` şeklinde yazın.")
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
        # Eğer özel link girildiyse onu kullan, yoksa genel linki kullan
        buy_link = product['link'] if "shopier.com" in product['link'] else GENEL_SHOPIER_LINK
        
        kb = [[InlineKeyboardButton("➕ Sepete Ekle", callback_data=f"add_{product['id']}")], 
              [InlineKeyboardButton("💳 Hemen Satın Al", url=buy_link)]]
        
        await update.message.reply_text(reply, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        
    else:
        await update.message.reply_text(
            "🤔 Aradığınız ürünü tam anlayamadım.\n"
            "- Ürün adını yazabilir (Örn: Çaycı, Fener)\n"
            "- Veya `/destek` yazarak bize ulaşabilirsiniz.",
            reply_markup=main_menu()
        )

# --- BUTON FONKSİYONLARI ---
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    await query.answer()

    # Tüm Ürünleri Listele
    if data == "all_prod":
        text = "📦 **ÜRÜN KATALOĞU**\n\n"
        for p in PRODUCTS:
            text += f"▪️ {p['name']} - {p['price']} TL\n"
        await query.edit_message_text(text, reply_markup=main_menu(), parse_mode='Markdown')

    # Sepete Ekle
    elif data.startswith("add_"):
        pid = int(data.split("_")[1])
        prod = next((p for p in PRODUCTS if p['id'] == pid), None)
        if prod:
            if user_id not in CART: CART[user_id] = []
            CART[user_id].append(prod)
            await query.edit_message_text(f"✅ **{prod['name']}** sepete eklendi!\nBaşka bir arzunuz?", reply_markup=main_menu(), parse_mode='Markdown')

    # Sepetim
    elif data == "my_cart":
        items = CART.get(user_id, [])
        if not items:
            await query.edit_message_text("🛒 Sepetiniz şu an boş.", reply_markup=main_menu())
            return
        
        total = sum(i['price'] for i in items)
        text = "🛒 **SEPETİNİZ**\n\n"
        for i in items:
            text += f"▫️ {i['name']} - {i['price']} TL\n"
        text += f"\n💰 **TOPLAM:** {total} TL"
        
        kb = [[InlineKeyboardButton("💳 Sepeti Onayla ve Satın Al", url=GENEL_SHOPIER_LINK)], 
              [InlineKeyboardButton("🗑 Sepeti Boşalt", callback_data="clear")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    # Sepet Temizle
    elif data == "clear":
        CART[user_id] = []
        await query.edit_message_text("🗑 Sepetiniz temizlendi.", reply_markup=main_menu())

    # İletişim Bilgileri (Google Profilinden)
    elif data == "contact":
        text = (
            "📞 **İLETİŞİM BİLGİLERİ**\n\n"
            f"📱 WhatsApp: {WHATSAPP_LINK}\n"
            f"🕒 Çalışma Saatleri: {CALISMA_SAATLERI}\n"
            "💬 Bize 7/24 buradan yazabilirsiniz."
        )
        kb = [[InlineKeyboardButton("📲 WhatsApp'tan Yaz", url=WHATSAPP_LINK)]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    # Konum ve Adres
    elif data == "location":
        text = (
            "📍 **MAĞAZA ADRESİMİZ**\n\n"
            f"🏢 {ADRES_BILGISI}\n\n"
            "👇 Haritada görmek için tıklayın:"
        )
        kb = [[InlineKeyboardButton("🗺 Google Haritalar'da Aç", url=GOOGLE_MAPS_LINK)]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

    # Kargo Takip
    elif data == "track":
        tarih = (datetime.now() + timedelta(days=2)).strftime("%d.%m.%Y")
        await query.edit_message_text(f"🚚 Siparişleriniz en geç **{tarih}** tarihinde kargoya verilir.", reply_markup=main_menu(), parse_mode='Markdown')

    # Fırsat Ürünü
    elif data == "deal":
        p = random.choice(PRODUCTS)
        new_price = int(p['price'] * 0.9)
        text = f"🔥 **GÜNÜN FIRSATI** 🔥\n\n**{p['name']}**\n~~{p['price']} TL~~ yerine sadece **{new_price} TL**!"
        # Fırsat ürününe de özel link varsa o butona eklenir
        link = p['link'] if "shopier.com" in p['link'] else GENEL_SHOPIER_LINK
        kb = [[InlineKeyboardButton("Hemen Yakala", url=link)]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

# --- DUYURU SİSTEMİ ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg: 
        await update.message.reply_text("⚠️ Boş duyuru atılamaz.")
        return
    
    count = 0
    await update.message.reply_text(f"📢 {len(USERS)} kişiye gönderiliyor...")
    for uid in USERS:
        try:
            await context.bot.send_message(chat_id=uid, text=f"🔔 **SEPETİKS DUYURU**\n\n{msg}")
            count += 1
        except: pass
    await update.message.reply_text(f"✅ {count} kişiye başarıyla iletildi.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("duyuru", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    print("✅ Sepetiks Final Sürüm Aktif!")
    app.run_polling()

if __name__ == '__main__':
    main()
