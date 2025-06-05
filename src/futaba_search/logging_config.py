"""ロギング設定モジュール"""

import logging
import sys
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: str | None = None,
    format_string: str | None = None,
) -> None:
    """
    アプリケーション全体のロギングを設定

    Args:
        level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: ログファイルのパス（Noneの場合はコンソールのみ）
        format_string: ログフォーマット文字列
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # ログレベルを設定
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 既存のハンドラーをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # フォーマッターを作成
    formatter = logging.Formatter(format_string)

    # コンソールハンドラーを設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # ファイルハンドラーを設定（指定された場合）
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # discord.pyのログレベルを調整（通常は少し高めに設定）
    discord_logger = logging.getLogger("discord")
    if numeric_level <= logging.DEBUG:
        discord_logger.setLevel(logging.DEBUG)
    elif numeric_level <= logging.INFO:
        discord_logger.setLevel(logging.INFO)
    else:
        discord_logger.setLevel(logging.WARNING)

    # aiohttp のログレベルを調整
    aiohttp_logger = logging.getLogger("aiohttp")
    if numeric_level <= logging.DEBUG:
        aiohttp_logger.setLevel(logging.INFO)
    else:
        aiohttp_logger.setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    指定された名前のロガーを取得

    Args:
        name: ロガー名（通常は __name__ を指定）

    Returns:
        設定済みのロガーインスタンス
    """
    return logging.getLogger(name)
