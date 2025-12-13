# Steam プレイログ & 実績集計ツール

このツールは、SteamのWeb APIを使用して、あなたのプレイ時間、所有ゲーム数、そして全ゲームの解除実績総数を集計・表示します。

## 使い方

1. `main.py` を実行します。
2. **Steam API Key** と **Steam ID (64bit)** を入力します。
3. 「データ取得開始」ボタンを押します。

## 必要な情報の取得方法

### 1. Steam API Key の取得
Steamのデータを取得するには、APIキーが必要です（無料）。

1. 以下のURLにアクセスしてください。
   - [https://steamcommunity.com/dev/apikey](https://steamcommunity.com/dev/apikey)
2. Steamアカウントでログインします。
3. 「ドメイン名」の欄には適当な名前（例: `localhost` や `mystatviewer` など）を入力します。
4. チェックボックスに同意して「登録」を押すと、長い文字列（API Key）が表示されます。これをコピーしてツールの入力欄に貼り付けてください。

### 2. Steam ID (64bit) の確認
あなたの固有のSteam ID（数字17桁）が必要です。

1. 以下のURLにアクセスして、アカウント詳細ページを開きます。
   - [https://store.steampowered.com/account/](https://store.steampowered.com/account/)
2. ページ上部の「Steam ID: 7656xxxxxxxxxxxxx」という表示を探してください。この「7656」から始まる数字がSteam IDです。
3. または、プロフィールページのURLが `https://steamcommunity.com/profiles/7656xxxxxxxxxxxxx/` となっている場合、その数字部分がIDです。
   - ※ URLがカスタムURL（例: `.../id/yourname/`）になっている場合は、[SteamID I/O](https://steamid.io/) などの外部サイトで変換して調べることも可能です。

## 注意事項
- プロフィール設定で「ゲームの詳細」が「公開」になっていないと、データを取得できません。Steamのプライバシー設定を確認してください。
