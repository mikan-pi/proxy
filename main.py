from flask import Flask, request, jsonify
import requests
import os
import time
import threading

app = Flask(__name__)

ip_cache = {}
post_data = []
post_data_str_length = 0
before_post_time = 0
is_reserved_post = False
COOLTIME = 10

# Discord Webhook のURL（環境変数で管理）
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

MANY_REQUESTS_INTERVAL = 9

class FakeStatus :status_code = 200

@app.route('/')
def home():
    return "Flask Proxy Server is running"

def send_and_clear(headers):
    global post_data
    global before_post_time
    global post_data_str_length
    global is_reserved_post
    send_str = ""
    # 先頭から2000文字になるまで加算
    while True:
        data = post_data.pop(0)
        post_data_str_length += len(data)
        send_str += data + "\n\n"
        # マイクラのチャットは255文字が上限なので1600+255でもオーバーしない
        if post_data_str_length > 1600 or len(post_data) == 0:
            break
    ret = FakeStatus()
    if data:
        ret = requests.post(DISCORD_WEBHOOK_URL, json={"content": send_str}, headers=headers)
        post_data = []
        post_data_str_length = 0
        before_post_time = 0

    is_reserved_post = False
    return ret

@app.route('/proxy', methods=['POST'])
def proxy():
    global before_post_time, is_reserved_post
    if not DISCORD_WEBHOOK_URL:
        return jsonify({"error": "Webhook URL is not set"}), 500
    
    # 同じipからrequestsが連続で飛んできてたら
    # if request.remote_addr in ip_cache and time.time() - ip_cache[request.remote_addr] < MANY_REQUESTS_INTERVAL:
    #     return jsonify({"error": "Too many requests from this IP"}), 429
    
    ip_cache[request.remote_addr] = time.time()
    data = request.json
    headers = {'Content-Type': 'application/json'}

    post_data.append(data['content'])

    try:
        # もし、10秒前にpostしたら、今回はpostせず予約する
        # coolはマイナスになるが、それは問題ない -> 予約時刻までの時間 + COOLTIME - 現在時刻なので、予約実行がされるまでマイナスになる。さらにそのあとCOOLTIME秒後まで休み
        # ただし、実質的には+はあまり見えないかもしれない(+の期間は新規予約が可能で、予約時マイナスにセットされるため)
        cool = time.time() - before_post_time
        if cool < COOLTIME:
            # 動作を最低でも前回のpostから3秒後にする
            if not is_reserved_post:
                is_reserved_post = True
                threading.Timer(COOLTIME - cool, send_and_clear, args=[headers]).start()
                before_post_time = time.time() + (COOLTIME - cool)
            return jsonify({"status": "success"}), 200
        else:
            # しばらく来ていなかったら、今回は即座にpostする
            response = send_and_clear(headers)
            before_post_time = time.time()
        return jsonify({"status": "success", "response": "ok"}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)