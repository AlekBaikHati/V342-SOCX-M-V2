from hydrogram import Client, errors, filters
from hydrogram.enums import ChatType
from hydrogram.helpers import ikb
from hydrogram.types import CallbackQuery

from bot import (
    add_admin,
    add_fs_chat,
    authorized_users_only,
    config,
    del_admin,
    del_fs_chat,
    helper_buttons,
    helper_handlers,
    logger,
    update_force_text_msg,
    update_generate_status,
    update_protect_content,
    update_start_text_msg,
)
from bot.db_funcs.text import (
    get_sponsor_enabled, set_sponsor_enabled,
    get_custom_caption_text, set_custom_caption_text, del_custom_caption_text,
    get_custom_caption_enabled, set_custom_caption_enabled,
    add_start_photo_msg, del_start_photo_msg,
    add_force_photo_msg, del_force_photo_msg,
    get_start_photo_msg, get_force_photo_msg
)
from bot.base import database
from bot.db_funcs import (
    add_content_channel, del_content_channel, get_content_channels,
    set_content_enabled, get_content_enabled,
    set_content_custom_caption, get_content_custom_caption, del_content_custom_caption,
)


@Client.on_callback_query(filters.regex(r"\bcancel\b"))
@authorized_users_only
async def cancel_handler_query(client: Client, query: CallbackQuery) -> None:
    chat_id, user_id = query.message.chat.id, query.from_user.id
    await client.stop_listening(chat_id=chat_id, user_id=user_id)
    await query.message.edit_text("<b>Process has been cancelled!</b>")


@Client.on_callback_query(filters.regex(r"settings"))
@authorized_users_only
async def settings_handler_query(_, query: CallbackQuery) -> None:
    await query.message.edit_text(
        "<b>Bot Settings:</b>", reply_markup=ikb(helper_buttons.Menu)
    )


@Client.on_callback_query(filters.regex(r"close\b"))
@authorized_users_only
async def close_handler_query(_, query: CallbackQuery) -> None:
    try:
        await query.message.reply_to_message.delete()
    except errors.RPCError:
        pass

    await query.message.delete()


@Client.on_callback_query(
    filters.regex(r"menu (generate|protect|admins|fsubs)")
)
@authorized_users_only
async def menu_handler_query(client, query: CallbackQuery) -> None:
    query_data = query.data.split()[1]
    def format_list_items(item_title: str, list_items: list) -> str:
        formatted_items = (
            "".join(
                f"  {i + 1}. <code>{item}</code>\n" for i, item in enumerate(list_items)
            )
            if list_items
            else "  <code>None</code>"
        )
        return f"{item_title}:\n{formatted_items}"

    response_texts = {
        "generate": f"Currently Generate Status is <b>{helper_handlers.generate_status}</b>",
        "protect": f"Currently Protect Content is <b>{helper_handlers.protect_content}</b>",
        "admins": format_list_items(
            "<b>List Admins</b>",
            [admin for admin in helper_handlers.admins if admin != config.OWNER_ID],
        ),
        "fsubs": format_list_items("<b>List F-Subs</b>", helper_handlers.fs_chats),
    }

    if query_data in response_texts:
        await query.message.edit_text(
            response_texts[query_data],
            reply_markup=ikb(getattr(helper_buttons, query_data.capitalize(), [])),
        )


@Client.on_callback_query(filters.regex(r"change (generate|protect)"))
@authorized_users_only
async def change_handler_query(_, query: CallbackQuery) -> None:
    query_data = query.data.split()[1]

    if query_data == "generate":
        await update_generate_status()
        await helper_handlers.generate_status_init()
        logger.info("Generate Status: Changed")
        text = f"Generate Status has been changed to <b>{helper_handlers.generate_status}</b>"
        buttons = helper_buttons.Generate_

    elif query_data == "protect":
        await update_protect_content()
        await helper_handlers.protect_content_init()
        logger.info("Protect Content: Changed")
        text = f"Protect Content has been changed to <b>{helper_handlers.protect_content}</b>"
        buttons = helper_buttons.Protect_

    else:
        return

    await query.message.edit_text(text, reply_markup=ikb(buttons))

@Client.on_callback_query(filters.regex(r"update start_photo"))
@authorized_users_only
async def update_start_photo_handler(client: Client, query: CallbackQuery) -> None:
    await query.message.edit_text(
        "Kirim link foto (URL gambar, bukan text biasa) untuk Set Photo Start!\n\n<b>Timeout:</b> 45s",
        reply_markup=ikb(helper_buttons.Cancel),
    )
    chat_id, user_id = query.message.chat.id, query.from_user.id
    await client.stop_listening(chat_id=chat_id, user_id=user_id)
    try:
        listening = await client.listen(chat_id=chat_id, user_id=user_id, timeout=45)
        user_input = listening.text
        await listening.delete()
    except errors.ListenerStopped:
        await menu_start_handler_query(client, query)
        return
    except errors.ListenerTimeout:
        buttons = await helper_buttons.get_start_buttons()
        await query.message.edit_text(
            "<b>Time limit exceeded! Proses Set Photo Start dibatalkan.</b>", reply_markup=ikb(buttons)
        )
        return
    except Exception:
        await menu_start_handler_query(client, query)
        return
    if not user_input or not (user_input.startswith("http://") or user_input.startswith("https://")):
        buttons = await helper_buttons.get_start_buttons()
        await query.message.edit_text("<b>Link tidak valid! Harus berupa URL gambar (http/https) untuk Set Photo Start.</b>", reply_markup=ikb(buttons))
        return
    from bot.db_funcs.text import add_start_photo_msg
    await add_start_photo_msg(user_input)
    buttons = await helper_buttons.get_start_buttons()
    await query.message.edit_text(f"<b>Set Photo Start berhasil diubah:</b>\n{user_input}", reply_markup=ikb([[('« Back', 'menu start')]]))

@Client.on_callback_query(filters.regex(r"update force_photo"))
@authorized_users_only
async def update_force_photo_handler(client: Client, query: CallbackQuery) -> None:
    await query.message.edit_text(
        "Kirim link foto (URL gambar, bukan text biasa) untuk Set Photo Force!\n\n<b>Timeout:</b> 45s",
        reply_markup=ikb(helper_buttons.Cancel),
    )
    chat_id, user_id = query.message.chat.id, query.from_user.id
    await client.stop_listening(chat_id=chat_id, user_id=user_id)
    try:
        listening = await client.listen(chat_id=chat_id, user_id=user_id, timeout=45)
        user_input = listening.text
        await listening.delete()
    except errors.ListenerStopped:
        await menu_force_handler_query(client, query)
        return
    except errors.ListenerTimeout:
        buttons = await helper_buttons.get_force_buttons()
        await query.message.edit_text(
            "<b>Time limit exceeded! Proses Set Photo Force dibatalkan.</b>", reply_markup=ikb(buttons)
        )
        return
    except Exception:
        await menu_force_handler_query(client, query)
        return
    if not user_input or not (user_input.startswith("http://") or user_input.startswith("https://")):
        buttons = await helper_buttons.get_force_buttons()
        await query.message.edit_text("<b>Link tidak valid! Harus berupa URL gambar (http/https) untuk Set Photo Force.</b>", reply_markup=ikb(buttons))
        return
    from bot.db_funcs.text import add_force_photo_msg
    await add_force_photo_msg(user_input)
    buttons = await helper_buttons.get_force_buttons()
    await query.message.edit_text(f"<b>Set Photo Force berhasil diubah:</b>\n{user_input}", reply_markup=ikb([[('« Back', 'menu force')]]))

@Client.on_callback_query(filters.regex(r"update (start|force)$"))
@authorized_users_only
async def set_text_handler_query(client: Client, query: CallbackQuery) -> None:
    query_data = query.data.split()[1]  # 'start' atau 'force'
    label_text = "Start" if query_data == "start" else "Force"
    await query.message.edit_text(
        f"Kirim pesan untuk Set Text {label_text}!\n\n<b>Timeout:</b> 45s",
        reply_markup=ikb(helper_buttons.Cancel),
    )
    back_buttons = await helper_buttons.get_start_buttons() if query_data == "start" else await helper_buttons.get_force_buttons()
    chat_id, user_id = query.message.chat.id, query.from_user.id
    await client.stop_listening(chat_id=chat_id, user_id=user_id)
    try:
        listening = await client.listen(chat_id=chat_id, user_id=user_id, timeout=45)
        user_input = listening.text
        await listening.delete()
    except errors.ListenerStopped:
        if query_data == "start":
            await menu_start_handler_query(client, query)
        else:
            await menu_force_handler_query(client, query)
        return
    except errors.ListenerTimeout:
        await query.message.edit_text(
            f"<b>Time limit exceeded! Proses Set Text {label_text} dibatalkan.</b>", reply_markup=ikb(back_buttons)
        )
        return
    except Exception:
        if query_data == "start":
            await menu_start_handler_query(client, query)
        else:
            await menu_force_handler_query(client, query)
        return
    if not user_input:
        await query.message.edit_text(f"<b>Invalid! Kirim pesan text untuk Set Text {label_text}.</b>", reply_markup=ikb(back_buttons))
        return
    if query_data == "start":
        await update_start_text_msg(user_input)
        await helper_handlers.start_text_init()
        logger.info("Start Text: Customized")
    else:
        await update_force_text_msg(user_input)
        await helper_handlers.force_text_init()
        logger.info("Force Text: Customized")
    await query.message.edit_text(
        f"<b>Set Text {label_text} berhasil diubah:</b>\n{user_input}",
        reply_markup=ikb([[('« Back', 'menu start')]]),
    )

@Client.on_callback_query(filters.regex(r"delete start_photo"))
@authorized_users_only
async def delete_start_photo_handler(_, query: CallbackQuery):
    from bot.db_funcs.text import del_start_photo_msg
    await del_start_photo_msg()
    await query.message.edit_text("<b>Start Photo berhasil dihapus!</b>", reply_markup=ikb(helper_buttons.Start_))


@Client.on_callback_query(filters.regex(r"delete force_photo"))
@authorized_users_only
async def delete_force_photo_handler(_, query: CallbackQuery):
    from bot.db_funcs.text import del_force_photo_msg
    await del_force_photo_msg()
    await query.message.edit_text("<b>Force Photo berhasil dihapus!</b>", reply_markup=ikb(helper_buttons.Force_))


@Client.on_callback_query(filters.regex(r"menu start"))
@authorized_users_only
async def menu_start_handler_query(_, query: CallbackQuery) -> None:
    from bot.db_funcs.text import get_start_photo_msg
    photo = await get_start_photo_msg()
    text = f"<b>Start Text:</b>\n  {helper_handlers.start_text}\n\n"
    if photo:
        text += f"<b>Start Photo:</b> <code>{photo}</code>"
    else:
        text += "<b>Start Photo:</b> <i>Belum disetting</i>"
    buttons = await helper_buttons.get_start_buttons()
    await query.message.edit_text(text, reply_markup=ikb(buttons))


@Client.on_callback_query(filters.regex(r"menu force"))
@authorized_users_only
async def menu_force_handler_query(_, query: CallbackQuery) -> None:
    from bot.db_funcs.text import get_force_photo_msg
    photo = await get_force_photo_msg()
    text = f"<b>Force Text:</b>\n  {helper_handlers.force_text}\n\n"
    if photo:
        text += f"<b>Force Photo:</b> <code>{photo}</code>"
    else:
        text += "<b>Force Photo:</b> <i>Belum disetting</i>"
    buttons = await helper_buttons.get_force_buttons()
    await query.message.edit_text(text, reply_markup=ikb(buttons))

#################

@Client.on_callback_query(filters.regex(r"add (admin|f-sub)"))
@authorized_users_only
async def add_handler_query(client: Client, query: CallbackQuery) -> None:
    query_data = query.data.split()[1]
    entity_data = "User ID" if query_data == "admin" else "Chat ID"
    await query.message.edit_text(
        f"Send a {entity_data} to add {query_data.title()}\n\n<b>Timeout:</b> 45s",
        reply_markup=ikb(helper_buttons.Cancel),
    )

    buttons = (
        ikb(helper_buttons.Admins_)
        if query_data == "admin"
        else ikb(helper_buttons.Fsubs_)
    )
    chat_id, user_id = query.message.chat.id, query.from_user.id

    try:
        listening = await client.listen(chat_id=chat_id, user_id=user_id, timeout=45)
        await listening.delete()
        new_id = int(listening.text)
    except errors.ListenerStopped:
        await query.message.edit_text(
            "<b>Process has been cancelled!</b>", reply_markup=buttons
        )
        return
    except errors.ListenerTimeout:
        await query.message.edit_text(
            "<b>Time limit exceeded! Process has been cancelled.</b>",
            reply_markup=buttons,
        )
        return
    except ValueError:
        await query.message.edit_text(
            f"<b>Invalid! Just send a {entity_data}.</b>", reply_markup=buttons
        )
        return

    list_ids = (
        helper_handlers.admins if query_data == "admin" else helper_handlers.fs_chats
    )
    if new_id in list_ids:
        await query.message.edit_text(
            f"<b>That's {entity_data} already added!</b>", reply_markup=buttons
        )
        return

    try:
        chat = await client.get_chat(new_id)
        if (query_data == "admin" and chat.type != ChatType.PRIVATE) or (
            query_data == "fsub"
            and chat.type not in [ChatType.SUPERGROUP, ChatType.CHANNEL]
        ):
            raise Exception
    except Exception:
        await query.message.edit_text(
            f"<b>That's {entity_data} isn't valid!</b>", reply_markup=buttons
        )
        return

    if query_data == "admin":
        await add_admin(new_id)
        logger.info("Bot Admins: Updating...")
        await helper_handlers.admins_init()
    else:
        await add_fs_chat(new_id)
        logger.info("Sub. Chats: Updating...")
        await helper_handlers.fs_chats_init()

    await query.message.edit_text(
        f"Added new {query_data.title()}: <code>{new_id}</code>",
        reply_markup=buttons,
    )


@Client.on_callback_query(filters.regex(r"del (admin|f-sub)"))
@authorized_users_only
async def del_handler_query(client: Client, query: CallbackQuery) -> None:
    query_data = query.data.split()[1]
    entity_data = "User ID" if query_data == "admin" else "Chat ID"
    await query.message.edit_text(
        f"Send a {entity_data} to delete {query_data.title()}\n\n<b>Timeout:</b> 45s",
        reply_markup=ikb(helper_buttons.Cancel),
    )

    buttons = (
        ikb(helper_buttons.Admins_)
        if query_data == "admin"
        else ikb(helper_buttons.Fsubs_)
    )
    chat_id, user_id = query.message.chat.id, query.from_user.id

    try:
        listening = await client.listen(chat_id=chat_id, user_id=user_id, timeout=45)
        await listening.delete()
        get_id = int(listening.text)
    except errors.ListenerStopped:
        await query.message.edit_text(
            "<b>Process has been cancelled!</b>", reply_markup=buttons
        )
        return
    except errors.ListenerTimeout:
        await query.message.edit_text(
            "<b>Time limit exceeded! Process has been cancelled.</b>",
            reply_markup=buttons,
        )
        return
    except ValueError:
        await query.message.edit_text(
            f"<b>Invalid! Just send a {entity_data}.</b>", reply_markup=buttons
        )
        return

    list_ids = (
        helper_handlers.admins if query_data == "admin" else helper_handlers.fs_chats
    )
    if get_id not in list_ids:
        await query.message.edit_text(
            f"<b>That's {entity_data} not found!</b>", reply_markup=buttons
        )
        return

    if query_data == "admin":
        if get_id == query.from_user.id:
            await query.message.edit_text(
                f"<b>No rights! That's Yours.</b>", reply_markup=buttons
            )
            return

        await del_admin(get_id)
        logger.info("Bot Admins: Updating...")
        await helper_handlers.admins_init()
    else:
        await del_fs_chat(get_id)
        logger.info("Sub. Chats: Updating...")
        await helper_handlers.fs_chats_init()

    await query.message.edit_text(
        f"The {query_data.title()} has been deleted: <code>{get_id}</code>",
        reply_markup=buttons,
    )


@Client.on_callback_query(filters.regex(r"menu sponsor"))
@authorized_users_only
async def menu_sponsor_handler_query(_, query: CallbackQuery) -> None:
    sponsor_enabled = await get_sponsor_enabled()
    text = f"""
<b>📝 Sponsor Text</b>
{helper_handlers.sponsor_text or '<i>Belum diatur</i>'}

<b>🖼️ Sponsor Photo</b>
{helper_handlers.sponsor_photo or '<i>Belum diatur</i>'}

<b>Status Sponsor:</b> {'🟢 <code>Aktif</code>' if sponsor_enabled else '🔴 <code>Nonaktif</code>'}

<b>Format Teks:</b>
- Mendukung <b>HTML</b> (misal: &lt;b&gt;tebal&lt;/b&gt;, &lt;i&gt;miring&lt;/i&gt;, &lt;a href="url"&gt;link&lt;/a&gt;)
- Contoh: <code>&lt;b&gt;Gabung Channel Sponsor:&lt;/b&gt; &lt;a href="https://t.me/sponsor_channel"&gt;Klik di sini&lt;/a&gt;</code>

<b>Contoh Penggunaan:</b>
- Hanya text: <code>&lt;b&gt;Download file premium di sini:&lt;/b&gt; &lt;a href="https://t.me/username"&gt;Klik di sini&lt;/a&gt;</code>
- Hanya photo: <i>Kirim link gambar saja, tanpa text</i>
- Photo + text: <i>Kirim link gambar dan isi text sponsor (caption) dengan HTML)</i>

<b>Parse Mode:</b> <code>HTML</code>
"""
    await query.message.edit_text(
        text,
        reply_markup=ikb(helper_buttons.get_sponsor_buttons(sponsor_enabled)),
    )


@Client.on_callback_query(filters.regex(r"update sponsor_text"))
@authorized_users_only
async def update_sponsor_text_handler(client: Client, query: CallbackQuery) -> None:
    await query.message.edit_text(
        "Kirim pesan teks sponsor baru!\n\n<b>Timeout:</b> 45s",
        reply_markup=ikb(helper_buttons.Cancel),
    )
    chat_id, user_id = query.message.chat.id, query.from_user.id
    try:
        listening = await client.listen(chat_id=chat_id, user_id=user_id, timeout=45)
        new_text = listening.text
        await listening.delete()
    except errors.ListenerStopped:
        await query.message.edit_text("<b>Proses dibatalkan!</b>", reply_markup=ikb(helper_buttons.Sponsor_))
        return
    except errors.ListenerTimeout:
        await query.message.edit_text("<b>Batas waktu habis!</b>", reply_markup=ikb(helper_buttons.Sponsor_))
        return

    if not new_text:
        await query.message.edit_text("<b>Pesan tidak valid!</b>", reply_markup=ikb(helper_buttons.Sponsor_))
        return

    from bot.db_funcs.text import update_sponsor_text_msg
    await update_sponsor_text_msg(new_text)
    await helper_handlers.sponsor_text_init()
    await query.message.edit_text(
        f"<b>Sponsor Text berhasil diubah:</b>\n{new_text}",
        reply_markup=ikb(helper_buttons.Sponsor_),
    )


@Client.on_callback_query(filters.regex(r"update sponsor_photo"))
@authorized_users_only
async def update_sponsor_photo_handler(client: Client, query: CallbackQuery) -> None:
    await query.message.edit_text(
        "Kirim link foto sponsor baru!\n\n<b>Timeout:</b> 45s",
        reply_markup=ikb(helper_buttons.Cancel),
    )
    chat_id, user_id = query.message.chat.id, query.from_user.id
    try:
        listening = await client.listen(chat_id=chat_id, user_id=user_id, timeout=45)
        new_photo = listening.text
        await listening.delete()
    except errors.ListenerStopped:
        await query.message.edit_text("<b>Proses dibatalkan!</b>", reply_markup=ikb(helper_buttons.Sponsor_))
        return
    except errors.ListenerTimeout:
        await query.message.edit_text("<b>Batas waktu habis!</b>", reply_markup=ikb(helper_buttons.Sponsor_))
        return

    if not new_photo:
        await query.message.edit_text("<b>Link tidak valid!</b>", reply_markup=ikb(helper_buttons.Sponsor_))
        return

    from bot.db_funcs.text import update_sponsor_photo_msg
    await update_sponsor_photo_msg(new_photo)
    await helper_handlers.sponsor_photo_init()
    await query.message.edit_text(
        f"<b>Sponsor Photo berhasil diubah:</b>\n{new_photo}",
        reply_markup=ikb(helper_buttons.Sponsor_),
    )


@Client.on_callback_query(filters.regex(r"delete sponsor_text"))
@authorized_users_only
async def delete_sponsor_text_handler(_, query: CallbackQuery):
    from bot.db_funcs.text import del_sponsor_text_msg
    await del_sponsor_text_msg()
    await helper_handlers.sponsor_text_init()
    await query.message.edit_text(
        "<b>Sponsor Text berhasil dihapus!</b>",
        reply_markup=ikb(helper_buttons.Sponsor_),
    )


@Client.on_callback_query(filters.regex(r"delete sponsor_photo"))
@authorized_users_only
async def delete_sponsor_photo_handler(_, query: CallbackQuery):
    from bot.db_funcs.text import del_sponsor_photo_msg
    await del_sponsor_photo_msg()
    await helper_handlers.sponsor_photo_init()
    await query.message.edit_text(
        "<b>Sponsor Photo berhasil dihapus!</b>",
        reply_markup=ikb(helper_buttons.Sponsor_),
    )


@Client.on_callback_query(filters.regex(r"toggle sponsor"))
@authorized_users_only
async def toggle_sponsor_handler(_, query: CallbackQuery):
    from bot.db_funcs.text import get_sponsor_enabled, set_sponsor_enabled
    sponsor_enabled = await get_sponsor_enabled()
    await set_sponsor_enabled(not sponsor_enabled)
    # Ambil data terbaru
    await helper_handlers.sponsor_text_init()
    await helper_handlers.sponsor_photo_init()
    sponsor_enabled = await get_sponsor_enabled()
    text = f"""
<b>📝 Sponsor Text</b>
{helper_handlers.sponsor_text or '<i>Belum diatur</i>'}

<b>🖼️ Sponsor Photo</b>
{helper_handlers.sponsor_photo or '<i>Belum diatur</i>'}

<b>Status Sponsor:</b> {'🟢 <code>Aktif</code>' if sponsor_enabled else '🔴 <code>Nonaktif</code>'}

<b>Format Teks:</b>
- Mendukung <b>HTML</b> (misal: &lt;b&gt;tebal&lt;/b&gt;, &lt;i&gt;miring&lt;/i&gt;, &lt;a href="url"&gt;link&lt;/a&gt;)
- Contoh: <code>&lt;b&gt;Gabung Channel Sponsor:&lt;/b&gt; &lt;a href="https://t.me/sponsor_channel"&gt;Klik di sini&lt;/a&gt;</code>

<b>Contoh Penggunaan:</b>
- Hanya text: <code>&lt;b&gt;Download file premium di sini:&lt;/b&gt; &lt;a href="https://t.me/username"&gt;Klik di sini&lt;/a&gt;</code>
- Hanya photo: <i>Kirim link gambar saja, tanpa text</i>
- Photo + text: <i>Kirim link gambar dan isi text sponsor (caption) dengan HTML)</i>

<b>Parse Mode:</b> <code>HTML</code>
"""
    await query.message.edit_text(
        text,
        reply_markup=ikb(helper_buttons.get_sponsor_buttons(sponsor_enabled)),
    )


@Client.on_callback_query(filters.regex(r"menu dbchannel"))
@authorized_users_only
async def menu_dbchannel_handler_query(client: Client, query: CallbackQuery):
    # Cek override di database
    doc = await database.get_doc(int(config.BOT_TOKEN.split(":")[0]))
    db_id = doc.get("DATABASE_CHAT_ID_OVERRIDE", [config.DATABASE_CHAT_ID])[0] if doc else config.DATABASE_CHAT_ID
    try:
        chat = await client.get_chat(db_id)
        name = chat.title or chat.username or "-"
    except Exception:
        name = "<i>Tidak ditemukan</i>"
    text = f"<b>🗄️ DB Channel</b>\nID: <code>{db_id}</code>\nNama: <b>{name}</b>"
    await query.message.edit_text(
        text,
        reply_markup=ikb(helper_buttons.DBChannel),
    )


@Client.on_callback_query(filters.regex(r"update dbchannel"))
@authorized_users_only
async def update_dbchannel_handler(client: Client, query: CallbackQuery):
    await query.message.edit_text(
        "Kirim ID channel baru!\n\n<b>Timeout:</b> 45s",
        reply_markup=ikb(helper_buttons.DBChannel_),
    )
    chat_id, user_id = query.message.chat.id, query.from_user.id
    try:
        listening = await client.listen(chat_id=chat_id, user_id=user_id, timeout=45)
        new_id = int(listening.text)
        await listening.delete()
    except Exception:
        await query.message.edit_text("<b>Proses dibatalkan atau ID tidak valid!</b>", reply_markup=ikb(helper_buttons.DBChannel_))
        return
    # Validasi: pastikan bot admin di channel
    try:
        chat = await client.get_chat(new_id)
        # Cek bot admin, dst...
        await database.clear_value(int(config.BOT_TOKEN.split(":")[0]), "DATABASE_CHAT_ID_OVERRIDE")
        await database.add_value(int(config.BOT_TOKEN.split(":")[0]), "DATABASE_CHAT_ID_OVERRIDE", new_id)
        await query.message.edit_text(f"<b>DB Channel berhasil diganti ke:</b>\nID: <code>{new_id}</code>\nNama: <b>{chat.title or chat.username or '-'}</b>", reply_markup=ikb(helper_buttons.DBChannel_))
    except Exception:
        await query.message.edit_text("<b>Gagal! Pastikan bot admin di channel tersebut.</b>", reply_markup=ikb(helper_buttons.DBChannel_))


@Client.on_callback_query(filters.regex(r"reset dbchannel"))
@authorized_users_only
async def reset_dbchannel_handler(_, query: CallbackQuery):
    await database.clear_value(int(config.BOT_TOKEN.split(":")[0]), "DATABASE_CHAT_ID_OVERRIDE")
    await query.message.edit_text("<b>DB Channel direset ke default dari config!</b>", reply_markup=ikb(helper_buttons.DBChannel_))


@Client.on_callback_query(filters.regex(r"menu custom_caption"))
@authorized_users_only
async def menu_custom_caption_handler(_, query: CallbackQuery):
    enabled = await get_custom_caption_enabled()
    template = await get_custom_caption_text()
    status = "🟢 Aktif" if enabled else "🔴 Nonaktif"
    text = f"""
<b>📝 Custom Caption</b>
Status: <b>{status}</b>

<b>Template:</b>
<code>{template or 'Belum diatur'}</code>

<b>Placeholder yang bisa digunakan:</b>
- <code>{{original_caption}}</code> = Caption asli file (jika ada)
- <code>{{link_file}}</code> = Link hasil generate file

<b>Format Teks:</b>
- Mendukung <b>HTML</b> (misal: <b>tebal</b>, <i>miring</i>, <a href=\"url\">link</a>)
- Contoh: <code>&lt;b&gt;File dari bot:&lt;/b&gt; {{original_caption}} &lt;a href=\"{{link_file}}\"&gt;[Link]&lt;/a&gt;</code>
"""
    await query.message.edit_text(
        text,
        reply_markup=ikb(helper_buttons.CustomCaption),
    )


@Client.on_callback_query(filters.regex(r"update custom_caption"))
@authorized_users_only
async def update_custom_caption_handler(client: Client, query: CallbackQuery):
    await query.message.edit_text(
        "Kirim template caption baru!\n\nGunakan <code>{original_caption}</code> untuk caption asli.",
        reply_markup=ikb(helper_buttons.CustomCaption_),
    )
    chat_id, user_id = query.message.chat.id, query.from_user.id
    try:
        listening = await client.listen(chat_id=chat_id, user_id=user_id, timeout=45)
        new_caption = listening.text
        await listening.delete()
    except Exception:
        await query.message.edit_text("<b>Proses dibatalkan!</b>", reply_markup=ikb(helper_buttons.CustomCaption_))
        return
    await set_custom_caption_text(new_caption)
    await query.message.edit_text("<b>Custom caption berhasil diubah!</b>", reply_markup=ikb(helper_buttons.CustomCaption_))


@Client.on_callback_query(filters.regex(r"delete custom_caption"))
@authorized_users_only
async def delete_custom_caption_handler(_, query: CallbackQuery):
    await del_custom_caption_text()
    await query.message.edit_text("<b>Custom caption berhasil dihapus!</b>", reply_markup=ikb(helper_buttons.CustomCaption_))


@Client.on_callback_query(filters.regex(r"toggle custom_caption"))
@authorized_users_only
async def toggle_custom_caption_handler(_, query: CallbackQuery):
    enabled = await get_custom_caption_enabled()
    await set_custom_caption_enabled(not enabled)
    # Langsung refresh menu custom caption tanpa pesan konfirmasi
    await menu_custom_caption_handler(_, query)


# === MENU KONTEN ===
@Client.on_callback_query(filters.regex(r"menu content"))
@authorized_users_only
async def menu_content_handler_query(client, query: CallbackQuery):
    await helper_handlers.content_channels_init()
    await helper_handlers.content_enabled_init()
    await helper_handlers.content_custom_caption_init()
    content_enabled = helper_handlers.content_enabled
    content_channels = helper_handlers.content_channels
    custom_caption = helper_handlers.content_custom_caption
    status = "🟢 ON" if content_enabled else "🔴 OFF"
    text = (
        "<b>Fitur Konten</b>\n"
        "Selain menyimpan file ke DB Channel, jika fitur ini aktif, bot akan meneruskan file ke semua channel konten yang didaftarkan.\n"
        "Mendukung custom caption (HTML, {original_caption}, {link_file}).\n"
        "\n<b>Status Konten:</b> " + status +
        f"\n<b>Custom Caption:</b> <code>{custom_caption or 'Belum disetting'}</code>"
    )
    buttons = helper_buttons.get_content_buttons(content_enabled, content_channels)
    await query.message.edit_text(text, reply_markup=ikb(buttons))

# === TOGGLE ON/OFF KONTEN ===
@Client.on_callback_query(filters.regex(r"toggle content"))
@authorized_users_only
async def toggle_content_handler_query(_, query: CallbackQuery):
    content_channels = await get_content_channels()
    if not content_channels:
        await query.message.edit_text("<b>Belum ada channel konten yang didaftarkan!</b>", reply_markup=ikb([[('Back', 'menu content')]]))
        return
    enabled = await get_content_enabled()
    await set_content_enabled(not enabled)
    await helper_handlers.content_enabled_init()
    await menu_content_handler_query(_, query)

# === TAMBAH CHANNEL KONTEN ===
@Client.on_callback_query(filters.regex(r"content add_channel"))
@authorized_users_only
async def content_add_channel_handler(client, query: CallbackQuery):
    await query.message.edit_text(
        "Kirim ID channel konten (harus channel, bot harus admin).\n\n<b>Timeout:</b> 45s",
        reply_markup=ikb([[('Batal', 'menu content')]]),
    )
    chat_id, user_id = query.message.chat.id, query.from_user.id
    try:
        listening = await client.listen(chat_id=chat_id, user_id=user_id, timeout=45)
        new_id = int(listening.text)
        await listening.delete()
    except Exception:
        await query.message.edit_text("<b>Proses dibatalkan atau ID tidak valid!</b>", reply_markup=ikb([[('Back', 'menu content')]]))
        return
    # Validasi: pastikan bot admin di channel
    try:
        chat = await client.get_chat(new_id)
        if chat.type.name != 'CHANNEL':
            raise Exception
        await add_content_channel(new_id)
        await helper_handlers.content_channels_init()
        await query.message.edit_text(f"<b>Channel konten berhasil ditambahkan:</b>\nID: <code>{new_id}</code>\nNama: <b>{chat.title or chat.username or '-'}" , reply_markup=ikb([[('Back', 'menu content')]]))
    except Exception:
        await query.message.edit_text("<b>Gagal! Pastikan ID channel valid dan bot admin di channel tersebut.</b>", reply_markup=ikb([[('Back', 'menu content')]]))

# === TOMBOL CHANNEL (UNTUK HAPUS) ===
@Client.on_callback_query(filters.regex(r"content ch_(\-?\d+)"))
@authorized_users_only
async def content_channel_button_handler(_, query: CallbackQuery):
    ch_id = int(query.data.split('_')[-1])
    ch_name = helper_handlers.content_channels.get(ch_id, str(ch_id))
    text = f"Konfirmasi channel <b>{ch_name}</b> (<code>{ch_id}</code>) akan dihapus?"
    buttons = helper_buttons.get_content_confirm_delete_buttons(ch_id)
    await query.message.edit_text(text, reply_markup=ikb(buttons))

# === KONFIRMASI HAPUS CHANNEL ===
@Client.on_callback_query(filters.regex(r"content del_confirm_(\-?\d+)"))
@authorized_users_only
async def content_channel_delete_confirm_handler(_, query: CallbackQuery):
    ch_id = int(query.data.split('_')[-1])
    await del_content_channel(ch_id)
    await helper_handlers.content_channels_init()
    # Jika tidak ada channel konten tersisa, set status konten OFF
    if not helper_handlers.content_channels:
        from bot.db_funcs import set_content_enabled
        await set_content_enabled(False)
        await helper_handlers.content_enabled_init()
    await query.message.edit_text("<b>Channel konten berhasil dihapus!</b>", reply_markup=ikb([[('Back', 'menu content')]]))

# === CUSTOM CAPTION KONTEN ===
@Client.on_callback_query(filters.regex(r"content custom_caption"))
@authorized_users_only
async def content_custom_caption_menu_handler(_, query: CallbackQuery):
    template = await get_content_custom_caption()
    text = (
        "<b>Custom Caption Konten</b>\n"
        f"Template saat ini:\n<code>{template or 'Belum diatur'}</code>\n\n"
        "<b>Placeholder yang bisa digunakan:</b>\n"
        "- <code>{original_caption}</code> = Caption asli file (jika ada)\n"
        "- <code>{link_file}</code> = Link hasil generate file\n\n"
        "<b>Contoh Penggunaan:</b>\n"
        "- Hanya link: <code>{link_file}</code>\n"
        "- HTML: <code>&lt;a href=\"{link_file}\"&gt;Download di sini&lt;/a&gt;</code>\n"
        "- Kombinasi: <code>&lt;b&gt;File:&lt;/b&gt; {original_caption} &lt;a href=\"{link_file}\"&gt;[Link]&lt;/a&gt;</code>\n\n"
        "<b>Format Teks:</b> Mendukung <b>HTML</b>"
    )
    await query.message.edit_text(text, reply_markup=ikb([[('Ubah Caption', 'content set_custom_caption')], [('Batal', 'menu content')]]))

@Client.on_callback_query(filters.regex(r"content set_custom_caption"))
@authorized_users_only
async def content_custom_caption_set_handler(client, query: CallbackQuery):
    await query.message.edit_text(
        "Kirim template custom caption baru untuk channel konten!\n\nGunakan <code>{original_caption}</code> dan <code>{link_file}</code> jika perlu.",
        reply_markup=ikb(helper_buttons.ContentCustomCaption_),
    )
    chat_id, user_id = query.message.chat.id, query.from_user.id
    try:
        listening = await client.listen(chat_id=chat_id, user_id=user_id, timeout=45)
        new_caption = listening.text
        await listening.delete()
    except Exception:
        await query.message.edit_text("<b>Proses dibatalkan!</b>", reply_markup=ikb(helper_buttons.ContentCustomCaption_))
        return
    await set_content_custom_caption(new_caption)
    await helper_handlers.content_custom_caption_init()
    await query.message.edit_text("<b>Custom caption konten berhasil diubah!</b>", reply_markup=ikb(helper_buttons.ContentCustomCaption_))

@Client.on_callback_query(filters.regex(r"menu content"))
@authorized_users_only
async def menu_content_back_handler(_, query: CallbackQuery):
    await menu_content_handler_query(_, query)


