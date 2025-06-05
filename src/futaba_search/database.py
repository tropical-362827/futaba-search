"""ふたば検索ボットのデータベース管理"""

from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import DATABASE_PATH
from .logging_config import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemyのベースクラス"""

    pass


class Subscription(Base):
    """チャンネルごとのキーワード購読を保存するモデル"""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer, nullable=False)
    keyword = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint("channel_id", "keyword"),)


class NotifiedThread(Base):
    """通知済みスレッドを追跡するモデル"""

    __tablename__ = "notified_threads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String, nullable=False)
    keyword = Column(String, nullable=False)
    channel_id = Column(Integer, nullable=False)
    notified_at = Column(DateTime, default=datetime.now)

    __table_args__ = (UniqueConstraint("thread_id", "keyword", "channel_id"),)


class MutedChannel(Base):
    """ミュート中のチャンネルを追跡するモデル"""

    __tablename__ = "muted_channels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(Integer, nullable=False, unique=True)
    muted_until = Column(DateTime, nullable=False)
    muted_at = Column(DateTime, default=datetime.now)


class FutabaDatabase:
    """購読情報と通知履歴を保存するSQLiteデータベースを管理"""

    def __init__(self, db_path: Path = DATABASE_PATH) -> None:
        self.db_path = db_path
        self.init_database()

    def init_database(self) -> None:
        """必要なテーブルでデータベースを初期化"""
        # ディレクトリが存在することを確認
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # SQLAlchemyエンジンとセッションを作成
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def _get_session(self) -> Session:
        """新しいデータベースセッションを取得"""
        return self.Session()

    def add_subscription(self, channel_id: int, keyword: str) -> bool:
        """チャンネルに新しいキーワード購読を追加"""
        try:
            with self._get_session() as session:
                subscription = Subscription(channel_id=channel_id, keyword=keyword)
                session.add(subscription)
                session.commit()
                return True
        except IntegrityError:
            return False

    def remove_subscription(self, channel_id: int, keyword: str) -> bool:
        """チャンネルのキーワード購読を削除"""
        with self._get_session() as session:
            result = (
                session.query(Subscription)
                .filter_by(channel_id=channel_id, keyword=keyword)
                .delete()
            )
            session.commit()
            return result > 0

    def get_subscriptions(self, channel_id: int) -> list[str]:
        """チャンネルの全てのキーワード購読を取得"""
        with self._get_session() as session:
            subscriptions = (
                session.query(Subscription.keyword)
                .filter_by(channel_id=channel_id)
                .all()
            )
            return [sub.keyword for sub in subscriptions]

    def get_all_subscriptions(self) -> list[tuple[int, str]]:
        """全チャンネルの全てのキーワード購読を取得"""
        with self._get_session() as session:
            subscriptions = session.query(
                Subscription.channel_id, Subscription.keyword
            ).all()
            return [(sub.channel_id, sub.keyword) for sub in subscriptions]

    def is_thread_notified(self, thread_id: str, keyword: str, channel_id: int) -> bool:
        """チャンネルでキーワードに対してスレッドが既に通知済みかチェック"""
        with self._get_session() as session:
            result = (
                session.query(NotifiedThread)
                .filter_by(thread_id=thread_id, keyword=keyword, channel_id=channel_id)
                .first()
            )
            return result is not None

    def mark_thread_notified(
        self, thread_id: str, keyword: str, channel_id: int
    ) -> None:
        """チャンネルでキーワードに対してスレッドを通知済みとしてマーク"""
        with self._get_session() as session:
            existing = (
                session.query(NotifiedThread)
                .filter_by(thread_id=thread_id, keyword=keyword, channel_id=channel_id)
                .first()
            )
            if not existing:
                notified_thread = NotifiedThread(
                    thread_id=thread_id, keyword=keyword, channel_id=channel_id
                )
                session.add(notified_thread)
                session.commit()

    def mute_channel(self, channel_id: int, muted_until: datetime) -> None:
        """指定された日時までチャンネルをミュート"""
        with self._get_session() as session:
            existing = (
                session.query(MutedChannel).filter_by(channel_id=channel_id).first()
            )
            if existing:
                existing.muted_until = muted_until  # type: ignore
                existing.muted_at = datetime.now()  # type: ignore
            else:
                muted_channel = MutedChannel(
                    channel_id=channel_id, muted_until=muted_until
                )
                session.add(muted_channel)
            session.commit()

    def unmute_channel(self, channel_id: int) -> bool:
        """チャンネルのミュートを解除"""
        with self._get_session() as session:
            result = (
                session.query(MutedChannel).filter_by(channel_id=channel_id).delete()
            )
            session.commit()
            return result > 0

    def is_channel_muted(self, channel_id: int) -> bool:
        """チャンネルが現在ミュート中かチェック"""
        with self._get_session() as session:
            now = datetime.now()
            result = (
                session.query(MutedChannel)
                .filter(
                    MutedChannel.channel_id == channel_id,
                    MutedChannel.muted_until > now,
                )
                .first()
            )
            return result is not None

    def get_mute_status(self, channel_id: int) -> datetime | None:
        """チャンネルがミュート中の場合、ミュート期限時刻を取得"""
        with self._get_session() as session:
            now = datetime.now()
            muted_channel = (
                session.query(MutedChannel)
                .filter(
                    MutedChannel.channel_id == channel_id,
                    MutedChannel.muted_until > now,
                )
                .first()
            )
            if muted_channel:
                return muted_channel.muted_until  # type: ignore
            return None

    def cleanup_expired_mutes(self) -> None:
        """期限切れのミュートエントリをデータベースから削除"""
        with self._get_session() as session:
            now = datetime.now()
            session.query(MutedChannel).filter(MutedChannel.muted_until <= now).delete()
            session.commit()

    def cleanup_old_notifications(self, days: int = 7) -> None:
        """指定日数より古い通知レコードをデータベースから削除"""
        with self._get_session() as session:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = (
                session.query(NotifiedThread)
                .filter(NotifiedThread.notified_at <= cutoff_date)
                .delete()
            )
            session.commit()
            if deleted_count > 0:
                logger.info(
                    f"{deleted_count}件の古い通知レコードをクリーンアップしました"
                )
