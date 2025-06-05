.PHONY: help install dev clean test lint format typecheck run build docker-build docker-run dev-run run-prod run-debug run-console check-env init-db format-check check

# デフォルトターゲット
help:
	@echo "利用可能なコマンド:"
	@echo "  install     - プロダクション依存関係をインストール"
	@echo "  dev         - 開発依存関係を含めてインストール"
	@echo "  clean       - キャッシュファイルとビルド成果物を削除"
	@echo "  test        - テストを実行"
	@echo "  lint        - コードの静的解析を実行"
	@echo "  format      - コードフォーマット・自動修正を実行"
	@echo "  typecheck   - 型チェックを実行"
	@echo "  run         - ボットを実行（.envファイルから環境変数を読み込み）"
	@echo "                コマンドラインオプション: --log-level DEBUG, --console-only など"
	@echo "  build       - プロジェクトをビルド"
	@echo "  docker-build - Dockerイメージをビルド"
	@echo "  docker-run  - Dockerコンテナでボットを実行（.envファイル対応、データ永続化）"
	@echo "  dev-run     - 開発モードでボットを実行（.envファイル対応）"
	@echo "  run-prod    - 本番環境でボットを実行（環境変数チェック付き）"
	@echo "  run-debug   - DEBUGレベルでボットを実行"
	@echo "  run-console - コンソールのみにログ出力でボットを実行"

# 依存関係のインストール
install:
	poetry install --only=main

# 開発環境のセットアップ
dev:
	poetry install

# キャッシュとビルド成果物の削除
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/
	rm -rf build/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -fr .ruff_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf logs/
	rm -rf data/

# テスト実行
test:
	poetry run pytest

# コード品質チェック
lint:
	poetry run ruff check src/
	poetry run mypy src/

# コードフォーマット
format:
	poetry run ruff format src/
	poetry run ruff check --fix src/

# 型チェック
typecheck:
	poetry run mypy src/

# ボット実行（.envファイルから環境変数を読み込み）
run:
	@if [ -f .env ]; then \
		echo ".envファイルから環境変数を読み込み中..."; \
		export $$(grep -v '^#' .env | xargs) && poetry run python -m futaba_search.main; \
	else \
		echo ".envファイルが見つかりません。環境変数を直接設定してください。"; \
		poetry run python -m futaba_search.main; \
	fi

# ログレベル指定で実行（例）
run-debug:
	@if [ -f .env ]; then \
		export $$(grep -v '^#' .env | xargs) && poetry run python -m futaba_search.main --log-level DEBUG; \
	else \
		poetry run python -m futaba_search.main --log-level DEBUG; \
	fi

run-console:
	@if [ -f .env ]; then \
		export $$(grep -v '^#' .env | xargs) && poetry run python -m futaba_search.main --console-only; \
	else \
		poetry run python -m futaba_search.main --console-only; \
	fi

# プロジェクトビルド
build:
	poetry build

# 開発用の便利コマンド
format-check:
	poetry run ruff format --check src/
	poetry run ruff check src/

# 全チェックを実行
check: format-check lint typecheck test

# データベースの初期化（必要に応じて）
init-db:
	@echo "データベースの初期化..."
	@python -c "from src.futaba_search.database import FutabaDatabase; FutabaDatabase()"

# Docker関連
docker-build:
	docker build -t futaba-search .

# Dockerコンテナでボット実行（.envファイルから環境変数を読み込み、データ永続化）
docker-run:
	@mkdir -p data logs
	@if [ -f .env ]; then \
		echo ".envファイルから環境変数を読み込んでDockerコンテナを起動中..."; \
		docker run --rm --env-file .env \
			-v $(PWD)/data:/app/data \
			-v $(PWD)/logs:/app/logs \
			futaba-search; \
	else \
		echo ".envファイルが見つかりません。環境変数DISCORD_TOKENを使用してコンテナを起動中..."; \
		docker run --rm -e DISCORD_TOKEN=$(DISCORD_TOKEN) \
			-v $(PWD)/data:/app/data \
			-v $(PWD)/logs:/app/logs \
			futaba-search; \
	fi

# 環境変数チェック
check-env:
	@if [ -z "$(DISCORD_TOKEN)" ]; then \
		echo "エラー: DISCORD_TOKEN環境変数が設定されていません"; \
		exit 1; \
	fi
	@echo "環境変数チェック完了"

# 本番環境での実行（環境変数チェック付き）
run-prod: check-env
	@if [ -f .env ]; then \
		export $$(grep -v '^#' .env | xargs) && poetry run python -m futaba_search.main; \
	else \
		poetry run python -m futaba_search.main; \
	fi

# 開発サーバー起動（監視付き、.envファイル対応）
dev-run:
	@echo "開発モードでボットを起動中..."
	@echo "Ctrl+Cで停止できます"
	@if [ -f .env ]; then \
		echo ".envファイルから環境変数を読み込み中..."; \
		export $$(grep -v '^#' .env | xargs) && poetry run python -m futaba_search.main --log-level DEBUG; \
	else \
		echo ".envファイルが見つかりません。環境変数を直接設定してください。"; \
		poetry run python -m futaba_search.main; \
	fi