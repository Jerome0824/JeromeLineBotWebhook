from flask import Flask, request
import os
import json
import requests

app = Flask(__name__)

LINE_ACCESS_TOKEN = "HSe3XVIu1uX1L5KKbtGP8YBEHWgLKfGpdFQhYgQtVuLmLwBUTVDMi7/J4YPB8ZejXP0Wxa4m+c/VWX48tzoFcx5k+Wd/iS4uIz71lkPEtG94S7xO92ED6h7a+ZmSEXreduRqiEsmAgnyUu1ukjOqiAdB04t89/1O/w1cDnyilFU="

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    
    print("📬 收到 LINE Webhook：", flush=True)
    print(json.dumps(data, indent=2, ensure_ascii=False), flush=True)

    for event in data.get("events", []):
        if event["type"] == "message" and event["message"]["type"] == "text":
            reply_token = event["replyToken"]
            user_message = event["message"]["text"]

            reply_message = f"你說的是：「{user_message}」"

            headers = {
                "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }

            body = {
                "replyToken": reply_token,
                "messages": [
                    {
                        "type": "text",
                        "text": reply_message
                    }
                ]
            }

            res = requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)
            app.logger.info(f"LINE 回覆結果：{res.status_code} - {res.text}")

    return "OK"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
from flask import request

@app.route('/send', methods=['GET'])
def send_message():
    user_id = request.args.get("userId")
    message = request.args.get("msg")

    if not user_id or not message:
        return "❌ 請附上 ?userId=...&msg=..."

    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    body = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)
    print(f"🔔 Push message 結果：{res.status_code} - {res.text}", flush=True)
    return f"✅ 已推播：{message} 給 {user_id}"
