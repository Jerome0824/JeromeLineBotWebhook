from flask import Flask, request
import os
import json
import requests

app = Flask(__name__)

LINE_ACCESS_TOKEN = "HSe3XVIu1uX1L5KKbtGP8YBEHWgLKfGpdFQhYgQtVuLmLwBUTVDMi7/J4YPB8ZejXP0Wxa4m+c/VWX48tzoFcx5k+Wd/iS4uIz71lkPEtG94S7xO92ED6h7a+ZmSEXreduRqiEsmAgnyUu1ukjOqiAdB04t89/1O/w1cDnyilFU="
BOT_USER_ID = "U6b27dfd1fc788e578193c9571b05b41a"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    print("📬 收到 LINE Webhook：", flush=True)
    print(json.dumps(data, indent=2, ensure_ascii=False), flush=True)

    for event in data.get("events", []):
        if event["type"] == "message" and event["message"]["type"] == "text":
            source = event.get("source", {})
            message = event["message"]
            text = message["text"]

            source_type = source.get("type")
            is_group = source_type == "group"
            mentioned = False

            # ✅ 檢查是否被 @
            if "mention" in message:
                for m in message["mention"].get("mentionees", []):
                    if m.get("userId") == BOT_USER_ID:
                        mentioned = True

            if is_group and not mentioned:
                print("👻 在群組中但沒被 tag，略過", flush=True)
                continue

            # ✅ 處理「台股查詢」格式
            reply_token = event["replyToken"]
            if text.startswith("台股") and len(text) >= 6:
                stock_code = text[2:6]
                reply_message = get_taiwan_stock_price(stock_code)
            else:
                reply_message = f"你說的是：「{text}」"

            # ✅ 發送回覆
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
            print(f"🔁 LINE 回覆結果：{res.status_code} - {res.text}", flush=True)

    return "OK"

# ✅ 查詢台股即時價格
def get_taiwan_stock_price(stock_code):
    try:
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{stock_code}.tw"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(url, headers=headers)
        data = res.json()
        stock = data.get("msgArray", [None])[0]

        if stock:
            name = stock.get("n", "未知股票")
            price = stock.get("z", "-")
            time = stock.get("t", "-")
            return f"[{name}({stock_code})] 現價：{price} 元\n時間：{time}"
        else:
            return f"❌ 查無股票代碼 {stock_code} 的即時資料"

    except Exception as e:
        print("❗ 查詢發生錯誤：", e, flush=True)
        return "❌ 無法取得股價資料，請稍後再試"

# ✅ 主動推播 API：GET /send?userId=xxx&msg=hello
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

# ✅ 埠口設定（Render 專用）
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
