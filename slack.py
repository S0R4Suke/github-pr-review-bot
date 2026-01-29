import os, json, urllib, logging
import urllib.request
import urllib.parse

# postメソッド
def postSlack(api_url, params):
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(api_url, data=data, method="POST")

    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))

    if data["ok"]:
        logging.info("Successfully posted to Slack.")
    else:
        logging.error(f"Error: {data['error']}")


# レビュー依頼メッセージの検索
def searchMessages(event, SLACK_USER_OAUTH_TOKEN):
    api_url = "https://slack.com/api/search.messages"
    search_query = (
        event["pull_request"]["html_url"] + " in:#CHANNEL_NAME"
    )

    params = {
        "query": search_query,
        "count": 1,
        "sort": "timestamp",
        "search_exclude_bots": False,  # ボットのメッセージを除外
    }

    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(api_url, data)

    req.add_header("Authorization", f"Bearer {SLACK_USER_OAUTH_TOKEN}")
    # Slack APIにGETリクエストを送信
    with urllib.request.urlopen(req) as response:
        slack_logs = json.loads(response.read().decode("utf-8"))

    # メッセージを出力
    if slack_logs["ok"]:
        messages = slack_logs["messages"]["matches"]
        if messages:
            logging.info("Matching message found.")
            return messages[0]["ts"]
        else:
            logging.warn("No matching message found:" + search_query)
            return None  # メッセージが見つからなかった場合はNoneを返す
    else:
        logging.error(f"Error: {slack_logs['error']}")
        return None  # エラーが発生した場合もNoneを返す

def getApprovalCountFromSlack(SLACK_BOT_USER_OAUTH_TOKEN, CHANNEL_ID, thread_ts):
    # Slackスレッド内の「Approveされました！」メッセージをカウント
    api_url = f"https://slack.com/api/conversations.replies?channel={CHANNEL_ID}&ts={thread_ts}"
    
    headers = {"Authorization": f"Bearer {SLACK_BOT_USER_OAUTH_TOKEN}"}
    req = urllib.request.Request(api_url, headers=headers)
    
    try:
        response = urllib.request.urlopen(req, timeout=10)
        
        if response.getcode() == 200:
            data = json.loads(response.read().decode("utf-8"))
            messages = data.get("messages", [])[1:]
            
            return sum(1 for msg in messages 
                    if "Approveされました！" in msg.get("text", ""))
    except Exception as e:
        logging.error(f"Failed to get approval count: {str(e)}")
    
    return 0

# リアクション付与
def addReaction(SLACK_BOT_USER_OAUTH_TOKEN, CHANNEL_ID, thread_ts):
    api_url = "https://slack.com/api/reactions.add"

    # 追加するリアクション:✅
    reaction = "white_check_mark"

    # Slack APIリクエストボディ
    params = {
        "token": SLACK_BOT_USER_OAUTH_TOKEN,
        "channel": CHANNEL_ID,
        "timestamp": thread_ts,
        "name": reaction,
    }
    postSlack(api_url, params)

# メッセージの投稿
def postMessages(
    event,
    CHANNEL_ID,
    SLACK_BOT_USER_OAUTH_TOKEN,
    thread_ts,
):
    # Slack APIエンドポイントを定義
    api_url = "https://slack.com/api/chat.postMessage"
    # PR作成者を格納
    author = event["pull_request"]["user"]["login"]

    # スレッドメッセージのテキスト、Slack APIにPOSTリクエストを送信する際のパラメータを設定
    if event["review"]["state"] == "approved":
        message_text = f"{author}さんへの通知: Approveされました！"

    elif event["review"]["state"] == "commented":
        message_text = f"<{event['review']['html_url']} | {author}さんへの通知: PRにコメントがされました！>"

    elif event["review"]["state"] == "changes_requested":
        message_text = f"<{event['review']['html_url']} | {author}さんへの通知: PRにコードの修正依頼が届きました！>"

    else:
        logging.warn("Unknown review state.")
        return None

    # Slack APIにPOSTリクエストを送信する際のパラメータを設定
    params = {
        "token": SLACK_BOT_USER_OAUTH_TOKEN,
        "channel": CHANNEL_ID,
        "text": message_text,
        "thread_ts": thread_ts,
    }

    postSlack(api_url, params)

    # メッセージ送信後、approvedの場合だけカウント&リアクション
    if event["review"]["state"] == "approved":
        approval_count = getApprovalCountFromSlack(SLACK_BOT_USER_OAUTH_TOKEN, CHANNEL_ID, thread_ts)
        if approval_count >= 2:
            addReaction(SLACK_BOT_USER_OAUTH_TOKEN, CHANNEL_ID, thread_ts)
