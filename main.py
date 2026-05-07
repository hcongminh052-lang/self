import json
import os
import asyncio
import random
import signal
import traceback
import discord
from discord.ext import commands

from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


prefix = "!"
intents = discord.Intents.all()
TOKEN = os.getenv["DISCORD_TOKEN"]
bot = commands.Bot(command_prefix=prefix,
                   help_command=None,
                   case_insensitive=True,
                   intents=intents,
                   self_bot = True)
channel_checkpoints = {}
checkpoint_file = "checkpoints1.json"

def shutdown_handler():
    print("Saving checkpoint before exit...")
    save_checkpoints()

signal.signal(signal.SIGINT, lambda s, f: shutdown_handler())

def load_checkpoints():
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r") as f:
            return json.load(f)
    return {}

def save_checkpoints():
    with open(checkpoint_file, "w") as f:
        json.dump(channel_checkpoints, f)

channel_checkpoints = load_checkpoints()

current_delay = 0.35
min_delay = 0.2
max_delay = 1.5

async def safe_add_reaction(msg, em, channel_id):
    global current_delay

    for lan_thu in range(5):
        try:
            await msg.add_reaction(em)
            print(f"[{channel_id}] + {em} -> {msg.id}")

            current_delay = max(current_delay * 1.01, 1.1)
            await asyncio.sleep(current_delay + random.uniform(0.2, 0.6))
            return True

        except discord.HTTPException as e:

            # RATE LIMIT
            if e.status == 429:
                wait_time = getattr(e, "retry_after", 2)
                current_delay = min(current_delay * 1.35, max_delay)

                print(f"[{channel_id}] ⏳ RATE LIMIT {wait_time}s | delay={round(current_delay,2)}")
                await asyncio.sleep(wait_time + random.uniform(1, 2))
                continue

            # MESSAGE KHÔNG CHO REACT / LOCK / PERMISSION RIÊNG
            elif e.status == 403:
                print(f"[{channel_id}] 🚫 403 skip msg {msg.id}")
                await asyncio.sleep(random.uniform(1.5, 2.5))
                return False

            # UNKNOWN MESSAGE / MESSAGE DIE
            elif e.status == 404:
                print(f"[{channel_id}] ❓ 404 msg mất {msg.id}")
                return False

            if "cloudflare" in str(e).lower():
                print(f"[{channel_id}] ☁️ Cloudflare ngủ 90s")
                await asyncio.sleep(90)
                return False

            print(f"[{channel_id}] HTTP {e.status}: {e}")
            return False

        except Exception as e:
            print(f"[{channel_id}] Lỗi khác {e}")
            return False

    return False

async def process_channel(channel_id, emoji_ids):
    global channel_checkpoints
    channel = bot.get_channel(channel_id)
    if not channel:
        print("Khong tim thay kenh:", channel_id)
        return

    data = channel_checkpoints.get(str(channel_id), {})
    if isinstance(data, dict):
        last_message_id = data.get("last_id")
        emoji_index = data.get("emoji_index", 0)
    else:
        last_message_id = data
        emoji_index = 0

    BATCH_SIZE = 2
    emoji_batch_raw = emoji_ids[emoji_index:emoji_index + BATCH_SIZE]
    emoji_batch = []
    for eid in emoji_batch_raw:
        if isinstance(eid, str):
            emoji_batch.append(eid)
        else:
            em = bot.get_emoji(eid)
            if em:
                emoji_batch.append(em)
            else:
                print(f"[{channel_id}] ❌ Emoji lỗi: {eid}")

    print(f"[{channel_id}] Emoji batch: {emoji_batch}")
    if last_message_id and str(last_message_id).isdigit():
        history = channel.history(
            limit=1000,
            before=discord.Object(id=int(last_message_id))
        )
        print(f"[{channel_id}] Resume từ {last_message_id}")
    else:
        history = channel.history(limit=1000)
        print(f"[{channel_id}] Quét mới")

    new_checkpoint = last_message_id
    tong_quet = 0
    async for msg in history:
        new_checkpoint = msg.id
        tong_quet += 1
        my_reactions = [str(r.emoji) for r in msg.reactions if r.me]
        for em in emoji_batch:
            if str(em) in my_reactions:
                continue

            await safe_add_reaction(msg, em, channel_id)

        await asyncio.sleep(random.uniform(0.2, 0.5))
        if tong_quet % 20 == 0:
            channel_checkpoints[str(channel_id)] = {
                "last_id": str(new_checkpoint),
                "emoji_index": emoji_index
            }
            save_checkpoints()
            print(f"[{channel_id}] 💾 Saved checkpoint {new_checkpoint}")

    next_index = emoji_index + BATCH_SIZE
    if next_index >= len(emoji_ids):
        next_index = 0

    channel_checkpoints[str(channel_id)] = {
        "last_id": str(new_checkpoint),
        "emoji_index": next_index
    }
    save_checkpoints()
    print(f"[{channel_id}] ✅ DONE | next emoji index: {next_index}")

def listToString(s):
    str1 = ""
    for i in s:
        str1 += i
        str1 += " "
    return str1

@bot.command()
async def cmd(ctx):
    msg = (
        "➤ !allchanels | !ac\n"
        "└ Hiển thị toàn bộ các kênh trong máy chủ.\n\n"

        "➤ !showhiddenvoice | !shdv\n"
        "└ Quét các kênh thoại bị ẩn và hiển thị người đang tham gia.\n\n"

        "➤ !showvoice | !sv\n"
        "└ Hiển thị các kênh thoại công khai cùng thành viên hiện diện.\n\n"

        "➤ !webhook | !wh\n"
        "└ Gửi tin nhắn bằng webhook mang tên/avatar của chính người dùng dùng lệnh.\n\n"

        "➤ !fake \n"
        "└ Giả danh một member khác trong server để gửi tin.\n\n"

        "➤ !clearwebhook | !cw\n"
        "└ Xoá toàn bộ webhook trong server.\n\n"
    )

    await ctx.send(msg)

@bot.command()
async def kao(ctx):
    await ctx.message.delete()
    await ctx.send("┬─┬ノ( º _ ºノ)")

@bot.command(aliases = ["ac"])
async def allchanels(ctx):
    vao_duoc = ""
    khong_vao_duoc = ""
    dem1 = 0
    dem2 = 0
    for ch in ctx.guild.channels:
        perms = ch.permissions_for(ctx.author)
        if perms.view_channel:
            dem1 += 1
            vao_duoc += f"[{dem1}] {ch.name.lower()}\n"
        else:
            dem2 += 1
            khong_vao_duoc += f"[{dem2}] {ch.name.lower()}\n"

    msg = "**=== KÊNH VÀO ĐƯỢC ===**\n"
    msg += vao_duoc if vao_duoc else "Không có\n"
    msg += "\n**=== KÊNH KHÔNG VÀO ĐƯỢC ===**\n"
    msg += khong_vao_duoc if khong_vao_duoc else "Không có"
    await ctx.send(msg)

@bot.command(aliases = ["shdv"])
async def showhiddenvoice(ctx):
    ds_voice = []
    for i in ctx.guild.channels:
        if i.type == discord.ChannelType.voice:
            if i.permissions_for(ctx.guild.me).connect == False:
                voice_channel = discord.utils.get(ctx.guild.channels, id=i.id)
                members = voice_channel.members
                ten_members = '\n - - -'.join([x.name for x in members])
                ds_voice.append(members)
                if ten_members.strip() == "":
                    await ctx.send(f"**[Hidden]: ** {voice_channel.name}\n> *No members inside*")
                else:
                    await ctx.send(f"**[Hidden]: ** {voice_channel.name}\n> {ten_members}")
    await ctx.send(f"**Succesfully: ** {len(ds_voice)} **hidden channels**")

@bot.command(aliases = ["sv"])
async def showvoice(ctx):
    ds_voice = []
    for i in ctx.guild.channels:
        if i.type == discord.ChannelType.voice:
            if i.permissions_for(ctx.guild.me).connect == True:
                voice_channel = discord.utils.get(ctx.guild.channels, id=i.id)
                members = voice_channel.members
                ten_members = '\n - - -'.join([x.name for x in members])
                ds_voice.append(members)
                if ten_members.strip() == "":
                    await ctx.send(f"**[Chanels]: ** {voice_channel.name}\n> *No members inside*")
                else:
                    await ctx.send(f"**[Chanels]: ** {voice_channel.name}\n> {ten_members}")
    await ctx.send(f"**Succesfully: ** {len(ds_voice)} **channels**")

@bot.command(aliases = ["wh"])
async def webhook(ctx, *args):
    text = listToString(args)
    try:
        webhook = await ctx.channel.create_webhook(name = ctx.author.name)
        await webhook.send(text, username=ctx.author.name, avatar_url=ctx.author.avatar_url)
        await webhook.delete()
    except:
        await ctx.send("Lỗi khi chạy")

@bot.command()
async def fake(ctx, mem:discord.Member, *args):
    await ctx.message.delete()
    text = listToString(args)
    try:
        webhook = await ctx.channel.create_webhook(name = mem.name)
        if mem.nick != mem.name:
            await webhook.send(text, username=mem.nick, avatar_url=mem.avatar_url)
        else:
            await webhook.send(text, username=mem.name, avatar_url=mem.avatar_url)
        await webhook.delete()
    except:
        await ctx.send("Lỗi khi chạy")

@bot.command(aliases = ["cw"])
async def clearwebhook(ctx):
    webhooks = await ctx.guild.webhooks()
    for webhook in webhooks:
        try:
            await webhook.delete()
        except:
            continue
    await ctx.send("Done!")

@bot.command(aliases = ["clm"])
async def clearmessage(ctx, soluong):
    await ctx.message.delete()
    demtn = 0
    async for message in ctx.channel.history(limit=9999):
        await message.delete()
        await asyncio.sleep(1)
        demtn += 1
    await ctx.send(f":wastebasket: Đã xoá {demtn} tin nhắn!")

@bot.command(aliases = ["dlm"])
async def deletmessage(ctx, soluong):
    await ctx.message.delete()
    if int(soluong) == 0:
        await ctx.send("Warning: Không thể xoá 0 tin nhắn")
    elif 1 <= int(soluong) <= 9999:
        gioihan = int(soluong)
        demtn = 0
        async for message in ctx.channel.history(limit=9999):
            if message.author == bot.user:
                await message.delete()
                await asyncio.sleep(1)
                demtn += 1
            if demtn == gioihan:
                break
        await ctx.send(f":wastebasket: Đã xoá {demtn} tin nhắn!")
    else:
        await ctx.send("Warning: Vượt quá giới hạn xoá tin nhắn")

last_message_id = None
@bot.command(aliases = ["or"])
async def oldreact(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    react_config = {
        1229716511401316404: [
            1194533745286451271,
            1194533743109611550,
            1194196518228463646,
            1194196538067529802,
            1194200700696137748,
            1286272027141083137
        ],
        1229716774195433472: [
            1194533745286451271,
            1194533743109611550,
            1194196518228463646,
            1194196538067529802,
            1194200700696137748,
            1286272027141083137,
            "❤️",
            1194196216985169951,
            1194196752803315772,
            1195014108085489866,
            1211715677497331732,
            1279164617117143113
        ],
        1380893805162528878: [
            1194533745286451271,
            "❤️",
            1194196216985169951,
            1194196752803315772,
            1195014108085489866,
            1211715677497331732,
            1279164617117143113
        ],
        1302993772006609007: [
            1194533745286451271,
            1194196216985169951,
            1211715677497331732,
            1195014108085489866,
            1196006750403440710,
            1196008739665358858,
            1194281783659864114
        ],
        1281154949077798912: [
            1194533745286451271,
            1194196216985169951,
            1211715677497331732,
            1195014108085489866,
            1196006750403440710,
            1196008739665358858,
            1194281783659864114
        ],
        1281155099590135878: [
            1194533745286451271,
            "❤️",
            1194196216985169951,
            1194196752803315772,
            1195014108085489866,
            1211715677497331732,
            1279164617117143113
        ],
        1281155158922760273: [
            1194533745286451271,
            1194196216985169951,
            1211715677497331732,
            1195014108085489866,
            1196006750403440710,
            1196008739665358858,
            1194281783659864114
        ],
        1281155174253199444: [
            1194533745286451271,
            "❤️",
            1194196216985169951,
            1194196752803315772,
            1195014108085489866,
            1211715677497331732,
            1279164617117143113
        ],
        1281155289625923676: [
            1194533745286451271,
            1194196216985169951,
            1211715677497331732,
            1195014108085489866,
            1196006750403440710,
            1196008739665358858,
            1194281783659864114
        ],
        1281155308684574723: [
            1194533745286451271,
            "❤️",
            1194196216985169951,
            1194196752803315772,
            1195014108085489866,
            1211715677497331732,
            1279164617117143113
        ]
    }

    print("========== FINAL FORM START ==========")
    semaphore = asyncio.Semaphore(1)
    async def limited_process(cid, eids):
        async with semaphore:
            await process_channel(cid, eids)

    tasks = [limited_process(cid, eids) for cid, eids in react_config.items()]
    await asyncio.gather(*tasks)

    print("========== FINAL FORM DONE ==========")

@bot.command()
async def allem(ctx):
    await ctx.message.delete()
    print("Tong emoji trong server:", len(ctx.guild.emojis))

    for em in ctx.guild.emojis:
        print(em.name, em.id)

farm_exp = False
@bot.command(aliases=["se"])
async def startexp(ctx):
    await ctx.message.delete()
    global farm_exp
    farm_exp = True
    channel = bot.get_channel(1381302690335952988)

    emoji_list = [em for em in ctx.guild.emojis if not em.animated]

    print("===== BAT DAU CAY EXP =====")
    print("Emoji thuong load duoc:", len(emoji_list))

    while farm_exp:
        try:
            so_luong = random.randint(1, 1)
            chosen = random.sample(emoji_list, so_luong)
            text = "".join(str(em) for em in chosen)
            await channel.send(text)
            print("Da gui:", text)
        except Exception as e:
            print("Loi gui:", e)
        await asyncio.sleep(random.randint(60, 90))

@bot.command(aliases=["xe"])
async def stopexp(ctx):
    await ctx.message.delete()
    global farm_exp
    farm_exp = False
    print("===== DA DUNG CAY EXP =====")

bot.run(TOKEN, bot = False)
