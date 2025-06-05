"""ふたばチャンネルの監視機能"""

from typing import Any

import aiohttp

from .config import FUTABA_API_URL
from .logging_config import get_logger

logger = get_logger(__name__)


class FutabaMonitor:
    """新しいスレッドのためにふたばチャンネルを監視"""

    def __init__(self) -> None:
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "FutabaMonitor":
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, _exc_type: Any, _exc_val: Any, _exc_tb: Any) -> None:
        if self.session:
            await self.session.close()

    async def fetch_threads(self) -> dict[str, Any] | None:
        """ふたばAPIからスレッドデータを取得"""
        if not self.session:
            raise RuntimeError(
                "セッションが初期化されていません。asyncコンテキストマネージャーを使用してください。"
            )

        try:
            async with self.session.get(FUTABA_API_URL) as response:
                if response.status == 200:
                    json_data: dict[str, Any] = await response.json()
                    return json_data
                else:
                    logger.warning(f"スレッドの取得に失敗: HTTP {response.status}")
                    return None
        except Exception as e:
            logger.error(f"スレッド取得中にエラーが発生: {e}", exc_info=True)
            return None

    def parse_threads(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """ふたばAPIレスポンスからスレッドデータを解析"""
        threads: list[dict[str, Any]] = []

        if "res" not in data:
            return threads

        for thread_id, thread_data in data["res"].items():
            # スレッド情報を抽出
            com = thread_data.get("com", "")
            now = thread_data.get("now", "")
            name = thread_data.get("name", "")
            sub = thread_data.get("sub", "")

            # 利用可能な場合は画像URLを構築
            thumb_url = None
            if thread_data.get("thumb"):
                thumb_url = f"https://may.2chan.net{thread_data['thumb']}"
            elif thread_data.get("src"):
                thumb_url = f"https://may.2chan.net{thread_data['src']}"

            threads.append(
                {
                    "id": thread_id,
                    "title": com,
                    "subject": sub,
                    "name": name,
                    "timestamp": now,
                    "thumb_url": thumb_url,
                }
            )

        return threads

    def check_keyword_match(self, thread: dict, keyword: str) -> bool:
        """スレッドがキーワードにマッチするかチェック"""
        searchable_text = f"{thread['title']} {thread['subject']}".lower()
        return keyword.lower() in searchable_text
