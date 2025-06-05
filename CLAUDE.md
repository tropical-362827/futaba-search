# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

- あなたは日本語で話します。
- コード中のコメントも日本語で書きます。

## プロジェクト概要

ふたば☆ちゃんねるのスレッドをチェックして、指定したキーワードが含まれるスレッドをDiscordに通知するボットです。

## 開発環境セットアップ

```bash
# 開発依存関係を含めてインストール
make dev

# または
poetry install
```

## よく使用するコマンド

### 開発・テスト
```bash
make dev-run      # 開発モード（DEBUGレベルログ、.env読み込み）
make run          # 通常実行（.env読み込み）
make run-debug    # DEBUGレベルで実行
make run-console  # コンソールのみにログ出力

make test         # テスト実行
make lint         # Ruff + mypy静的解析
make format       # Ruffフォーマット・自動修正
make typecheck    # mypy型チェック
make check        # 全品質チェック（format-check + lint + typecheck + test）
```

### Docker
```bash
make docker-build  # Dockerイメージビルド
make docker-run    # Docker実行（.env対応、データ永続化）
```

### クリーンアップ
```bash
make clean  # キャッシュとビルド成果物削除
```

## アーキテクチャ

### 主要コンポーネント

- **main.py**: エントリポイント、コマンドライン引数解析、ログ設定初期化
- **bot.py**: Discord Bot実装、スラッシュコマンド処理、定期監視タスク
- **monitor.py**: ふたば☆ちゃんねるAPI取得、スレッドデータ解析
- **database.py**: SQLAlchemyを使用したデータベース操作（購読、通知履歴、ミュート）
- **config.py**: 環境変数からの設定読み込み
- **logging_config.py**: 統一ログ設定、外部ライブラリのログレベル調整
- **utils.py**: ユーティリティ関数（時間解析、フォーマット）

### データベーススキーマ

SQLAlchemyのDeclarativeBase使用：

- `subscriptions`: チャンネルごとのキーワード購読
- `notified_threads`: 通知済みスレッド追跡（重複防止）
- `muted_channels`: ミュート中のチャンネル

### 定期処理フロー

1. **5分間隔**でふたば☆ちゃんねるAPIからスレッドデータを取得
2. 登録された全購読（チャンネル+キーワード）をループ
3. ミュート中チャンネルをスキップ
4. キーワードマッチング実行
5. 未通知スレッドのみDiscordに通知送信
6. 通知履歴をデータベースに記録
7. 古いレコード（1週間以上）の自動クリーンアップ

### スラッシュコマンド

`/futaba-search` コマンドで以下のアクションを処理：

- `subscribe`: キーワード購読追加
- `unsubscribe`: キーワード購読削除  
- `list`: 登録キーワード一覧表示
- `mute`: 指定時間チャンネルをミュート
- `unmute`: ミュート解除

### ログシステム

- **レベル**: 環境変数`LOG_LEVEL`またはコマンドライン`--log-level`で制御
- **出力先**: コンソール + ログファイル（`--console-only`でコンソールのみ）
- **外部ライブラリ**: discord.py、aiohttpのログレベルを適切に調整
- **DEBUGレベル**: スラッシュコマンドの詳細な分岐ログ、監視処理の詳細

### 環境設定

- **.env**: ローカル開発用（DATABASE_PATHコメントアウト推奨）
- **Docker**: `/app`パス使用、`docker-compose.yml`で永続化
- **設定項目**: DISCORD_TOKEN、LOG_LEVEL、LOG_FILE、DATABASE_PATH、MONITOR_INTERVAL

## 開発時の注意点

### ローカル開発
- .envファイルの`DATABASE_PATH`はコメントアウト（プロジェクトルートに自動作成）
- `make dev-run`でDEBUGレベルログが確認可能

### コード品質
- Ruffによる統一フォーマット・リント（black, isort, flake8を統合）
- mypy型チェック（厳格モード、Union構文は`X | Y`形式使用）
- pytestによる自動テスト

### Docker
- マルチアーキテクチャビルド（AMD64/ARM64）
- GitHub Container Registry（GHCR）へのプッシュ
- Trivyセキュリティスキャン

### CI/CD
- GitHub Actions: テスト、品質チェック、Dockerビルド、リリース自動化
- Dependabot: 週次依存関係更新

## トラブルシューティング

- **PyNaCl警告**: 音声機能未使用のため問題なし
- **型エラー**: SQLAlchemyの新しいDeclarativeBaseでは`# type: ignore`が必要な箇所あり
- **環境変数エラー**: .envファイルのDocker用パス設定をローカル開発時はコメントアウト