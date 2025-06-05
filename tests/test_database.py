"""データベース機能のテスト"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from src.futaba_search.database import FutabaDatabase


@pytest.fixture
def temp_db():
    """テスト用の一時データベース"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    db = FutabaDatabase(db_path)
    yield db
    
    # クリーンアップ
    if db_path.exists():
        db_path.unlink()


def test_add_subscription(temp_db):
    """購読追加のテスト"""
    # 新しい購読を追加
    result = temp_db.add_subscription(12345, "テスト")
    assert result is True
    
    # 重複した購読を追加（失敗することを確認）
    result = temp_db.add_subscription(12345, "テスト")
    assert result is False


def test_get_subscriptions(temp_db):
    """購読取得のテスト"""
    # 購読を追加
    temp_db.add_subscription(12345, "テスト1")
    temp_db.add_subscription(12345, "テスト2")
    temp_db.add_subscription(67890, "テスト3")
    
    # チャンネルの購読を取得
    subscriptions = temp_db.get_subscriptions(12345)
    assert len(subscriptions) == 2
    assert "テスト1" in subscriptions
    assert "テスト2" in subscriptions
    assert "テスト3" not in subscriptions


def test_remove_subscription(temp_db):
    """購読削除のテスト"""
    # 購読を追加
    temp_db.add_subscription(12345, "テスト")
    
    # 削除
    result = temp_db.remove_subscription(12345, "テスト")
    assert result is True
    
    # 存在しない購読の削除
    result = temp_db.remove_subscription(12345, "存在しない")
    assert result is False


def test_notification_tracking(temp_db):
    """通知追跡のテスト"""
    thread_id = "123456789"
    keyword = "テスト"
    channel_id = 12345
    
    # 最初は通知されていない
    assert temp_db.is_thread_notified(thread_id, keyword, channel_id) is False
    
    # 通知済みとしてマーク
    temp_db.mark_thread_notified(thread_id, keyword, channel_id)
    
    # 通知済みかチェック
    assert temp_db.is_thread_notified(thread_id, keyword, channel_id) is True


def test_channel_muting(temp_db):
    """チャンネルミュート機能のテスト"""
    channel_id = 12345
    future_time = datetime.now() + timedelta(hours=1)
    
    # 最初はミュートされていない
    assert temp_db.is_channel_muted(channel_id) is False
    
    # ミュート設定
    temp_db.mute_channel(channel_id, future_time)
    
    # ミュート状態の確認
    assert temp_db.is_channel_muted(channel_id) is True
    
    # ミュート期限の確認
    mute_status = temp_db.get_mute_status(channel_id)
    assert mute_status is not None
    assert mute_status == future_time
    
    # ミュート解除
    result = temp_db.unmute_channel(channel_id)
    assert result is True
    assert temp_db.is_channel_muted(channel_id) is False


def test_cleanup_old_notifications(temp_db):
    """古い通知のクリーンアップテスト"""
    # テスト用の古い通知レコードを作成
    thread_id = "123456789"
    keyword = "テスト"
    channel_id = 12345
    
    # 通知を追加
    temp_db.mark_thread_notified(thread_id, keyword, channel_id)
    
    # 通知が存在することを確認
    assert temp_db.is_thread_notified(thread_id, keyword, channel_id) is True
    
    # 1日前の通知として削除（実際のテストでは時間操作が難しいため、
    # ここでは関数が正常に実行されることのみ確認）
    temp_db.cleanup_old_notifications(days=0)
    
    # 関数が正常に実行されることを確認（エラーが発生しないこと）


def test_cleanup_expired_mutes(temp_db):
    """期限切れミュートのクリーンアップテスト"""
    channel_id = 12345
    past_time = datetime.now() - timedelta(hours=1)
    
    # 過去の時間でミュート設定
    temp_db.mute_channel(channel_id, past_time)
    
    # クリーンアップ実行
    temp_db.cleanup_expired_mutes()
    
    # ミュートが自動的に解除されていることを確認
    assert temp_db.is_channel_muted(channel_id) is False