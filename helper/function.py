import asyncio
import contextlib
import logging

from telethon import Button, TelegramClient, types
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
from telethon.tl.functions.contacts import AddContactRequest
from telethon.tl.functions.messages import AddChatUserRequest
from Eaglebot import Config, eagle
from Eaglebot.core.managers import edit_or_reply
from Eaglebot.helpers import _eagleutils

from .vcp_helper import EagleVc

LOGS = logging.getLogger(__name__)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)

if vc_session := Config.VC_SESSION:
    vc_client = TelegramClient(
        StringSession(vc_session), Config.APP_ID, Config.API_HASH
    )
else:
    vc_client = eagle

vc_client.__class__.__module__ = "telethon.client.telegramclient"
vc_player = EagleVc(vc_client)


@vc_player.app.on_closed_voice_chat()
async def on_closed_vc(_, update):
    await _catutils.runcmd("rm -rf temp")
    vc_player.clear_vars()
    if not vc_player.CLEANMODE:
        return
    for event in vc_player.EVENTS:
        with contextlib.suppress(Exception):
            await event.delete()


@vc_player.app.on_stream_end()
async def handler(_, update):
    event = False
    if vc_player.REPEAT:
        return await vc_player.repeat()
    if not vc_player.PLAYLIST:
        if vc_player.CHAT_ID and not vc_player.SILENT:
            return await vc_player.leave_vc()
        else:
            return
    resp = await vc_player.handle_next(update)
    print("In the end it doesnt even matter")
    buttons = [
        [
            Button.inline("⏮ Prev", data="previousvc"),
            Button.inline("⏸ Pause", data="pausevc"),
            Button.inline("⏭ Next", data="skipvc"),
        ],
        [
            Button.inline("Repeat ❌", data="repeatvc"),
            Button.inline("〣 Mainmenu", data="menuvc"),
        ],
        [
            Button.inline("🗑 Close", data="vc_close"),
        ],
    ]
    if vc_player.BOTMODE:
        if resp and type(resp) is list:
            caption = resp[1].split(f"\n\n")[1] if f"\n\n" in resp[1] else resp[1]
            event = await eagle.tgbot.send_file(
                vc_player.CHAT_ID, file=resp[0], caption=caption, buttons=buttons
            )
        elif resp and type(resp) is str:
            resp = resp.split(f"\n\n")[1] if f"\n\n" in resp else resp
            event = await eagle.tgbot.send_message(
                vc_player.CHAT_ID, resp, buttons=buttons
            )
    else:
        try:
            results = await eagle.inline_query(Config.TG_BOT_USERNAME, "vcplayer")
            event = await results[0].click(vc_player.CHAT_ID, hide_via=True)
        except Exception:
            if resp and type(resp) is list:
                caption = resp[1].split(f"\n\n")[1] if f"\n\n" in resp[1] else resp[1]
                event = await eagle.send_file(
                    vc_player.CHAT_ID, file=resp[0], caption=caption, buttons=buttons
                )
            elif resp and type(resp) is str:
                resp = resp.split(f"\n\n")[1] if f"\n\n" in resp else resp
                event = await eagle.send_message(
                    vc_player.CHAT_ID, resp, buttons=buttons
                )
    if vc_player.CLEANMODE and event:
        vc_player.EVENTS.append(event)


async def check_vcassis(event):
    chat = await eagle.get_entity(event.chat_id)
    participants = await eagle.get_participants(chat)
    assis = await vc_player.client.get_me()
    cat_ub = await eagle.get_me()
    get_id = assis.id
    ids = [int(users.id) for users in participants]
    if get_id not in ids:
        await event.edit("VC assistant will be joining shortly...")
        if isinstance(chat, types.Chat):
            chat.username = None
        if username := chat.username:
            try:
                await vc_player.client(JoinChannelRequest(username))
                await event.edit(f"VC assistant Joined {chat.title} successfully.")
            except Exception:
                await event.edit("Failed to join this chat.")
                return False
        else:
            try:
                await event.client(InviteToChannelRequest(chat.id, [get_id]))
            except Exception:
                try:
                    await vc_player.client(
                        AddContactRequest(
                            id=cat_ub.id,
                            first_name="VC",
                            last_name="Assistant",
                            phone="zarox",
                        )
                    )
                    await eagle(
                        AddContactRequest(
                            id=assis.id,
                            first_name="EAGLE",
                            last_name="",
                            phone="zarox",
                        )
                    )
                    await event.client(InviteToChannelRequest(chat.id, [get_id]))
                except TypeError:
                    await event.client(AddChatUserRequest(chat.id, get_id, fwd_limit=1))
                except Exception:
                    await event.edit(
                        "Failed to add VC assistant. Please provide add members right or invite manually."
                    )
                    return False
    return True


async def vc_reply(event, text, file=False, firstmsg=False, dlt=False, **kwargs):
    me = await eagle.get_me()
    if vc_player.BOTMODE:
        try:
            if file:
                catevent = await eagle.tgbot.send_file(
                    event.chat_id, file=file, caption=text, **kwargs
                )
            else:
                catevent = (
                    await eagle.tgbot.send_message(event.chat_id, text, **kwargs)
                    if firstmsg
                    else await event.edit(text, **kwargs)
                )
        except Exception:
            return await event.reply(
                f"Please disable Bot Mode or Invite {Config.TG_BOT_USERNAME} to the chat"
            )
    elif file:
        try:
            results = await event.client.inline_query(
                Config.TG_BOT_USERNAME, "vcplayer"
            )
            catevent = await results[0].click(event.chat_id, hide_via=True)
        except Exception:
            catevent = await eagle.send_file(
                event.chat_id, file=file, caption=text, **kwargs
            )
    elif vc_player.PUBLICMODE:
        catevent = (
            await eagle.send_message(event.chat_id, text, **kwargs)
            if firstmsg and event.sender_id != me.id
            else await event.edit(text, **kwargs)
        )
    else:
        catevent = await edit_or_reply(event, text)
    if dlt:
        await asyncio.sleep(dlt)
        return await catevent.delete()
    if vc_player.CLEANMODE and not firstmsg:
        vc_player.EVENTS.append(catevent)
    else:
        return catevent


async def sendmsg(event, res):
    buttons = buttons = [
        [
            Button.inline("⏮ Prev", data="previousvc"),
            Button.inline("⏸ Pause", data="pausevc"),
            Button.inline("⏭ Next", data="skipvc"),
        ],
        [
            Button.inline("🔁 repeat", data="repeatvc"),
            Button.inline("≡ Mainmenu", data="menuvc"),
        ],
        [
            Button.inline("🗑 close", data="vc_close0"),
        ],
    ]
    if res:
        if isinstance(res, list):
            await event.delete()
            event = await vc_reply(event, res[1], file=res[0], buttons=buttons)
        elif isinstance(res, tuple):
            event = await vc_reply(event, res[0], dlt=15)
        elif isinstance(res, str):
            event = await vc_reply(event, res, buttons=buttons)


asyncio.create_task(vc_player.start())
