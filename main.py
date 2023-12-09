import discord
from discord.ext import commands
import datetime
import os
from dotenv import load_dotenv
import discord.utils
import pytz
import asyncio 

bot = commands.Bot(command_prefix="a.", intents=discord.Intents.all())

rooms = {}

load_dotenv()
TOKEN = os.getenv('TOKEN')

def read_rooms():
    global rooms
    try:
        with open("rooms.txt", "r", encoding='utf-8') as f:
            for line in f:
                room_id, owner_id, created_at, name = line.strip().split(",")
                created_at = datetime.datetime.fromisoformat(created_at).astimezone(pytz.timezone('UTC'))
                rooms[int(room_id)] = {"owner": int(owner_id), "created_at": created_at, "name": name}
    except FileNotFoundError:
        with open("rooms.txt", "w") as f:
            pass

def write_rooms():
    global rooms
    with open("rooms.txt", "w", encoding='utf-8') as f:
        for room_id, room_info in rooms.items():
            f.write(f"{room_id},{room_info['owner']},{room_info['created_at'].astimezone(pytz.timezone('Asia/Ho_Chi_Minh')).isoformat()},{room_info['name']}\n")

def is_owner(ctx):
    global rooms
    voice_channel = ctx.author.voice.channel
    if voice_channel.id in rooms:
        if ctx.author.id == rooms[voice_channel.id]["owner"]:
            return True
        else:
            return False
    else:
        return False

def is_in_room(ctx):
    global rooms
    voice_channel = ctx.author.voice.channel
    if voice_channel.id in rooms:
        return True
    else:
        return False

async def create_room(member, master_channel):
    global rooms
    guild = bot.get_guild(1122956235902300260)
    max_bitrate = guild.bitrate_limit
    new_channel = await guild.create_voice_channel(f"Phòng của {member.name}", category=master_channel.category, position=master_channel.position + 1, bitrate=max_bitrate)
    await member.move_to(new_channel)
    await new_channel.set_permissions(member, view_channel=True, connect=True)
    created_at = datetime.datetime.now(pytz.timezone('Asia/Ho_Chi_Minh'))
    rooms[new_channel.id] = {"owner": member.id, "created_at": created_at, "name": new_channel.name}
    await new_channel.send(f"Xin chào **{member.mention}**!")
    embed = discord.Embed(title="Danh sách lệnh để tùy chỉnh phòng:"
                          , description=f"`{bot.command_prefix}name + tên phòng` : đổi tên phòng\n"
                            f"`{bot.command_prefix}kick + @user` : ngắt kết nối một người nào đó khỏi phòng\n"
                            f"`{bot.command_prefix}transfer + @user` : chuyển chủ phòng cho người dùng nào đó \n"
                            f"`{bot.command_prefix}limit + 0-99` : đặt giới hạn số người tham gia phòng\n"
                            f"`{bot.command_prefix}info`: xem thông tin chủ phòng và thời gian tạo\n"
                            f"`{bot.command_prefix}lock`: khóa phòng\n"
                            f"`{bot.command_prefix}invisible` : ẩn phòng\n"
                            f"`{bot.command_prefix}visible`: hiển thi phòng\n"
                            f"`{bot.command_prefix}unlock`: mở khóa phòng\n"
                            f"`{bot.command_prefix}allow + @user1 @user2 @user_n...` : cho phép người dùng nào đó thấy và tham gia kênh thoại\n"
                            f"`{bot.command_prefix}disallow + @user1 @user2 @user_n...` : không cho phép người dùng nào đó thấy và tham gia kênh thoại\n"
                            f"`{bot.command_prefix}claim`: lấy phòng khi chủ phòng không ở đấy\n"
                            f"`{bot.command_prefix}bitrate + giá trị (8-384)` : chỉnh bitrate của phòng\n"
                            f"Để hiển thị lại cách sử dụng bot, bạn hãy sử dụng lệnh `{bot.command_prefix}helpp` để hiển thị lại cách sử dụng bot"
                            , color=0xfd5296)
    await new_channel.send(embed=embed)
    rooms[new_channel.id] = {"owner": member.id, "created_at": datetime.datetime.now(), "name": new_channel.name}
    write_rooms()


async def delete_room(channel):
    global rooms
    if channel.id in rooms:
        await channel.delete()
        del rooms[channel.id]
        write_rooms()

@bot.event
async def on_ready():
    read_rooms()
    print(f"Bot is ready as {bot.user}")

@bot.event
async def on_voice_state_update(member, before, after):
    master_channel_id = 1182333430894174258
    if after.channel and after.channel.id == master_channel_id:
        await create_room(member, after.channel)
    if before.channel and before.channel.id in rooms:
      bot_count = 0
      for user in before.channel.members:
          if user.bot:
              bot_count += 1
      if len(before.channel.members) == bot_count:
          await delete_room(before.channel)

@bot.command(name="name", descryption="Đổi tên phòng")
@commands.check(is_in_room)
async def name(ctx, *, new_name):
    voice_channel = ctx.author.voice.channel
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    if ctx.author == owner:
      await ctx.send("Đang đổi tên phòng, vui lòng chờ...")
      await voice_channel.edit(name=new_name)
      rooms[voice_channel.id]["name"] = new_name
      write_rooms()
      await ctx.send(f"Kênh thoại đã được đổi tên thành **{new_name}**.")
    else:
      await ctx.send("Bạn cần phải là chủ phòng để sử dụng lệnh này.")

@bot.command(name="kick", descryption="Ngắt kết nối người dùng nào đó khỏi kênh thoại")
@commands.check(is_in_room)
async def kick(ctx, user: discord.Member):
    voice_channel = ctx.author.voice.channel
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    if ctx.author == owner:
      if user.voice and user.voice.channel == voice_channel:
          await user.move_to(None)
          await ctx.send(f"**{user.name}** đã bị ngắt kết nối khỏi phòng.")
      else:
          await ctx.send(f"**{user.name}** không ở trong phòng.")
    else:
      await ctx.send("Bạn cần phải là chủ phòng để sử dụng lệnh này.")

@bot.command(name="transfer", descryption="Chuyển quyền sở hữu phòng cho người dùng nào đó")
@commands.check(is_in_room)
async def transfer(ctx, user: discord.Member):
    voice_channel = ctx.author.voice.channel
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    if ctx.author == owner:
      if user.voice and user.voice.channel == voice_channel:
          rooms[voice_channel.id]["owner"] = user.id
          write_rooms()
          await ctx.send(f"Bạn đã chuyển quyền sở hữu của phòng cho **{user.name}**.")
          await voice_channel.set_permissions(user, view_channel=True, connect=True)
      else:
          await ctx.send(f"**{user.name}** không ở trong phòng.")
    else:
      await ctx.send("Bạn cần phải là chủ phòng để sử dụng lệnh này.")

@bot.command(name="limit", descryption="Đặt giới hạn số người tham gia của phòng")
@commands.check(is_in_room)
async def limit(ctx, limit: int):
    voice_channel = ctx.author.voice.channel
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    if ctx.author == owner:
      if 0 <= limit <= 99:
          await voice_channel.edit(user_limit=limit)
          await ctx.send(f"Bạn đã đặt giới hạn số người tham gia phòng là **{limit}**.")
      else:
          await ctx.send(f"Giới hạn số người tham gia phòng phải nằm trong khoảng từ 0 đến 99.")
    else:
      await ctx.send("Bạn cần phải là chủ phòng để sử dụng lệnh này.")

@bot.command(name="info", descryption="Xem thông tin phòng")
@commands.check(is_in_room)
async def info(ctx):
    voice_channel = ctx.author.voice.channel
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    created_at = room_info["created_at"]
    timezone = pytz.timezone('Asia/Ho_Chi_Minh')
    now_utc7 = datetime.datetime.now(timezone)
    created_at_utc7 = created_at.astimezone(timezone)
    days_since_created = (now_utc7 - created_at_utc7).days
    embed = discord.Embed(title="Thông tin phòng:"
                          , description=f"Tên phòng: **{voice_channel.name}**\n"
                            f"Chủ phòng: **{owner.name}**\n"
                            f"Thời gian tạo: {created_at.astimezone(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%d/%m/%Y %H:%M:%S')} **(UTC+7)**\n"
                            f"Tạo cách đây: **{days_since_created} ngày**\n"
                            f"Số người tham gia: **{len(voice_channel.members)}/{voice_channel.user_limit or 'không giới hạn'}**\n"
                            f"Bitrate: **{voice_channel.bitrate / 1000} kbps**"
                            , color=0xfd5296)
    await ctx.send(embed=embed)

@bot.command(name="lock", descryption="Khóa phòng")
@commands.check(is_in_room)
async def lock(ctx):
    voice_channel = ctx.author.voice.channel
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    guild = ctx.guild
    default_role = guild.default_role
    if ctx.author == owner:
      await voice_channel.set_permissions(default_role, connect=False)
      await ctx.send(f"Bạn đã khóa phòng. Chỉ những người được cho phép mới có thể thấy và tham gia kênh thoại.")
    else:
      await ctx.send("Bạn cần phải là chủ phòng để sử dụng lệnh này.")

@bot.command(name="invisible", descryption="Ẩn phòng")
@commands.check(is_in_room)
async def invisible(ctx):
    voice_channel = ctx.author.voice.channel
    guild = ctx.guild
    default_role = guild.default_role
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    if ctx.author == owner:
      await voice_channel.set_permissions(default_role, view_channel=False)
      await ctx.send(f"Bạn đã ẩn phòng. Chỉ những người được cho phép mới có thể thấy và tham gia kênh thoại.")
    else:
      await ctx.send("Bạn cần phải là chủ phòng để sử dụng lệnh này.")

@bot.command(name="visible", descryption="Hiển thị")
@commands.check(is_in_room)
async def visible(ctx):
    voice_channel = ctx.author.voice.channel
    room_info = rooms[voice_channel.id]
    guild = ctx.guild
    default_role = guild.default_role
    owner = ctx.guild.get_member(room_info["owner"])
    if ctx.author == owner:
      await voice_channel.set_permissions(default_role, view_channel=True)
      await ctx.send(f"Bạn đã hiển thị phòng. Tất cả mọi người trong máy chủ có thể thấy và tham gia kênh thoại.")
    else:
      await ctx.send("Bạn cần phải là chủ phòng để sử dụng lệnh này.")

@bot.command(name="unlock", descryption="Mở khóa phòng")
@commands.check(is_in_room)
async def unlock(ctx):
    voice_channel = ctx.author.voice.channel
    guild = ctx.guild
    default_role = guild.default_role
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    if ctx.author == owner:
      await voice_channel.set_permissions(default_role, connect=True)
      await ctx.send(f"Bạn đã mở khóa phòng. Tất cả mọi người trong máy chủ có thể tham gia kênh thoại.")
    else:
      await ctx.send("Bạn cần phải là chủ phòng để sử dụng lệnh này.")

@bot.command(name="allow", descryption="Cho phép người dùng nào đó")
@commands.check(is_in_room)
async def allow(ctx, *users: discord.Member):
    voice_channel = ctx.author.voice.channel
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    if ctx.author == owner:
      for user in users:
          await voice_channel.set_permissions(user, view_channel=True, connect=True)
      await ctx.send(f"Bạn đã cho phép **{', '.join(user.name for user in users)}** tham gia kênh thoại.")
    else:
      await ctx.send("Bạn cần phải là chủ phòng để sử dụng lệnh này.")

@bot.command(name="disallow", descryption="Không cho phép người dùng nào đó")
@commands.check(is_in_room)
async def disallow(ctx, *users: discord.Member):
    voice_channel = ctx.author.voice.channel
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    if ctx.author == owner:
      for user in users:
          await voice_channel.set_permissions(user, connect=False)
      await ctx.send(f"Bạn đã không cho phép **{', '.join(user.name for user in users)}** tham gia kênh thoại.")
    else:
      await ctx.send("Bạn cần phải là chủ phòng để sử dụng lệnh này.")

@bot.command(name="claim", descryption="Nhận chủ phòng")
@commands.check(is_in_room)
async def claim(ctx):
    voice_channel = ctx.author.voice.channel
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    if owner.voice is None or owner.voice.channel != voice_channel:
        rooms[voice_channel.id]["owner"] = ctx.author.id
        write_rooms()
        owner = ctx.guild.get_member(room_info["owner"])
        await ctx.send(f"Hiện **{owner.name}** đã là chủ phòng mới!")
        await voice_channel.set_permissions(ctx, view_channel=True, connect=True)
    else:
        await ctx.send(f"Chủ phòng vẫn ở trong phòng mà.")

@bot.command(name="bitrate", descryption="Chỉnh bitrate của phòng")
@commands.check(is_in_room)
async def bitrate(ctx, bitrate: int):
    voice_channel = ctx.author.voice.channel
    room_info = rooms[voice_channel.id]
    owner = ctx.guild.get_member(room_info["owner"])
    if ctx.author == owner:
      if 8 <= bitrate <= 384:
          await voice_channel.edit(bitrate=bitrate * 1000)
          await ctx.send(f"Bạn đã chỉnh bitrate của phòng là {bitrate} kbps.")
      else:
          await ctx.send(f"Bitrate của phòng phải nằm trong khoảng từ 8 đến 384 kbps.")
    else:
      await ctx.send("Bạn cần phải là chủ phòng để sử dụng lệnh này.")

@bot.command(name="helpp", descryption="Hiện cách sử dụng bot")
@commands.check(is_in_room)
async def helpp(ctx):
    embed = discord.Embed(title="Danh sách lệnh để tùy chỉnh phòng:"
                          , description=f"`{bot.command_prefix}name + tên phòng` : đổi tên phòng\n"
                            f"`{bot.command_prefix}kick + @user` : ngắt kết nối một người nào đó khỏi phòng\n"
                            f"`{bot.command_prefix}transfer + @user` : chuyển chủ phòng cho người dùng nào đó \n"
                            f"`{bot.command_prefix}limit + 0-99` : đặt giới hạn số người tham gia phòng\n"
                            f"`{bot.command_prefix}info`: xem thông tin chủ phòng và thời gian tạo\n"
                            f"`{bot.command_prefix}lock`: khóa phòng\n"
                            f"`{bot.command_prefix}invisible` : ẩn phòng\n"
                            f"`{bot.command_prefix}visible`: hiển thi phòng\n"
                            f"`{bot.command_prefix}unlock`: mở khóa phòng\n"
                            f"`{bot.command_prefix}allow + @user1 @user2 @user_n...` : cho phép người dùng nào đó thấy và tham gia kênh thoại\n"
                            f"`{bot.command_prefix}disallow + @user1 @user2 @user_n...` : không cho phép người dùng nào đó thấy và tham gia kênh thoại\n"
                            f"`{bot.command_prefix}claim`: lấy phòng khi chủ phòng không ở đấy\n"
                            f"`{bot.command_prefix}bitrate + giá trị (8-384)` : chỉnh bitrate của phòng\n"
                            f"Để hiển thị lại cách sử dụng bot, bạn hãy sử dụng lệnh `{bot.command_prefix}helpp` để hiển thị lại cách sử dụng bot"
                            , color=0xfd5296)
    await ctx.send(embed=embed)

# Run the bot with the bot token
bot.run(TOKEN)
