import discord
import asyncio

HUB_CHANNEL_ID = 1490301863692865597 

async def join_voice_channel(bot):
    hub_channel = bot.get_channel(HUB_CHANNEL_ID)
    if not hub_channel:
        return

    # Lấy đối tượng voice_client của bot trong server này
    vc = discord.utils.get(bot.voice_clients, guild=hub_channel.guild)
    
    # CHỈ CONNECT NẾU: Bot hoàn toàn chưa vào voice (vc is None) 
    # HOẶC Bot đã vào nhưng bị rớt kết nối (is_connected == False)
    if vc is None or not vc.is_connected():
        try:
            print(f"📡 Đang kết nối vào Hub...")
            await hub_channel.connect()
        except Exception as e:
            print(f"❌ Lỗi connect: {e}")
    else:
        # Nếu Bot đã ở trong Voice, kiểm tra xem nó có đang ở một mình không
        # (Phòng JTC thường tự xóa nếu chỉ có 1 mình bot sau một khoảng thời gian)
        if len(vc.channel.members) == 1 and vc.channel.id != HUB_CHANNEL_ID:
            print("🔄 Phòng trống, quay lại Hub để làm mới...")
            await vc.disconnect()
            await asyncio.sleep(2)
            await hub_channel.connect()
        else:
            print(f"✅ Bot vẫn đang ổn định tại kênh: {vc.channel.name}")

async def check_voice_status(bot, member, before, after):
    # Chỉ kích hoạt lại khi chính BOT bị thoát hoàn toàn (after.channel là None)
    if member.id == bot.user.id and after.channel is None:
        print("⚠️ Bot rớt kết nối hoàn toàn, chuẩn bị vào lại...")
        await asyncio.sleep(3)
        await join_voice_channel(bot)
