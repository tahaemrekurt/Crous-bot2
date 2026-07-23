import asyncio
import os
import sys
import smtplib
from email.mime.text import MIMEText
from urllib.parse import urlparse

# ======================== SETTINGS =========================
TARGET_URL = "https://trouverunlogement.lescrous.fr/tools/47/search?bounds=7.6881371_48.6461896_7.8360646_48.491861&locationName=Strasbourg"          
HEADLESS   = True   # GitHub Actions için mutlaka True olmalı
# ===========================================================

# --- EMAIL CONFIGURATION ---
SENDER_EMAIL = "kurttahaemre@gmail.com"
SENDER_PASSWORD = "ijyq ysbl bsgy izym" # Google Uygulama Şifreniz
RECEIVER_EMAIL = "kurttahaemre@gmail.com"

def send_alert(housing_url):
    subject = "🏠 CROUS Strasbourg: GERÇEK İLAN TESPİT EDİLDİ!"
    body = f"CROUS sisteminden gerçek bir arama verisi / ilan akışı yakalandı!\n\nLink: {housing_url}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

async def monitor():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        page = await browser.new_page()

        # Sadece ağ isteklerini dinle
        page.on("request", lambda req: asyncio.create_task(handle(req)))

        print(f"🔎 Monitoring Strasbourg (Filtrelenmiş): {TARGET_URL}")
        await page.goto(TARGET_URL, wait_until="networkidle")

        # İsteklerin toparlanması için kısa bir süre bekleyip güvenle kapatıyoruz
        print("⏳ İstekler dinleniyor...")
        await asyncio.sleep(5)
        print("✅ Kontrol tamamlandı, oturum kapatılıyor.")

async def handle(request):
    url = request.url
    
    # Kriter: Sadece CROUS'un arama / veri API'sine giden istekleri dikkate al
    if "/api/" in url and "search" in url:
        print(f"🎯 Gerçek Arama API İsteği Yakalandı: {url}")
        
        # API'den gelen yanıtı kontrol et (Ev var mı?)
        try:
            response = await request.response()
            if response:
                body = await response.text()
                # Eğer gelen JSON verisinin içinde 'items' doluysa veya 'results' varsa
                if '"items":[' in body and '"items":[]' not in body:
                    print("🎉 Ev / İlan Bulundu!")
                    send_alert(url)
                else:
                    print("API yanıtı boş (Şu an ev yok).")
        except Exception as e:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        print("\n👋 Durduruldu.")
