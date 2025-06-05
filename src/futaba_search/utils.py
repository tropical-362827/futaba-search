"""ふたば検索ボットのユーティリティ関数"""

import re
from datetime import datetime, timedelta


def parse_time_interval(interval: str) -> timedelta | None:
    """
    '30m', '1h', '2d'のような時間間隔文字列をtimedeltaに解析。

    サポートされている形式:
    - m, min, minutes: 分
    - h, hour, hours: 時間
    - d, day, days: 日
    """
    if not interval:
        return None

    # スペースを削除して小文字に変換
    interval = interval.strip().lower()

    # 数値の後に時間単位が続くパターンをマッチ
    match = re.match(r"^(\d+)\s*(m|min|minutes?|h|hour|hours?|d|day|days?)$", interval)
    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)

    if unit in ("m", "min", "minute", "minutes"):
        return timedelta(minutes=value)
    elif unit in ("h", "hour", "hours"):
        return timedelta(hours=value)
    elif unit in ("d", "day", "days"):
        return timedelta(days=value)

    return None


def format_datetime(dt: datetime) -> str:
    """ユーザーフレンドリーな表示のために日時をフォーマット"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_mute_until_datetime(interval: str) -> datetime | None:
    """間隔に基づいてミュートが期限切れになる日時を取得"""
    delta = parse_time_interval(interval)
    if delta:
        return datetime.now() + delta
    return None
