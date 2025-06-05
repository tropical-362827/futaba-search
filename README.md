# ふたばスレッド検索 Discord Bot

ふたば☆ちゃんねるのスレッド一覧を監視し、指定したキーワードを含むスレッドが新たに見つかったときにDiscordに通知するボットです。

## 機能

- **キーワード監視**: 登録したキーワードを含むスレッドを5分間隔で監視
- **Discord通知**: マッチしたスレッドを埋め込み形式(ふたばフォレスト、FTBucketのリンク含む)で通知
- **重複防止**: 一度通知されたスレッドは再通知されません
- **チャンネル別管理**: Discord チャンネルごとに独立したキーワード設定
- **一時ミュート**: 指定時間だけ通知を停止可能

## インストール方法

### Option 1: Docker Compose を使用（推奨）

1. **リポジトリをクローン**:

```bash
git clone https://github.com/tropical-362827/futaba-search.git
cd futaba-search
```

2. **環境変数ファイルを作成**:
```bash
cp .env.example .env
```

3. **Discord Bot トークンを設定**:
`.env` ファイルを編集:
```env
DISCORD_TOKEN=your_discord_bot_token_here
```

4. **データディレクトリを作成**:
```bash
mkdir -p data logs
```

5. **ボットを起動**:
```bash
docker-compose up -d
```

6. **ログを確認** (オプション):
```bash
docker-compose logs -f futaba-search
```

### Option 2: Python環境を使用

1. **要件**: Python 3.11+ と Poetry

2. **セットアップ**:
```bash
git clone https://github.com/tropical-362827/futaba-search.git
cd futaba-search
poetry install
```

3. **環境変数を設定**:
```bash
export DISCORD_TOKEN="your_discord_bot_token_here"
```

4. **ボットを実行**:
```bash
poetry run futaba-search
```

## Discord Bot 設定

### 1. Bot トークンの取得

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. **"New Application"** → アプリケーション名を入力 → **"Create"**
3. 左メニューから **"Bot"** → **"Add Bot"** → **"Yes, do it!"**
4. **"Token"** セクションで **"Reset Token"** → トークンをコピー

### 2. Bot 権限の設定

#### OAuth2 設定
- **Scopes**: `bot` と `applications.commands` を選択

#### Bot Permissions
| 権限 | 用途 | 重要度 |
|------|------|--------|
| **Send Messages** | キーワード通知の送信 | 必須 ✅ |
| **Use Slash Commands** | `/futaba-search` コマンドの使用 | 必須 ✅ |
| **Embed Links** | 美しい埋め込み形式での通知表示 | 推奨 ⚠️ |
| **Attach Files** | ふたばスレッドのサムネイル画像表示 | 推奨 ⚠️ |

### 3. Bot をサーバーに招待

1. Discord Developer Portal の **"OAuth2"** → **"URL Generator"**
2. 上記の権限を選択してURLを生成
3. 生成されたURLでBotをサーバーに招待

## 使用方法

### スラッシュコマンド

Discord で `/futaba-search` と入力すると利用できるコマンド：

| コマンド | 説明 | 例 |
|----------|------|-----|
| `/futaba-search subscribe keyword:{keyword}` | キーワード通知を登録 | `/futaba-search subscribe keyword:東方` |
| `/futaba-search unsubscribe keyword:{keyword}` | キーワード通知を解除 | `/futaba-search unsubscribe keyword:東方` |
| `/futaba-search list` | 登録中のキーワード一覧を表示 | `/futaba-search list` |
| `/futaba-search mute interval:{time}` | 指定時間、通知をミュート | `/futaba-search mute interval:1h` |
| `/futaba-search unmute` | ミュートを解除 | `/futaba-search unmute` |

### 時間指定の形式

- `30m` または `30minutes` - 30分
- `2h` または `2hours` - 2時間  
- `1d` または `1day` - 1日

## よくある質問

### Q: Botが反応しない
A: 以下を確認してください：
- Discord Token が正しく設定されているか
- Bot に必要な権限が付与されているか
- Bot がサーバーに招待されているか

### Q: 通知が来ない
A: 以下を確認してください：
- キーワードが正しく登録されているか (`/futaba-search list` で確認)
- チャンネルがミュートされていないか
- ふたば☆ちゃんねるにマッチするスレッドが実際に投稿されているか

### Q: 通知を止めたい
A: 一時的に止める場合は `/futaba-search mute interval:1h` を使用
完全に止める場合は `/futaba-search unsubscribe keyword:キーワード` でキーワードを削除

## サポート・貢献

- **Issues**: バグ報告や機能要求は [GitHub Issues](https://github.com/tropical-362827/futaba-search/issues)
- **開発者向け情報**: [CONTRIBUTING.md](CONTRIBUTING.md) を参照
- **ライセンス**: MIT License

---

**注意**: このボットはふたば☆ちゃんねるの非公式ツールです。節度を持って使用してください。