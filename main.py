import os
from flask import Flask
from threading import Thread
from dotenv import load_dotenv
from src.bot import run_discord_bot
from src.log import logger

# --- AWAL KODE PENJAGA PORT (FLASK) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and healthy!"

def run():
    # Ini yang akan menjawab Port 8000 di Koyeb
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run)
    t.start()
# --- AKHIR KODE PENJAGA PORT ---

def validate_environment():
    """Validate required environment variables"""
    required_vars = ["DISCORD_BOT_TOKEN"]
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    return True

if __name__ == "__main__":
    load_dotenv()
    
    if validate_environment():
        # JALANKAN PENJAGA PORT DI BACKGROUND
        print("Starting web server for Koyeb...")
        keep_alive()
        
        # JALANKAN BOT DISCORD
        print("Starting Discord bot...")
        run_discord_bot()
