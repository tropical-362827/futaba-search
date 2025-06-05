"""ふたば検索ボットのメインエントリポイント"""

import argparse
import sys

from .bot import run_bot
from .config import LOG_FILE, LOG_LEVEL
from .logging_config import setup_logging


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(
        description="ふたば☆ちゃんねるのスレッドを監視してDiscordに通知するボット",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""例:
  %(prog)s                          # デフォルト設定で実行
  %(prog)s --log-level DEBUG        # DEBUGレベルで実行
  %(prog)s --log-file /tmp/bot.log  # ログファイルを指定
  %(prog)s --console-only           # コンソールのみに出力
""",
    )

    parser.add_argument(
        "--log-level",
        default=LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=f"ログレベルを指定 (デフォルト: {LOG_LEVEL})",
    )

    parser.add_argument(
        "--log-file",
        default=LOG_FILE,
        help=f"ログファイルのパスを指定 (デフォルト: {LOG_FILE})",
    )

    parser.add_argument(
        "--console-only",
        action="store_true",
        help="コンソールのみにログを出力（ファイルには出力しない）",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="futaba-search 1.0.0",
        help="バージョン情報を表示",
    )

    return parser.parse_args()


def main() -> None:
    """メインエントリポイント"""
    try:
        args = parse_args()

        # ログ設定を初期化
        log_file = None if args.console_only else args.log_file
        setup_logging(level=args.log_level, log_file=log_file)

        # ボットを実行
        run_bot()

    except KeyboardInterrupt:
        print("\nボットを停止しました。")
        sys.exit(0)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
