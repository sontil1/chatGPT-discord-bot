import threading
import os
import asyncio
from flask import Flask, render_template, request, jsonify
from src.aclient import discordClient
from src.providers import ProviderManager

app = Flask(__name__)
pm = ProviderManager()

@app.route('/')
def index():
    # Menampilkan tampilan chat ala ChatGPT
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    user_msg = data.get("message", "")
    # Menjalankan AI dengan sistem Llama -> GPT Backup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res = loop.run_until_complete(pm.get_response_with_backup([{"role": "user", "content": user_msg}]))
    return jsonify({"reply": res["text"], "model": res["name"]})

def run_discord():
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        discordClient.run(token)

if __name__ == "__main__":
    # Menjalankan Discord Bot tanpa mengganggu Website
    threading.Thread(target=run_discord, daemon=True).start()
    # Port 8000 adalah standar agar Koyeb terdeteksi Healthy
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port)
