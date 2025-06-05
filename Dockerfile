# Python 3.11のスリムイメージを使用
FROM python:3.11-slim

# メタデータ
LABEL maintainer="Futaba Search Bot"
LABEL description="Discord bot for monitoring Futaba channel threads"

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージの更新とPoetryのインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        build-essential && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    apt-get purge -y --auto-remove curl build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Poetryのパスを設定
ENV PATH="/root/.local/bin:$PATH"

# Poetryの設定（仮想環境を作成しない）
RUN poetry config virtualenvs.create false

# プロジェクトファイルをコピー
COPY pyproject.toml poetry.lock ./

# 依存関係をインストール（本番環境用）
RUN poetry install --only=main --no-root

# アプリケーションコードをコピー
COPY src/ ./src/

# データベース用のディレクトリを作成
RUN mkdir -p /app/data

# データベースファイルの場所を環境変数で設定
ENV DATABASE_PATH=/app/data/futaba_bot.db

# 非rootユーザーを作成
RUN groupadd -r futaba && useradd -r -g futaba futaba

# データディレクトリの所有者を変更
RUN chown -R futaba:futaba /app/data

# 非rootユーザーに切り替え
USER futaba

# ヘルスチェック用のスクリプト
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('/app/data/futaba_bot.db'); conn.close()" || exit 1

# ボットを実行
CMD ["python", "-m", "src.futaba_search.main"]