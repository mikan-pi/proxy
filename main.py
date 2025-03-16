from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Discord Webhook のURL（環境変数で管理）
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

@app.route('/')
def home():
    return "Flask Proxy Server is running!"

@app.route('/proxy', methods=['POST'])
def proxy():
    if not DISCORD_WEBHOOK_URL:
        return jsonify({"error": "Webhook URL is not set"}), 500
    
    data = request.json
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=data, headers=headers)
        return jsonify({"status": "success", "response": response.text}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)