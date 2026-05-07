import discord
import asyncio
from discord.ext import tasks

HUB_CHANNEL_ID = 1490301863692865597 

async def join_voice_channel(bot):
    hub_channel = bot.get_channel(HUB_CHANNEL_ID)
    if not hub_channel:
        print("❌ Không tìm thấy kênh Hub với ID đã cung cấp!")
        return

    # Lấy trạng thái voice hiện tại của bot trong server đó
    vc = discord.utils.get(bot.voice_clients, guild=hub_channel.guild)
    
    # Trường hợp 1: Bot chưa vào voice
    if not vc:
        try:
            print(f"📡 Đang vào Hub để tạo phòng...")
            await hub_channel.connect()
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    
    # Trường hợp 2: Bot đang ở trong một kênh voice
    else:
        # Nếu bot đang đứng ở kênh Hub mà không được move (lỗi bot JTC)
        # Hoặc bot đang ở một mình trong phòng cũ (phòng đã chết)
        if vc.channel.id == HUB_CHANNEL_ID or len(vc.channel.members) == 1:
            print("🔄 Làm mới trạng thái voice...")
            await vc.disconnect()
            await asyncio.sleep(2)
            await hub_channel.connect()

@tasks.loop(minutes=2)
async def voice_keepalive_task(bot):
    """Vòng lặp kiểm tra mỗi 2 phút để đảm bảo bot luôn trong voice"""
    if bot.is_ready():
        await join_voice_channel(bot)

async def check_voice_status(bot, member, before, after):
    """Xử lý khi bot bị kick hoặc rớt mạng"""
    if member.id == bot.user.id and after.channel is None:
        print("⚠️ Bot bị văng khỏi voice, sẽ quay lại sau 5s...")
        await asyncio.sleep(5)
        await join_voice_channel(bot)
