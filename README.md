## 環境変数の設定
### Lambda

Lambda の環境変数に以下を設定してください。

| 変数名 | 説明 | 必要なスコープ |
|--------|------|---------------|
| `SLACK_CHANNEL_ID` | 通知先のSlackチャンネルID | - |
| `Secrets` | GitHub Webhook の Secret | - |
| `UserOAuthToken` | Slack User OAuth Token | `search:read` |
| `BotUserOAuthToken` | Slack Bot User OAuth Token | `chat:write`, `reactions:write` |

## デプロイ方法

1. Lambda 関数を作成
2. 上記環境変数を設定
3. GitHub Webhook の URL に Lambda の Function URL を指定
4. Events: `Pull request reviews` を有効化

## GitHub Secrets の設定

リポジトリの Settings → Secrets and variables → Actions から、以下のSecretsを追加してください。

| Secret名 | 説明 | 
|----------|------| 
| `SLACK_BOT_TOKEN` | Slack Bot Token | 
| `SLACK_CHANNEL_ID` | 通知先チャンネルID | 
| `SLACK_GROUP_ID` | メンション先のUser Group ID | 

## 使い方

1. PRのコメント欄で `/review` とコメント
2. CIが全て成功していれば、Slackに通知が飛びます
3. 特定の人にもCCしたい場合: `/review <@U01234ABCDE> 追加メッセージ`
