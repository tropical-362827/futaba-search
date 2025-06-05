"""ふたば検索のDiscordボット実装"""

from datetime import UTC, datetime

import discord
from discord.ext import commands, tasks

from .config import DISCORD_TOKEN, MONITOR_INTERVAL
from .database import FutabaDatabase
from .logging_config import get_logger
from .monitor import FutabaMonitor
from .utils import format_datetime, get_mute_until_datetime

logger = get_logger(__name__)


class FutabaBot(commands.Bot):
    """ふたばスレッドを監視するDiscordボット"""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        self.db = FutabaDatabase()
        self.monitor_task: tasks.Loop | None = None

    async def setup_hook(self) -> None:
        """ボット開始時に呼び出されるセットアップフック"""
        # スラッシュコマンドを同期
        try:
            await self.tree.sync()
            print(f"Synced {len(self.tree.get_commands())} commands")
        except Exception as e:
            print(f"Failed to sync commands: {e}")

    async def on_ready(self) -> None:
        """ボットが準備完了時に呼び出される"""
        logger.info(f"{self.user} がDiscordに接続しました!")

        # 初期ステータスを設定
        activity = discord.Activity(
            type=discord.ActivityType.watching, name="ふたば☆ちゃんねるをチェック中..."
        )
        await self.change_presence(status=discord.Status.online, activity=activity)
        logger.info("初期ステータスを設定")

        if not self.monitor_task:
            self.monitor_task = self.monitor_futaba.start()  # type: ignore

    @tasks.loop(seconds=MONITOR_INTERVAL)
    async def monitor_futaba(self) -> None:
        """ふたばの新しいスレッドを監視する定期タスク"""
        logger.debug("監視タスクを開始")
        try:
            # 期限切れのミュートを最初にクリーンアップ
            self.db.cleanup_expired_mutes()
            # 一週間以上前の古い通知レコードをクリーンアップ
            self.db.cleanup_old_notifications()

            async with FutabaMonitor() as monitor:
                data = await monitor.fetch_threads()
                if not data:
                    logger.debug("スレッドデータの取得に失敗、監視をスキップ")
                    return

                threads = monitor.parse_threads(data)
                subscriptions = self.db.get_all_subscriptions()

                logger.debug(
                    f"{len(threads)}件のスレッド、{len(subscriptions)}件の購読をチェック"
                )

                # アクティブなチャンネル数を計算してステータス更新
                active_channels = len({channel_id for channel_id, _ in subscriptions})
                if active_channels > 0:
                    activity = discord.Activity(
                        type=discord.ActivityType.watching,
                        name=f"{active_channels}個のチャンネルで動作中!",
                    )
                else:
                    activity = discord.Activity(
                        type=discord.ActivityType.watching, name="購読登録待ち中..."
                    )
                await self.change_presence(
                    status=discord.Status.online, activity=activity
                )
                logger.debug(f"ステータス更新: {active_channels}個のチャンネルで動作中")

                for channel_id, keyword in subscriptions:
                    # ミュート中のチャンネルをスキップ
                    if self.db.is_channel_muted(channel_id):
                        continue

                    channel = self.get_channel(channel_id)
                    if not channel:
                        continue

                    for thread in threads:
                        thread_id = thread["id"]

                        if self.db.is_thread_notified(thread_id, keyword, channel_id):
                            continue

                        if monitor.check_keyword_match(thread, keyword):
                            logger.info(
                                f"キーワード '{keyword}' がマッチ: {thread.get('title', 'N/A')}"
                            )
                            if isinstance(channel, discord.TextChannel):
                                await self.send_notification(channel, thread, keyword)
                                logger.debug(
                                    f"通知送信完了: チャンネル{channel_id} -> {thread_id}"
                                )
                            self.db.mark_thread_notified(thread_id, keyword, channel_id)

        except Exception as e:
            logger.error(f"監視タスクでエラーが発生: {e}", exc_info=True)
        finally:
            logger.debug("監視タスクを終了")

    async def send_notification(
        self, channel: discord.TextChannel, thread: dict, keyword: str
    ) -> None:
        """通知埋め込みをDiscordチャンネルに送信"""
        thread_id = thread["id"]
        title = thread["title"]
        thumb_url = thread["thumb_url"]
        timestamp = datetime.now(UTC)

        embed = discord.Embed(
            title=f"キーワード『{keyword}』",
            description=f"https://may.2chan.net/b/res/{thread_id}.htm\n{title}",
            timestamp=timestamp,
            color=0x00FF00,
        )

        if thumb_url:
            embed.set_image(url=thumb_url)

        embed.add_field(
            name="ふたばフォレスト",
            value=f"http://futabaforest.net/b/res/{thread_id}.htm",
            inline=False,
        )

        ftbucket_url = (
            f"https://may.ftbucket.info/may/cont/"
            f"may.2chan.net_b_res_{thread_id}/index.htm"
        )
        embed.add_field(
            name="FTBucket",
            value=ftbucket_url,
            inline=False,
        )

        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to send notification: {e}")


def create_bot() -> FutabaBot:
    """ボットインスタンスを作成し設定"""
    bot = FutabaBot()

    @bot.tree.command(name="futaba-search", description="Futaba monitoring commands")
    async def futaba_search(
        interaction: discord.Interaction,
        action: str,
        keyword: str | None = None,
        interval: str | None = None,
    ) -> None:
        """ふたば検索スラッシュコマンドを処理"""
        logger.debug(
            f"スラッシュコマンド受信: action={action}, keyword={keyword}, interval={interval}, channel_id={interaction.channel.id if interaction.channel else None}, user={interaction.user}"
        )
        await interaction.response.defer()

        if action == "subscribe":
            logger.debug(f"subscribeアクションを処理中: keyword={keyword}")
            if not keyword:
                logger.debug("subscribe: キーワード未指定でエラー返却")
                await interaction.followup.send(
                    "キーワードを指定してください。", ephemeral=True
                )
                return

            if interaction.channel is None:
                logger.debug("subscribe: チャンネル情報取得失敗")
                await interaction.followup.send(
                    "チャンネル情報を取得できませんでした。", ephemeral=True
                )
                return
            logger.debug(
                f"subscribe: データベースに購読追加試行 - channel_id={interaction.channel.id}, keyword={keyword}"
            )
            success = bot.db.add_subscription(interaction.channel.id, keyword)
            if success:
                logger.debug(
                    f"subscribe: 購読追加成功 - channel_id={interaction.channel.id}, keyword={keyword}"
                )
                await interaction.followup.send(
                    f"キーワード '{keyword}' の通知を登録しました。"
                )
            else:
                logger.debug(
                    f"subscribe: 購読追加失敗(重複) - channel_id={interaction.channel.id}, keyword={keyword}"
                )
                await interaction.followup.send(
                    f"キーワード '{keyword}' は既に登録済みです。", ephemeral=True
                )

        elif action == "unsubscribe":
            logger.debug(f"unsubscribeアクションを処理中: keyword={keyword}")
            if not keyword:
                logger.debug("unsubscribe: キーワード未指定でエラー返却")
                await interaction.followup.send(
                    "キーワードを指定してください。", ephemeral=True
                )
                return

            if interaction.channel is None:
                logger.debug("unsubscribe: チャンネル情報取得失敗")
                await interaction.followup.send(
                    "チャンネル情報を取得できませんでした。", ephemeral=True
                )
                return
            logger.debug(
                f"unsubscribe: データベースから購読削除試行 - channel_id={interaction.channel.id}, keyword={keyword}"
            )
            success = bot.db.remove_subscription(interaction.channel.id, keyword)
            if success:
                logger.debug(
                    f"unsubscribe: 購読削除成功 - channel_id={interaction.channel.id}, keyword={keyword}"
                )
                await interaction.followup.send(
                    f"キーワード '{keyword}' の通知を解除しました。"
                )
            else:
                logger.debug(
                    f"unsubscribe: 購読削除失敗(登録なし) - channel_id={interaction.channel.id}, keyword={keyword}"
                )
                await interaction.followup.send(
                    f"キーワード '{keyword}' は登録されていません。", ephemeral=True
                )

        elif action == "list":
            logger.debug("listアクションを処理中")
            if interaction.channel is None:
                logger.debug("list: チャンネル情報取得失敗")
                await interaction.followup.send(
                    "チャンネル情報を取得できませんでした。", ephemeral=True
                )
                return
            logger.debug(
                f"list: チャンネルの購読情報を取得中 - channel_id={interaction.channel.id}"
            )
            keywords = bot.db.get_subscriptions(interaction.channel.id)
            mute_status = bot.db.get_mute_status(interaction.channel.id)
            logger.debug(
                f"list: 取得結果 - keywords={len(keywords)}件, muted={bool(mute_status)}"
            )

            response = ""
            if keywords:
                keyword_list = "\n".join([f"• {kw}" for kw in keywords])
                response = f"このチャンネルの登録キーワード:\n{keyword_list}\n"
                logger.debug(f"list: キーワードリストを表示 - {len(keywords)}件")
            else:
                response = "このチャンネルにはキーワードが登録されていません。\n"
                logger.debug("list: キーワードなしで空リストを表示")

            if mute_status:
                response += f"\n🔇 通知は {format_datetime(mute_status)} まで無効になっています。"
                logger.debug(f"list: ミュート状態を表示 - until={mute_status}")

            await interaction.followup.send(response)

        elif action == "mute":
            logger.debug(f"muteアクションを処理中: interval={interval}")
            if not interval:
                logger.debug("mute: 期間未指定でエラー返却")
                await interaction.followup.send(
                    "期間を指定してください（例: 30m, 1h, 2d）。", ephemeral=True
                )
                return

            logger.debug(f"mute: 期間文字列を解析中 - interval={interval}")
            mute_until = get_mute_until_datetime(interval)
            if not mute_until:
                logger.debug(f"mute: 無効な期間形式でエラー返却 - interval={interval}")
                await interaction.followup.send(
                    "無効な期間形式です。例: 30m, 1h, 2d", ephemeral=True
                )
                return

            if interaction.channel is None:
                logger.debug("mute: チャンネル情報取得失敗")
                await interaction.followup.send(
                    "チャンネル情報を取得できませんでした。", ephemeral=True
                )
                return
            logger.debug(
                f"mute: チャンネルをミュート設定中 - channel_id={interaction.channel.id}, until={mute_until}"
            )
            bot.db.mute_channel(interaction.channel.id, mute_until)
            logger.debug(
                f"mute: ミュート設定完了 - channel_id={interaction.channel.id}"
            )
            await interaction.followup.send(
                f"🔇 通知を {format_datetime(mute_until)} まで無効にしました。"
            )

        elif action == "unmute":
            logger.debug("unmuteアクションを処理中")
            if interaction.channel is None:
                logger.debug("unmute: チャンネル情報取得失敗")
                await interaction.followup.send(
                    "チャンネル情報を取得できませんでした。", ephemeral=True
                )
                return
            logger.debug(
                f"unmute: チャンネルのミュート解除試行 - channel_id={interaction.channel.id}"
            )
            success = bot.db.unmute_channel(interaction.channel.id)
            if success:
                logger.debug(
                    f"unmute: ミュート解除成功 - channel_id={interaction.channel.id}"
                )
                await interaction.followup.send("🔔 通知を再開しました。")
            else:
                logger.debug(
                    f"unmute: ミュート解除失敗(ミュートされていない) - channel_id={interaction.channel.id}"
                )
                await interaction.followup.send(
                    "このチャンネルはミュートされていません。", ephemeral=True
                )

        else:
            logger.debug(f"不明なアクションでエラー返却: action={action}")
            await interaction.followup.send(
                "有効なアクション: subscribe, unsubscribe, list, mute, unmute",
                ephemeral=True,
            )

    @futaba_search.autocomplete("action")
    async def action_autocomplete(
        _interaction: discord.Interaction, current: str
    ) -> list[discord.app_commands.Choice[str]]:
        """アクションパラメータの自動補完を提供"""
        actions = ["subscribe", "unsubscribe", "list", "mute", "unmute"]
        return [
            discord.app_commands.Choice(name=action, value=action)
            for action in actions
            if current.lower() in action.lower()
        ]

    return bot


def run_bot() -> None:
    """Discordボットを実行"""
    if not DISCORD_TOKEN:
        print("DISCORD_TOKEN environment variable is required")
        exit(1)

    bot = create_bot()
    bot.run(DISCORD_TOKEN)
