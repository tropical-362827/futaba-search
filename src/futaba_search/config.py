"""ふたば検索ボットの設定"""

import os
from pathlib import Path

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
FUTABA_API_URL = os.getenv(
    "FUTABA_API_URL", "https://may.2chan.net/b/futaba.php?mode=json"
)
MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "60"))  # 1 minutes in seconds

# ログ設定
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE")  # ログファイルパス（指定されない場合はコンソールのみ）

# プロジェクトルートパスを取得
PROJECT_ROOT = Path(__file__).parent.parent.parent

# データベースパス - 環境変数から取得、なければプロジェクトルートに作成
DATABASE_PATH_ENV = os.getenv("DATABASE_PATH")
if DATABASE_PATH_ENV:
    DATABASE_PATH = Path(DATABASE_PATH_ENV)
else:
    DATABASE_PATH = PROJECT_ROOT / "futaba_bot.db"

# ログファイルのデフォルトパス設定（環境変数で指定されない場合）
if not LOG_FILE:
    LOGS_DIR = PROJECT_ROOT / "logs"
    LOGS_DIR.mkdir(exist_ok=True)
    LOG_FILE = str(LOGS_DIR / "futaba_search.log")
