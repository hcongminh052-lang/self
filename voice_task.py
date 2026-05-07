import discord
import asyncio
from discord.ext import tasks

HUB_CHANNEL_ID = 1490301863692865597 

@tasks.loop(seconds=30)
async def voice_keepalive_loop(bot):
    if not bot.is_ready():
        return

    hub_channel = bot.get_channel(HUB_CHANNEL_ID)
    if not hub_channel:
        return

    # Lấy voice_client trong server của Hub
    vc = discord.utils.get(bot.voice_clients, guild=hub_channel.guild)

    # Nếu hoàn toàn không ở trong voice
    if vc is None or not vc.is_connected():
        print("📡 Phát hiện Bot đứng ngoài, đang vào lại Hub...")
        try:
            await hub_channel.connect()
        except Exception as e:
            print(f"❌ Lỗi kết nối lại: {e}")
    
    # Nếu đang ở một mình trong phòng JTC (thường phòng sẽ bị xóa)
    elif len(vc.channel.members) == 1 and vc.channel.id != HUB_CHANNEL_ID:
        print("🔄 Phòng trống, quay về Hub để tạo phòng mới...")
        try:
            await vc.disconnect(force=True)
            await asyncio.sleep(2)
            await hub_channel.connect()
        except:
            pass

async def check_voice_status(bot, member, before, after):
    # Khi bot bị văng, gọi loop kiểm tra ngay lập tức
    if member.id == bot.user.id and after.channel is None:
        await asyncio.sleep(2)
        await voice_keepalive_loop(bot)
