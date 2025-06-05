"""ユーティリティ関数のテスト"""

import pytest
from datetime import datetime, timedelta

from src.futaba_search.utils import (
    parse_time_interval,
    format_datetime,
    get_mute_until_datetime
)


def test_parse_time_interval():
    """時間間隔解析のテスト"""
    # 分の解析
    assert parse_time_interval("30m") == timedelta(minutes=30)
    assert parse_time_interval("45min") == timedelta(minutes=45)
    assert parse_time_interval("60minutes") == timedelta(minutes=60)
    
    # 時間の解析
    assert parse_time_interval("2h") == timedelta(hours=2)
    assert parse_time_interval("3hour") == timedelta(hours=3)
    assert parse_time_interval("24hours") == timedelta(hours=24)
    
    # 日の解析
    assert parse_time_interval("1d") == timedelta(days=1)
    assert parse_time_interval("7day") == timedelta(days=7)
    assert parse_time_interval("30days") == timedelta(days=30)
    
    # 無効な形式
    assert parse_time_interval("invalid") is None
    assert parse_time_interval("") is None
    assert parse_time_interval("30x") is None


def test_format_datetime():
    """日時フォーマットのテスト"""
    dt = datetime(2023, 12, 25, 15, 30, 45)
    formatted = format_datetime(dt)
    assert formatted == "2023-12-25 15:30:45"


def test_get_mute_until_datetime():
    """ミュート期限日時取得のテスト"""
    # 有効な間隔
    before = datetime.now()
    result = get_mute_until_datetime("30m")
    after = datetime.now()
    
    assert result is not None
    assert before + timedelta(minutes=30) <= result <= after + timedelta(minutes=30)
    
    # 無効な間隔
    assert get_mute_until_datetime("invalid") is None
    assert get_mute_until_datetime("") is None


def test_parse_time_interval_case_insensitive():
    """大文字小文字を区別しない解析のテスト"""
    assert parse_time_interval("30M") == timedelta(minutes=30)
    assert parse_time_interval("2H") == timedelta(hours=2)
    assert parse_time_interval("1D") == timedelta(days=1)


def test_parse_time_interval_with_spaces():
    """スペースを含む時間間隔のテスト"""
    assert parse_time_interval(" 30m ") == timedelta(minutes=30)
    assert parse_time_interval("  2h  ") == timedelta(hours=2)
    assert parse_time_interval("\t1d\n") == timedelta(days=1)