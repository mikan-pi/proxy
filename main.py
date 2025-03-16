from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

ip_cache = {}

# Discord Webhook のURL（環境変数で管理）
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

MANY_REQUESTS_INTERVAL = 9

@app.route('/')
def home():
    return "Flask Proxy Server is running!"

@app.route('/proxy', methods=['POST'])
def proxy():
    if not DISCORD_WEBHOOK_URL:
        return jsonify({"error": "Webhook URL is not set"}), 500
    
    # 同じipからrequestsが連続で飛んできてたら
    if request.remote_addr in ip_cache and time.time() - ip_cache[request.remote_addr] < MANY_REQUESTS_INTERVAL:
        return jsonify({"error": "Too many requests from this IP"}), 429
    
    ip_cache[request.remote_addr] = time.time()
    data = request.json
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, headers=headers)
        return jsonify({"status": "success", "response": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)