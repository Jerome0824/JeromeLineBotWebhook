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

            # ✅ 檢查是否被 @ 並移除 mention 字串
            mention = message.get("mention")
            if mention:
                for m in mention.get("mentionees", []):
                    if m.get("userId") == BOT_USER_ID:
                        mentioned = True
                        mention_text = text[m.get("index"): m.get("index") + m.get("length")]
                        text = text.replace(mention_text, "").strip()


            # ✅ 在群組中但沒被 tag，略過
            if is_group and not mentioned:
                print("👻 群組中未被 tag，略過", flush=True)
                continue

            reply_token = event["replyToken"]

            # ✅ 偵測股票指令
            stock_code = None
            is_otc = False
            if text.startswith("台股") and len(text) >= 6:
                stock_code = text[2:6]
            elif text.startswith("上櫃") and len(text) >= 6:
                stock_code = text[2:6]
                is_otc = True

            if stock_code:
                reply_message = get_stock_info(stock_code, is_otc)
            else:
                reply_message = f"你說的是：「{text}」"

            print("📝 回應內容：", reply_message, flush=True)

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

# ✅ 查詢台股 / 上櫃股票
def get_stock_info(stock_code, is_otc=False):
    try:
        market = "otc" if is_otc else "tse"
        url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={market}_{stock_code}.tw"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        res = requests.get(url, headers=headers)
        data = res.json()
        msg_array = data.get("msgArray", [])

        if not msg_array:
            return f"❌ 找不到代碼 {stock_code} 的即時股價資料"

        stock = msg_array[0]
        name = stock.get("n", "未知股票")
        z = stock.get("z", "-")  # 現價
        y = stock.get("y", "-")  # 昨收
        o = stock.get("o", "-")  # 開盤
        h = stock.get("h", "-")  # 最高
        l = stock.get("l", "-")  # 最低
        c = stock.get("c", stock_code)  # 股票代碼
        t = stock.get("t", "-")  # 時間

        # 漲跌與漲幅計算
        try:
            change = round(float(z) - float(y), 2)
            percent = round((change / float(y)) * 100, 2)
            sign = "▲" if change > 0 else ("▼" if change < 0 else "")
            change_str = f"{sign}{abs(change)} ({percent}%)"
        except:
            change_str = "N/A"

        return (
            f"[{name}({c})] {t}\n"
            f"💰 現價：{z} 元\n"
            f"📈 漲跌：{change_str}\n"
            f"📊 開盤：{o} / 高：{h} / 低：{l} / 昨收：{y}"
        )

    except Exception as e:
        print("❗ 查詢錯誤：", e, flush=True)
        return "❌ 查詢股價失敗，請稍後再試"

# ✅ 主動推播
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

# ✅ Render 埠口
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
