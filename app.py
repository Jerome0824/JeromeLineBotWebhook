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

    # 🔕 已停用群組 @ 標記與文字指令處理邏輯
    return "OK"

# ✅ 查詢台股 / 上正股票（保留，可視未來需求啟用）
def get_stock_info(stock_code):
    try:
        def fetch(market):
            url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={market}_{stock_code}.tw"
            headers = {
                "User-Agent": "Mozilla/5.0"
            }
            res = requests.get(url, headers=headers)
            print(f"📱 嘗試查詢：{url}", flush=True)
            data = res.json()
            msg_array = data.get("msgArray", [])
            if not msg_array:
                return None
            stock = msg_array[0]
            return stock if stock.get("n") and stock.get("c") else None

        stock = fetch("tse")
        if not stock or stock.get("z") in ["-", "", None]:
            stock = fetch("otc")

        if not stock:
            return f"❌ 找不到代碼 {stock_code} 的即時股價資料"

        name = stock.get("n", "未知股票")
        z = stock.get("z", "-")
        y = stock.get("y", "-")
        o = stock.get("o", "-")
        h = stock.get("h", "-")
        l = stock.get("l", "-")
        c = stock.get("c", stock_code)
        t = stock.get("t", "-")

        if z in ["-", "", None]:
            return (
                f"[{name}({c})] 尚無即時成交價（可能已收盤）\n"
                f"🕐 時間：{t}\n"
                f"📊 開盤：{o} / 高：{h} / 低：{l} / 昨收：{y}"
            )

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

# ✅ 主動推播（支援 GET & POST）
@app.route('/send', methods=['GET', 'POST'])
def send_message():
    if request.method == 'GET':
        user_id = request.args.get("userId")
        message = request.args.get("msg")
    else:
        data = request.get_json()
        user_id = data.get("userId")
        message = data.get("msg")

    if not user_id or not message:
        return "❌ 請附上 userId 和 msg"

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

# ✅ 防止 Render 休眠
@app.route('/ping')
def ping():
    return "pong", 200

# ✅ 查詢 LINE 剩餘推播配題
@app.route('/quota')
def quota():
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    res = requests.get("https://api.line.me/v2/bot/message/quota/consumption", headers=headers)
    print(f"📊 查詢 quota 結果：{res.status_code} - {res.text}", flush=True)
    return res.text, res.status_code

# ✅ Render 埠口
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
