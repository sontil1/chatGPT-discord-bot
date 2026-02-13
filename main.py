import os
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
from src.bot import run_discord_bot
from src.log import logger

# 1. SETUP FLASK UNTUK MENIPU KOYEB (Agar Port 8000 Aktif)
app = Flask('')

@app.route('/')
def home():
    return "Bot is Online!"

def run():
    # Koyeb akan senang karena port 8000 sekarang ada isinya
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# 2. JALANKAN BOT SEPERTI BIASA
if __name__ == "__main__":
    load_dotenv()
    
    # Panggil Flask di background
    print("Starting Flask web server...")
    keep_alive()
    
    # Jalankan bot Discord kamu
    print("Starting Discord bot...")
    run_discord_bot()
