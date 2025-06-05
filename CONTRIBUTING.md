# コントリビューションガイド

このプロジェクトへの貢献方法について説明します。

## 開発環境のセットアップ

### 要件

- Python 3.11+
- Poetry

または

- Docker & Docker Compose

### セットアップ手順

1. リポジトリをクローン:
```bash
git clone https://github.com/tropical-362827/futaba-search.git
cd futaba-search
```

2. Poetry環境をセットアップ:
```bash
# 依存関係をインストール
poetry install

# 仮想環境をアクティベート
poetry shell
```

3. 環境変数を設定:
```bash
cp .env.example .env
# .envファイルでDISCORD_TOKENを設定
```

## 開発ワークフロー

### 依存関係の管理

```bash
# 依存関係の追加
poetry add package_name

# 開発用依存関係の追加
poetry add --group dev package_name
```

### コード品質管理

```bash
# フォーマット
poetry run ruff format src/

# リント
poetry run ruff check src/

# 自動修正
poetry run ruff check --fix src/

# 型チェック
poetry run mypy src/
```

### テスト

```bash
# テスト実行
poetry run pytest

# カバレッジ付きテスト
poetry run pytest --cov=src --cov-report=html
```

### Makefileコマンド

便利なMakefileコマンドが用意されています：

```bash
# 開発環境のセットアップ
make dev

# 全品質チェック
make check

# コードフォーマット・自動修正
make format

# テスト実行
make test

# リント実行
make lint

# 型チェック
make typecheck

# ボット実行
make run

# クリーンアップ
make clean
```

## プロジェクト構成

```
src/futaba_search/
├── __init__.py           # パッケージ初期化
├── main.py              # エントリーポイント
├── bot.py               # Discordボット実装
├── config.py            # 設定管理
├── database.py          # SQLiteデータベース管理（SQLAlchemy）
├── monitor.py           # ふたば☆ちゃんねる監視機能
└── utils.py             # ユーティリティ関数

tests/
├── __init__.py
├── test_database.py     # データベース機能のテスト
└── test_utils.py        # ユーティリティ関数のテスト

.github/workflows/
├── ci.yml               # 継続的インテグレーション
├── docker.yml           # Dockerイメージビルド
└── release.yml          # リリース自動化
```

## CI/CD

このプロジェクトはGitHub Actionsを使用した自動化されたCI/CDパイプラインを備えています：

### 継続的インテグレーション (CI)
- **テスト**: Python 3.11と3.12でのユニットテスト実行
- **コード品質**: Ruff（フォーマット・リント・インポート順序）、mypy（型チェック）
- **セキュリティ**: safety（脆弱性チェック）、bandit（セキュリティリンター）
- **カバレッジ**: Codecovでのコードカバレッジ測定

### 継続的デプロイメント (CD)
- **Dockerイメージ**: mainブランチへのプッシュ時に自動ビルド・プッシュ
- **マルチアーキテクチャ**: AMD64とARM64両対応
- **セキュリティスキャン**: Trivyによる脆弱性スキャン
- **リリース**: タグプッシュ時の自動リリース作成

### 依存関係管理
- **Dependabot**: 週次での依存関係更新チェック
- **Python、Docker、GitHub Actions**の依存関係を自動更新

## コントリビューション方法

### プルリクエストを送る前に

1. **ブランチを作成**:
```bash
git checkout -b feature/your-feature-name
```

2. **品質チェックを実行**:
```bash
make check
```

3. **テストが通ることを確認**:
```bash
make test
```

4. **コミットメッセージの規約**:
```
feat: 新機能を追加
fix: バグ修正
docs: ドキュメント更新
style: コードスタイル修正
refactor: リファクタリング
test: テスト追加・修正
chore: その他の変更
```

### プルリクエストのガイドライン

- **明確なタイトル**と**説明**を記載
- **関連するIssue**があれば参照
- **テストケース**を追加（新機能の場合）
- **破壊的変更**がある場合は明記

## アーキテクチャ

### データベース設計

SQLAlchemyを使用したSQLiteデータベース：

- `subscriptions`: チャンネルごとのキーワード購読
- `notified_threads`: 通知済みスレッド追跡
- `muted_channels`: ミュート中のチャンネル

### 監視システム

- **5分間隔**でふたば☆ちゃんねるAPIを監視
- **キーワードマッチング**でスレッドを検出
- **重複通知防止**機能
- **古いレコードの自動削除**（1週間以上前）

## トラブルシューティング

### 開発環境の問題

1. **Poetry環境の問題**:
```bash
poetry env remove python
poetry install
```

2. **依存関係の問題**:
```bash
poetry lock --no-update
poetry install
```

3. **テストの失敗**:
```bash
# テスト環境をクリーン
rm -rf .pytest_cache
poetry run pytest -v
```

### Docker環境の問題

1. **イメージの再ビルド**:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

2. **ログの確認**:
```bash
docker-compose logs -f futaba-search
```

## セキュリティ

- **Discord Token**は絶対にコミットしない
- **環境変数**または**Docker secrets**で機密情報を管理
- **依存関係の脆弱性**は定期的にチェック
- **セキュリティ関連の問題**は非公開で報告

## ライセンス

このプロジェクトへの貢献は、プロジェクトと同じライセンスの下でライセンスされます。