import os, json, logging
import logging

from security import checkHMAC
from slack import searchMessages, postMessages


def lambda_handler(event, context):
    # 環境変数定義
    ## Channel ID
    CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")

    ## GitHub WebHookに設定したSecrets
    SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET")

    ## Slack API Token
    SLACK_USER_OAUTH_TOKEN = os.environ.get("SLACK_USER_TOKEN")
    SLACK_BOT_USER_OAUTH_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

    # GitHubからのリクエストかを確認
    if checkHMAC(event, SECRET):
        logging.info("HMAC認証成功")
    else:
        return {"statusCode": 401, "body": "Unauthorized"}

    ## GitHubのWebhookからのデータを取得
    github_event = json.loads(event["body"])

    # 特定のラベルが付与されている場合スキップ
    skip_labels = ["Label-A", "Label-B", "Sandbox"]  # スキップしたいラベルの名前をセット
    labels = github_event["pull_request"]["labels"]
    skip_processing = any(label["name"] in skip_labels for label in labels)
    if skip_processing:
        return {
            "statusCode": 200,
            "body": "Skipped processing for the specified label(s).",
        }

    # actionが"edited"の場合スキップ
    if github_event["action"] == "edited":
        return {
            "statusCode": 200,
            "body": "Skipped processing because the action is 'edited'.",
        }

    # レビュー依頼メッセージを取得
    try:
        thread_ts = searchMessages(github_event, SLACK_USER_OAUTH_TOKEN)
    except Exception as e:
        error_message = f"Error in searchMessages: {str(e)}"
        logging.error(error_message)
        return {"statusCode": 500, "body": error_message}

    # フィードバック結果の送信
    try:
        postMessages(github_event, CHANNEL_ID, SLACK_BOT_USER_OAUTH_TOKEN, thread_ts)
    except Exception as e:
        error_message = f"Error in postMessages: {str(e)}"
        logging.error(error_message)
        return {"statusCode": 500, "body": error_message}

    return {"statusCode": 200, "body": "Success"}
