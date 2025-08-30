import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import requests

# .env...環境変数を定義するためのテキストファイル。
# override=True：既にOS等で定義済みの環境変数を.envの内容で上書き実行する。
load_dotenv(override=True)

line_bot_api = LineBotApi(os.environ["ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])

app = Flask(__name__)


# セッション管理用の辞書
user_sessions = {}

# 万博公式サイトのURL
EXPO_URL = "https://www.expo2025.or.jp/official-participant/"


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
    user_id = event.source.user_id
    message_text = event.message.text

    # 終了処理
    if message_text == "終わる":
        if user_id in user_sessions:
            del user_sessions[user_id]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="処理を終了しました。"))
        return

    # パビリオン検索開始
    if message_text == "パビリオン":
        user_sessions[user_id] = {"state": "waiting_country"}
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="国名を入力してください。"))
        return

    # セッションが存在しない場合
    if user_id not in user_sessions:
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text="「パビリオン」と入力して検索を開始してください。")
        )
        return

    # 国名入力待ち状態の場合
    if user_sessions[user_id]["state"] == "waiting_country":
        country_name = message_text
        user_sessions[user_id]["country"] = country_name

        # パビリオン情報を検索
        pavilion_info = search_pavilion(country_name)

        if pavilion_info:
            # パビリオンが見つかった場合
            reply_message = f"【{country_name}パビリオン】\n\n{pavilion_info['description']}\n\n詳細は公式サイトをご確認ください。"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))
            # セッションをクリア
            del user_sessions[user_id]
        else:
            # パビリオンが見つからない場合
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="パビリオンが存在しません。再度入力しなおしてください。"),
            )
            # 国名入力状態に戻る
            user_sessions[user_id]["state"] = "waiting_country"


def search_pavilion(country_name):
    """
    万博公式サイトからパビリオン情報を検索する
    """
    try:
        # サイトのHTMLを取得
        response = requests.get(EXPO_URL)
        response.raise_for_status()

        # 国名とパビリオン名のマッピング（簡易版）
        country_pavilion_map = {
            "日本": "日本パビリオン",
            "アメリカ": "アメリカパビリオン",
            "中国": "中国パビリオン",
            "韓国": "韓国パビリオン",
            "フランス": "フランスパビリオン",
            "ドイツ": "ドイツパビリオン",
            "イタリア": "イタリアパビリオン",
            "イギリス": "イギリスポビリオン",
            "カナダ": "カナダパビリオン",
            "オーストラリア": "オーストラリアパビリオン",
            "ブラジル": "ブラジルパビリオン",
            "メキシコ": "メキシコパビリオン",
            "スペイン": "スペインパビリオン",
            "オランダ": "オランダパビリオン",
            "スイス": "スイスパビリオン",
            "スウェーデン": "スウェーデンパビリオン",
            "ノルウェー": "ノルウェーパビリオン",
            "デンマーク": "デンマークパビリオン",
            "フィンランド": "フィンランドパビリオン",
            "ベルギー": "ベルギーパビリオン",
            "ポルトガル": "ポルトガルパビリオン",
            "オーストリア": "オーストリアパビリオン",
            "チェコ": "チェコパビリオン",
            "ポーランド": "ポーランドパビリオン",
            "ハンガリー": "ハンガリーパビリオン",
            "ルーマニア": "ルーマニアパビリオン",
            "ブルガリア": "ブルガリアパビリオン",
            "ギリシャ": "ギリシャパビリオン",
            "トルコ": "トルコパビリオン",
            "イスラエル": "イスラエルパビリオン",
            "エジプト": "エジプトパビリオン",
            "南アフリカ": "南アフリカパビリオン",
            "ナイジェリア": "ナイジェリアパビリオン",
            "ケニア": "ケニアパビリオン",
            "モロッコ": "モロッコパビリオン",
            "チュニジア": "チュニジアパビリオン",
            "インド": "インドパビリオン",
            "パキスタン": "パキスタンパビリオン",
            "バングラデシュ": "バングラデシュパビリオン",
            "スリランカ": "スリランカパビリオン",
            "ネパール": "ネパールパビリオン",
            "タイ": "タイパビリオン",
            "ベトナム": "ベトナムパビリオン",
            "カンボジア": "カンボジアパビリオン",
            "ラオス": "ラオスパビリオン",
            "ミャンマー": "ミャンマーパビリオン",
            "マレーシア": "マレーシアパビリオン",
            "シンガポール": "シンガポールパビリオン",
            "インドネシア": "インドネシアパビリオン",
            "フィリピン": "フィリピンパビリオン",
            "ニュージーランド": "ニュージーランドパビリオン",
            "フィジー": "フィジーパビリオン",
            "パプアニューギニア": "パプアニューギニアパビリオン",
            "チリ": "チリパビリオン",
            "ペルー": "ペルーパビリオン",
            "コロンビア": "コロンビアパビリオン",
            "ベネズエラ": "ベネズエラパビリオン",
            "エクアドル": "エクアドルパビリオン",
            "ボリビア": "ボリビアパビリオン",
            "パラグアイ": "パラグアイパビリオン",
            "ウルグアイ": "ウルグアイパビリオン",
            "アルゼンチン": "アルゼンチンパビリオン",
        }

        # 国名を正規化（部分一致対応）
        normalized_country = None
        for key in country_pavilion_map.keys():
            if country_name in key or key in country_name:
                normalized_country = key
                break

        if normalized_country:
            pavilion_name = country_pavilion_map[normalized_country]
            # 簡易的なパビリオン情報（実際のサイトから取得する場合は、より詳細なスクレイピングが必要）
            description = f"{pavilion_name}は、{normalized_country}の文化、技術、イノベーションを紹介するパビリオンです。"
            return {"description": description}

        return None

    except Exception as e:
        print(f"スクレイピングエラー: {e}")
        return None


# ポート番号の設定
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
