from typing import Dict, List, Optional, Union

import hydrogram
from hydrogram import enums, errors

from bot.base import bot
from bot.db_funcs import (
    del_fs_chat,
    get_admins,
    get_force_text_msg,
    get_fs_chats,
    get_generate_status,
    get_protect_content,
    get_start_text_msg,
    get_content_channels,
    get_content_enabled,
    get_content_custom_caption,
)
from bot.utils import config, logger
from bot.db_funcs.text import (
    get_sponsor_text_msg,
    get_sponsor_photo_msg,
)

from .url_safe import url_safe


class HelperHandlers:
    def __init__(self, client: hydrogram.Client) -> None:
        """
        Initializes the HelperHandlers with the given bot client.

        Args:
            client (bot): The bot client instance.
        """
        self.client = client
        self.start_text: str = ""
        self.force_text: str = ""
        self.admins: List[int] = []
        self.fs_chats: Dict[int, Dict[str, Union[str, str]]] = {}
        self.protect_content: bool = False
        self.generate_status: bool = False
        self.sponsor_text: str = ""
        self.sponsor_photo: str = ""
        self.content_channels: Dict[int, str] = {}  # id: nama
        self.content_enabled: bool = False
        self.content_custom_caption: str = ""

    async def start_text_init(self) -> str:
        """
        Initializes the start text from the database.

        Returns:
            str: The start text.
        """
        self.start_text = await get_start_text_msg()
        return self.start_text

    async def force_text_init(self) -> str:
        """
        Initializes the force text from the database.

        Returns:
            str: The force text.
        """
        self.force_text = await get_force_text_msg()
        return self.force_text

    async def admins_init(self) -> List[int]:
        """
        Initializes the list of admin user IDs from the database and adds the owner ID.

        Returns:
            List[int]: A list of admin user IDs.
        """
        admin_ids = await get_admins()
        self.admins = admin_ids + [config.OWNER_ID] if admin_ids else [config.OWNER_ID]

        for i, user_id in enumerate(self.admins):
            logger.info(f"Bot Admin {i + 1}: {user_id}")

        return self.admins

    async def fs_chats_init(self) -> Dict[int, Dict[str, Union[str, str]]]:
        """
        Initializes the list of free subscription chats from the database and verifies their details.

        Returns:
            Dict[int, Dict[str, Union[str, str]]]: A dictionary of chat details.
        """
        self.fs_chats.clear()  # Restore to default
        fs_chats = await get_fs_chats()
        if fs_chats:
            for i, chat_id in enumerate(fs_chats):
                try:
                    chat = await self.client.get_chat(chat_id=chat_id)
                    chat_type = (
                        "Group"
                        if chat.type
                        in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]
                        else "Channel"
                    )
                    invite_link = chat.invite_link
                    if not invite_link:
                        raise errors.RPCError

                    self.fs_chats[chat_id] = {
                        "chat_type": chat_type,
                        "invite_link": invite_link,
                    }
                    logger.info(f"Sub. Chat {i + 1}: {chat_id}")
                except errors.RPCError as rpc:
                    logger.warning(f"Sub. Chat {i + 1}: {rpc.MESSAGE}")
                    await del_fs_chat(chat_id)
        else:
            logger.info("Sub. Chats: None")

        return self.fs_chats

    async def protect_content_init(self) -> bool:
        """
        Initializes the content protection status from the database.

        Returns:
            bool: The content protection status.
        """
        self.protect_content = await get_protect_content()
        return self.protect_content

    async def generate_status_init(self) -> bool:
        """
        Initializes the generate status from the database.

        Returns:
            bool: The generate status.
        """
        self.generate_status = await get_generate_status()
        return self.generate_status

    async def user_is_not_join(self, user_id: int) -> Optional[List[int]]:
        """
        Checks which subscription chats the user has not joined yet.

        Args:
            user_id (int): The ID of the user to check.

        Returns:
            Optional[List[int]]: A list of chat IDs that the user has not joined, or None if the user is an admin.
        """
        chat_ids = list(self.fs_chats.keys())
        if not chat_ids or user_id in self.admins:
            return None

        already_joined = set()
        for chat_id in chat_ids:
            try:
                await self.client.get_chat_member(chat_id, user_id)
                already_joined.add(chat_id)
            except errors.RPCError:
                continue

        return [chat_id for chat_id in chat_ids if chat_id not in already_joined]

    def decode_data(self, encoded_data: str) -> Union[List[int], range]:
        """
        Decodes the given encoded data into a list of IDs or a range of IDs.

        Args:
            encoded_data (str): The encoded data to decode.

        Returns:
            Union[List[int], range]: A list of IDs or a range of IDs.
        """
        database_chat_id = config.DATABASE_CHAT_ID
        decoded_data = url_safe.decode_data(encoded_data).split("-")
        if len(decoded_data) == 2:
            return [int(int(decoded_data[1]) / abs(database_chat_id))]

        elif len(decoded_data) == 3:
            start_id = int(int(decoded_data[1]) / abs(database_chat_id))
            end_id = int(int(decoded_data[2]) / abs(database_chat_id))
            if start_id < end_id:
                return range(start_id, end_id + 1)
            else:
                return range(start_id, end_id - 1, -1)

    async def sponsor_text_init(self) -> str:
        self.sponsor_text = await get_sponsor_text_msg()
        return self.sponsor_text

    async def sponsor_photo_init(self) -> str:
        self.sponsor_photo = await get_sponsor_photo_msg()
        return self.sponsor_photo

    async def content_channels_init(self) -> Dict[int, str]:
        """
        Inisialisasi daftar channel konten dari database dan ambil nama channel.
        """
        self.content_channels.clear()
        channel_ids = await get_content_channels()
        for ch_id in channel_ids:
            try:
                chat = await self.client.get_chat(ch_id)
                self.content_channels[ch_id] = chat.title or chat.username or str(ch_id)
            except Exception:
                self.content_channels[ch_id] = str(ch_id)
        return self.content_channels

    async def content_enabled_init(self) -> bool:
        self.content_enabled = await get_content_enabled()
        return self.content_enabled

    async def content_custom_caption_init(self) -> str:
        self.content_custom_caption = await get_content_custom_caption()
        return self.content_custom_caption


helper_handlers: HelperHandlers = HelperHandlers(bot)
