from flask import Flask, request, abort
import os
import json

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        app.logger.info("📬 收到 LINE Webhook：\n" + json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        app.logger.error(f"❌ 處理 webhook 發生錯誤: {e}")
    return 'OK'

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
