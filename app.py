from flask import Flask, request
import os
import json
import requests

app = Flask(__name__)

LINE_ACCESS_TOKEN = "<<<請填入你的 Channel Access Token>>>"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    app.logger.info("📬 收到 LINE Webhook：\n" + json.dumps(data, indent=2, ensure_ascii=False))

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
