"""
Twitch IRC Chat Client

twitchioを使用してTwitchチャットからコメントを取得します。
"""

import asyncio
from datetime import datetime
from typing import Callable, Optional
import logging

try:
    from twitchio.ext import commands
    from twitchio import Message, Channel
    TWITCHIO_AVAILABLE = True
except ImportError:
    TWITCHIO_AVAILABLE = False
    commands = None
    Message = None
    Channel = None

from .base import BaseChatClient
from .models import Comment, Platform

logger = logging.getLogger(__name__)


class TwitchChatClient(BaseChatClient):
    """Twitch IRC チャットクライアント"""

    def __init__(
        self,
        access_token: str,
        channel_name: str,
        client_id: Optional[str] = None,
        prefix: str = "!",
    ):
        """
        Twitch チャットクライアントを初期化

        Args:
            access_token: Twitch OAuthアクセストークン
            channel_name: 接続するチャンネル名（#なし）
            client_id: Twitch Client ID（オプション）
            prefix: コマンドプレフィックス
        """
        if not TWITCHIO_AVAILABLE:
            raise ImportError(
                "twitchio is not installed. "
                "Please install it with: pip install twitchio"
            )

        self.access_token = access_token
        self.channel_name = channel_name.lower().lstrip('#')
        self.client_id = client_id
        self.prefix = prefix

        self._bot: Optional['TwitchBot'] = None
        self._callback: Optional[Callable[[Comment], None]] = None
        self._connected = False
        self._comments: list[Comment] = []
        self._task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Twitchチャットに接続"""
        if self._connected:
            logger.warning("Already connected to Twitch chat")
            return

        logger.info(f"Connecting to Twitch channel: {self.channel_name}")

        # Botインスタンスを作成
        self._bot = TwitchBot(
            token=self.access_token,
            prefix=self.prefix,
            initial_channels=[self.channel_name],
            client=self,
        )

        # バックグラウンドでBotを実行
        self._task = asyncio.create_task(self._run_bot())

        # 接続を待機（最大10秒）
        for _ in range(100):
            if self._connected:
                break
            await asyncio.sleep(0.1)

        if not self._connected:
            raise ConnectionError("Failed to connect to Twitch chat")

        logger.info(f"Connected to Twitch channel: {self.channel_name}")

    async def _run_bot(self) -> None:
        """Botを実行"""
        try:
            await self._bot.start()
        except Exception as e:
            logger.error(f"Twitch bot error: {e}")
            self._connected = False

    async def disconnect(self) -> None:
        """接続を切断"""
        if not self._connected:
            return

        logger.info("Disconnecting from Twitch chat")

        if self._bot:
            await self._bot.close()
            self._bot = None

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        self._connected = False
        logger.info("Disconnected from Twitch chat")

    async def get_comments(self, limit: int = 10) -> list[Comment]:
        """
        最新コメントを取得

        Args:
            limit: 取得するコメント数の上限

        Returns:
            コメントのリスト
        """
        comments = self._comments[-limit:] if self._comments else []
        self._comments = []  # 取得後はクリア
        return comments

    def on_comment(self, callback: Callable[[Comment], None]) -> None:
        """
        コメント受信時のコールバックを設定

        Args:
            callback: コメントを受け取るコールバック関数
        """
        self._callback = callback

    def _handle_message(self, message: 'Message') -> None:
        """
        メッセージを処理

        Args:
            message: twitchioのMessageオブジェクト
        """
        # Commentオブジェクトを作成
        comment = self._message_to_comment(message)

        # リストに追加
        self._comments.append(comment)

        # 古いコメントを削除（最大100件保持）
        if len(self._comments) > 100:
            self._comments = self._comments[-100:]

        # コールバックがあれば呼び出し
        if self._callback:
            try:
                self._callback(comment)
            except Exception as e:
                logger.error(f"Error in comment callback: {e}")

    def _message_to_comment(self, message: 'Message') -> Comment:
        """
        twitchioのMessageをCommentに変換

        Args:
            message: twitchioのMessageオブジェクト

        Returns:
            Commentオブジェクト
        """
        # ユーザー情報を取得
        author = message.author
        tags = message.tags or {}

        # バッジからメンバーシップ・モデレーター判定
        badges = tags.get('badges', '')
        is_subscriber = 'subscriber' in badges or 'founder' in badges
        is_moderator = author.is_mod if author else False
        is_broadcaster = 'broadcaster' in badges

        # Bits（投げ銭）の金額を取得
        bits = int(tags.get('bits', 0))

        return Comment(
            id=tags.get('id', str(hash(message.content + str(datetime.now())))),
            platform=Platform.TWITCH,
            user_id=str(author.id) if author and author.id else 'unknown',
            user_name=author.name if author else 'unknown',
            message=message.content,
            timestamp=datetime.now(),
            is_member=is_subscriber,
            is_moderator=is_moderator or is_broadcaster,
            donation_amount=bits,  # Bitsを金額として扱う
        )

    @property
    def is_connected(self) -> bool:
        """接続状態を返す"""
        return self._connected


class TwitchBot(commands.Bot if commands else object):
    """Twitch Bot クラス"""

    def __init__(
        self,
        token: str,
        prefix: str,
        initial_channels: list[str],
        client: TwitchChatClient,
    ):
        """
        Twitch Botを初期化

        Args:
            token: OAuthトークン
            prefix: コマンドプレフィックス
            initial_channels: 初期接続チャンネル
            client: 親のTwitchChatClientインスタンス
        """
        if commands is None:
            raise ImportError("twitchio is not installed")

        super().__init__(
            token=token,
            prefix=prefix,
            initial_channels=initial_channels,
        )
        self._client = client

    async def event_ready(self) -> None:
        """Bot準備完了時のイベント"""
        logger.info(f"Twitch bot logged in as {self.nick}")
        self._client._connected = True

    async def event_message(self, message: 'Message') -> None:
        """
        メッセージ受信時のイベント

        Args:
            message: 受信したメッセージ
        """
        # Bot自身のメッセージは無視
        if message.echo:
            return

        # クライアントに通知
        self._client._handle_message(message)

        # コマンドも処理
        await self.handle_commands(message)

    async def event_join(self, channel: 'Channel', user) -> None:
        """
        ユーザー参加時のイベント

        Args:
            channel: チャンネル
            user: 参加したユーザー
        """
        logger.debug(f"User {user.name} joined {channel.name}")

    async def event_part(self, user) -> None:
        """
        ユーザー退出時のイベント

        Args:
            user: 退出したユーザー
        """
        logger.debug(f"User {user.name} left the channel")


async def create_twitch_client(
    access_token: str,
    channel_name: str,
    client_id: Optional[str] = None,
) -> TwitchChatClient:
    """
    Twitchチャットクライアントを作成して接続

    Args:
        access_token: Twitch OAuthアクセストークン
        channel_name: 接続するチャンネル名
        client_id: Twitch Client ID（オプション）

    Returns:
        接続済みのTwitchChatClient
    """
    client = TwitchChatClient(
        access_token=access_token,
        channel_name=channel_name,
        client_id=client_id,
    )
    await client.connect()
    return client
