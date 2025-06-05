from typing import List, Optional, Tuple

from hydrogram import Client
from hydrogram.helpers import ikb
from hydrogram.types import Message

from bot.utils import config

from .handlers import helper_handlers


def admin_buttons() -> ikb:
    """
    Creates an inline keyboard with buttons for admin-related actions.

    Returns:
        ikb: An inline keyboard with buttons for managing chats and additional settings.
    """
    buttons: List[Tuple[str, str, str]] = []
    fs_data = helper_handlers.fs_chats
    if fs_data:
        for chat_id, chat_info in fs_data.items():
            chat_type = chat_info.get("chat_type", "Unknown")
            invite_link = chat_info.get("invite_link", "#")
            buttons.append((chat_type, invite_link, "url"))

    button_layouts: List[List[Tuple[str, str, str]]] = [
        buttons[i : i + 3] for i in range(0, len(buttons), 3)
    ]
    button_layouts.append([("Bot Settings", "settings")])

    return ikb(button_layouts)


async def join_buttons(client: Client, message: Message, user_id: int) -> Optional[ikb]:
    """
    Creates an inline keyboard with buttons for joining chats the user hasn't joined yet.

    Args:
        client (Client): The hydrogram client instance.
        message (Message): The message that triggered this action.
        user_id (int): The ID of the user for whom the join buttons are being created.

    Returns:
        Optional[ikb]: An inline keyboard with join buttons, or None if the user is already joined.
    """
    no_join_ids = await helper_handlers.user_is_not_join(user_id)
    if not no_join_ids:
        return None

    buttons: List[Tuple[str, str, str]] = []
    fs_data = helper_handlers.fs_chats
    for chat_id in no_join_ids:
        chat_info = fs_data.get(chat_id, {})
        chat_type = chat_info.get("chat_type", "Unknown")
        invite_link = chat_info.get("invite_link", "#")
        buttons.append((f"Join {chat_type}", invite_link, "url"))

    button_layouts: List[List[Tuple[str, str, str]]] = [
        buttons[i : i + 2] for i in range(0, len(buttons), 2)
    ]

    if len(message.command) > 1:
        start_url = f"https://t.me/{client.me.username}?start={message.command[1]}"
        button_layouts.append([("Try Again", start_url, "url")])

    return ikb(button_layouts)


class HelperButtons:
    """
    Defines various inline button layouts for the bot.
    """

    #Contact: List[List[Tuple[str, str, str]]] = [
    #    [("Contact", f"https://t.me/{config.OWNER_USERNAME}/3", "url")]
    #]
    Contact: List[List[Tuple[str, str, str]]] = [
        [("Privacy Policy", "https://telegram.org/privacy-tpa", "url")]
    ]

    Close: List[List[Tuple[str, str]]] = [[("Close", "close")]]
    Broadcast: List[List[Tuple[str, str]]] = [[("Refresh", "broadcast")]]
    Ping: List[List[Tuple[str, str]]] = [[("Refresh", "ping")]]
    Uptime: List[List[Tuple[str, str]]] = [[("Refresh", "uptime")]]
    Menu: List[List[Tuple[str, str]]] = [
        [("Generate Status", "menu generate")],
        [("Start", "menu start"), ("Force", "menu force")],
        [("Protect Content", "menu protect")],
        [("Admins", "menu admins"), ("F-Subs", "menu fsubs")],
        [("Sponsor", "menu sponsor")],
        [("🗄️ DB Channel", "menu dbchannel")],
        [("📝 Custom Caption", "menu custom_caption")],
        [("📤 Konten", "menu content")],
        [("Close", "close")],
    ]
    Cancel: List[List[Tuple[str, str]]] = [[("Cancel", "cancel")]]
    Generate: List[List[Tuple[str, str]]] = [
        [("« Back", "settings"), ("Change", "change generate")]
    ]
    Generate_: List[List[Tuple[str, str]]] = [[("« Back", "menu generate")]]
    @staticmethod
    async def get_start_buttons() -> List[List[Tuple[str, str]]]:
        from bot.db_funcs.text import get_start_photo_msg
        photo = await get_start_photo_msg()
        buttons = [[("Set Text Start", "update start")], [("Set Photo Start", "update start_photo")]]
        if photo:
            buttons.append([("Del Photo Start", "delete start_photo")])
        buttons.append([("Back", "settings")])
        return buttons

    @staticmethod
    async def get_force_buttons() -> List[List[Tuple[str, str]]]:
        from bot.db_funcs.text import get_force_photo_msg
        photo = await get_force_photo_msg()
        buttons = [[("Set Text Force", "update force")], [("Set Photo Force", "update force_photo")]]
        if photo:
            buttons.append([("Del Photo Force", "delete force_photo")])
        buttons.append([("Back", "settings")])
        return buttons

    Start_: List[List[Tuple[str, str]]] = [[("« Back", "menu start")]]
    Force_: List[List[Tuple[str, str]]] = [[("« Back", "menu force")]]
    Protect: List[List[Tuple[str, str]]] = [
        [("« Back", "settings"), ("Change", "change protect")]
    ]
    Protect_: List[List[Tuple[str, str]]] = [[("« Back", "menu protect")]]
    Admins: List[List[Tuple[str, str]]] = [
        [("Add", "add admin"), ("Del.", "del admin")],
        [("« Back", "settings")],
    ]
    Admins_: List[List[Tuple[str, str]]] = [[("« Back", "menu admins")]]
    Fsubs: List[List[Tuple[str, str]]] = [
        [("Add", "add f-sub"), ("Del.", "del f-sub")],
        [("« Back", "settings")],
    ]
    Fsubs_: List[List[Tuple[str, str]]] = [[("« Back", "menu fsubs")]]
    @staticmethod
    def get_sponsor_buttons(sponsor_enabled: bool) -> List[List[Tuple[str, str]]]:
        # Tombol on/off dinamis
        toggle_text = "🔴 Nonaktifkan Sponsor" if sponsor_enabled else "🟢 Aktifkan Sponsor"
        return [
            [("✏️ Edit Text", "update sponsor_text"), ("🖼️ Edit Photo", "update sponsor_photo")],
            [("🗑️ Hapus Text", "delete sponsor_text"), ("🗑️ Hapus Photo", "delete sponsor_photo")],
            [(toggle_text, "toggle sponsor")],
            [("« Back", "settings")],
        ]
    # Untuk submenu back
    Sponsor_: List[List[Tuple[str, str]]] = [[("« Back", "menu sponsor")]]

    DBChannel: List[List[Tuple[str, str]]] = [
        [("🔄 Ganti DB Channel", "update dbchannel"), ("♻️ Reset ke Default", "reset dbchannel")],
        [("« Back", "settings")],
    ]
    DBChannel_: List[List[Tuple[str, str]]] = [[("« Back", "menu dbchannel")]]

    CustomCaption: List[List[Tuple[str, str]]] = [
        [("✏️ Edit Caption", "update custom_caption"), ("🗑️ Hapus Caption", "delete custom_caption")],
        [("🔄 On/Off Caption", "toggle custom_caption")],
        [("« Back", "settings")],
    ]
    CustomCaption_: List[List[Tuple[str, str]]] = [[("« Back", "menu custom_caption")]]

    # === Konten ===
    @staticmethod
    def get_content_buttons(content_enabled: bool, content_channels: dict) -> list:
        status = "🟢 ON" if content_enabled else "🔴 OFF"
        buttons = [
            [(f"Status: {status}", "toggle content")],
            [("Custom Caption", "content custom_caption")],
            [("Tambah Channel Konten", "content add_channel")],
        ]
        # Daftar channel konten
        if content_channels:
            for ch_id, ch_name in content_channels.items():
                buttons.append([(f"{ch_name} ({ch_id})", f"content ch_{ch_id}")])
        return buttons + [[("Back", "settings")]]

    @staticmethod
    def get_content_confirm_delete_buttons(ch_id: int) -> list:
        return [
            [("Ya, Hapus", f"content del_confirm_{ch_id}"), ("Tidak", "menu content")]
        ]

    ContentCustomCaption_: List[List[Tuple[str, str]]] = [[("Back", "menu content")]]


helper_buttons: HelperButtons = HelperButtons()
