import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

# .env...環境変数を定義するためのテキストファイル。
# override=True：既にOS等で定義済みの環境変数を.envの内容で上書き実行する。
load_dotenv(override=True)

line_bot_api = LineBotApi(os.environ["ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

app = Flask(__name__)


# /にアクセスでメッセージを返す
@app.route("/")
def index():
    return "You call index()"


@app.route("/callback", methods=["POST"])
def callback():
    """Messaging APIからの呼び出し関数 ラインから来た処理なのかを確認する"""
    # LINEがリクエストの改ざんを防ぐために付与する署名を取得
    signature = request.headers["X-Line-Signature"]
    # リクエストの内容をテキストで取得
    body = request.get_data(as_text=True)
    # ログに出力
    app.logger.info("Request body:" + body)

    try:
        # signature と body を比較することで、リクエストがLINEから送信されたものであることを検証
        # エラーとなり得る処理を書く
        handler.handle(body, signature)
    except InvalidSignatureError:
        # クライアントからのリクエストに誤りがあったことを示すエラーを返す
        # エラーがでた場合の処理を記述する
        abort(400)

    return "OK"


# WebhookHandlerでリクエストを受け取ってhandle_message関数で受け取ったメッセージをそのまま返信
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if "ばか" in TextMessage:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="今バカって言いました？"))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=event.message.text))


# ポート番号の設定
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
