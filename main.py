import discord
from discord.ext import commands
from discord import app_commands
import random, json, os, asyncio, datetime
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

DATA_FILE = "data.json"
casino = {
    "active": False,
    "tai": {},
    "xiu": {},
    "channel": None,
    "message": None
}
quiz_data = [
    {
        "question": "2 + 2 = ?",
        "options": ["1","2","3","4"],
        "answer": "4"
    },
    {
        "question": "Thủ đô Việt Nam?",
        "options": ["Hà Nội","HCM","Đà Nẵng","Huế"],
        "answer": "Hà Nội"
    },
    {
        "question": "5 x 6 = ?",
        "options": ["11","30","60","56"],
        "answer": "30"
    },
    {
        "question": "1 ngày có bao nhiêu giờ?",
        "options": ["12","24","48","36"],
        "answer": "24"
    },
    {
        "question": "Có bao nhiêu ngày trong tuần?",
        "options": ["5","6","7","8"],
        "answer": "7"
    },
    {
        "question": "Đâu là một loại bánh Huế?",
        "options": ["Khoái","Sàing","Thích","Vui"],
        "answer": "Khoái"
    },
    {
        "question": "Màu cờ nước Pháp?",
        "options": ["Đỏ - Trắng - Xanh","Đỏ - Vàng - Xanh","Trắng - Đen - Xanh","Đỏ - Trắng - Vàng"],
        "answer": "Đỏ - Trắng - Xanh"
    },
    {
        "question": "Đâu là một loại trái cây?",
        "options": ["Táo","Bàn","Ghế","Sách"],
        "answer": "Táo"
    },
    {
        "question": "\"Vĩnh Viễn\" là danh từ hay tính từ?",
        "options": ["Danh từ", "Tính từ", "Động từ", "Trạng từ"],
        "answer": "Tính từ"
    },
    {
        "question": "Chữ cái thứ tư trong bảng chữ cái tiếng Việt là chữ gì?",
        "options": ["A", "C", "D", "B"],
        "answer": "B"
    },
    {
        "question": "Sắp xếp các chữ sau thành từ đúng: r / ò / i / g / V / ồ / n",
        "options": ["Vòi rồng", "Vòng tròn", "Rồng vòi", "Vòi nước"],
        "answer": "Vòi rồng"
    },
]
def load():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}
def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
data = load()

def get_user(uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {"money": 1000, "daily": ""}
    return data[uid]

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot online: {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(
            f"⏳ Bạn đang cooldown! Thử lại sau **{round(error.retry_after, 1)} giây**"
        )
# ================= BALANCE =================
@bot.command()
async def balance(ctx):
    user = get_user(ctx.author.id)
    await ctx.send(f"💰 {user['money']} coins")

# ================= DAILY =================
@bot.command()
async def daily(ctx):
    user = get_user(ctx.author.id)
    today = str(datetime.date.today())

    if user["daily"] == today:
        await ctx.send("❌ Hôm nay nhận rồi!")
        return

    reward = random.randint(100, 300)
    user["money"] += reward
    user["daily"] = today
    save(data)

    await ctx.send(f"🎁 Bạn nhận {reward} coins!")

# ================= TOP =================
@bot.command()
async def top(ctx):
    top_users = sorted(data.items(), key=lambda x: x[1]["money"], reverse=True)[:5]

    msg = ""
    for i, (uid, info) in enumerate(top_users, 1):
        msg += f"{i}. <@{uid}> - {info['money']} coins\n"

    await ctx.send(f"🏆 TOP GIÀU NHẤT\n{msg}")


# ================= QUIZ =================
@bot.command()
@commands.cooldown(1, 10, commands.BucketType.user)
async def quiz(ctx):
    user = get_user(ctx.author.id)
    q = random.choice(quiz_data)

    time_left = 15

    embed = discord.Embed(
        title="🧠 QUIZ GAME",
        description=f"{q['question']}\n\n"
                    f"A. {q['options'][0]}\n"
                    f"B. {q['options'][1]}\n"
                    f"C. {q['options'][2]}\n"
                    f"D. {q['options'][3]}",
        color=0x00ffcc
    )
    embed.set_footer(text=f"⏱ Còn {time_left} giây")

    class QuizView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=15)
            self.locked = False

        async def check(self, interaction, choice):
            if self.locked:
                return await interaction.response.send_message("❌ Đã có người trả lời", ephemeral=True)

            self.locked = True

            for b in self.children:
                b.disabled = True

            if choice == q["answer"]:
                reward = random.randint(100, 300)
                user["money"] += reward
                text = f"🎉 ĐÚNG +{reward}"
                color = 0x00ff00
            else:
                text = f"❌ SAI | Đáp án: {q['answer']}"
                color = 0xff0000

            save(data)

            new_embed = discord.Embed(title="🧠 KẾT QUẢ", description=text, color=color)
            await interaction.response.edit_message(embed=new_embed, view=self)

        @discord.ui.button(label="A", style=discord.ButtonStyle.primary)
        async def a(self, i, b): await self.check(i, q["options"][0])

        @discord.ui.button(label="B", style=discord.ButtonStyle.primary)
        async def b(self, i, b): await self.check(i, q["options"][1])

        @discord.ui.button(label="C", style=discord.ButtonStyle.primary)
        async def c(self, i, b): await self.check(i, q["options"][2])

        @discord.ui.button(label="D", style=discord.ButtonStyle.primary)
        async def d(self, i, b): await self.check(i, q["options"][3])

    view = QuizView()
    msg = await ctx.send(embed=embed, view=view)

    # ⏱ COUNTDOWN LOOP
    for i in range(15, 0, -1):
        await asyncio.sleep(1)

        if view.locked:
            return

        new_embed = discord.Embed(
            title="🧠 QUIZ GAME",
            description=f"{q['question']}\n\n"
                        f"A. {q['options'][0]}\n"
                        f"B. {q['options'][1]}\n"
                        f"C. {q['options'][2]}\n"
                        f"D. {q['options'][3]}",
            color=0x00ffcc
        )
        new_embed.set_footer(text=f"⏱ Còn {i} giây")

        await msg.edit(embed=new_embed, view=view)

    # ⏰ HẾT GIỜ
    if not view.locked:
        view.locked = True
        for b in view.children:
            b.disabled = True

        end_embed = discord.Embed(
            title="⏰ HẾT GIỜ",
            description=f"❌ Đáp án đúng là: **{q['answer']}**",
            color=0xff0000
        )

        await msg.edit(embed=end_embed, view=view)

# ================= TAIXIU button =================
class CasinoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎲 TÀI", style=discord.ButtonStyle.success)
    async def tai(self, interaction: discord.Interaction, button: discord.ui.Button):
        await join_game(interaction, "tai")

    @discord.ui.button(label="🎲 XỈU", style=discord.ButtonStyle.danger)
    async def xiu(self, interaction: discord.Interaction, button: discord.ui.Button):
        await join_game(interaction, "xiu")
# ================= TAIXIU GAME=================
async def join_game(interaction, choice):
    if not casino["active"]:
        return await interaction.response.send_message("❌ Không có phòng", ephemeral=True)

    uid = str(interaction.user.id)

    if uid in casino["tai"] or uid in casino["xiu"]:
        return await interaction.response.send_message("❌ Bạn đã chọn rồi", ephemeral=True)

    bet = random.randint(50, 300)
    casino[choice][uid] = bet

    await update_ui(interaction.channel)

    await interaction.response.send_message(
        f"✅ Bạn chọn {choice.upper()}",
        ephemeral=True
    )


async def update_ui(channel):
    tai_list = casino["tai"]
    xiu_list = casino["xiu"]

    tai_text = "\n".join([f"<@{uid}>: {bet}" for uid, bet in tai_list.items()]) or "Không có ai"
    xiu_text = "\n".join([f"<@{uid}>: {bet}" for uid, bet in xiu_list.items()]) or "Không có ai"

    embed = discord.Embed(
        title="🎰 CASINO LIVE",
        description="🟢 Đang mở cược...\n⏱ Chọn TÀI hoặc XỈU",
        color=0x00ffcc
    )

    embed.add_field(name="🎲 TÀI", value=tai_text, inline=True)
    embed.add_field(name="🎲 XỈU", value=xiu_text, inline=True)

    total_tai = sum(tai_list.values()) if tai_list else 0
    total_xiu = sum(xiu_list.values()) if xiu_list else 0

    embed.add_field(name="💰 Tổng TÀI", value=str(total_tai), inline=True)
    embed.add_field(name="💰 Tổng XỈU", value=str(total_xiu), inline=True)

    if casino["message"]:
        await casino["message"].edit(embed=embed, view=CasinoView())

# ================= OPEN CASINO =================  
@bot.command()
async def opensong(ctx):
    if casino["active"]:
        return await ctx.send("❌ Đã có phòng rồi!")

    casino["active"] = True
    casino["tai"] = {}
    casino["xiu"] = {}
    casino["message"] = None

    embed = discord.Embed(
        title="🎰 CASINO PRO",
        description="Bấm nút để cược!\n⏱ 15 giây",
        color=0x00ffcc
    )

    msg = await ctx.send(embed=embed, view=CasinoView())
    casino["message"] = msg

    for i in range(15, 0, -1):
        await asyncio.sleep(1)
        embed.description = f"⏱ Còn {i}s"
        await msg.edit(embed=embed)

    await end_casino(ctx)    

# ================= END CASINO =================
async def end_casino(ctx):
    dice = [random.randint(1,6) for _ in range(3)]
    total = sum(dice)
    result = "tai" if total >= 11 else "xiu"

    winners = casino[result]
    losers = casino["xiu" if result == "tai" else "tai"]

    win_text = ""
    lose_text = ""

    # 💰 xử lý thắng
    for uid, bet in winners.items():
        data[uid]["money"] += bet * 2
        win_text += f"🎉 <@{uid}> +{bet*2} coins\n"

    # 💀 xử lý thua
    for uid, bet in losers.items():
        data[uid]["money"] -= bet
        lose_text += f"💀 <@{uid}> -{bet} coins\n"

    save(data)

    embed = discord.Embed(
        title="🏁 KẾT QUẢ CASINO",
        description=f"🎲 Xúc xắc: {dice} = {total}\n🏆 Kết quả: **{result.upper()}**",
        color=0xffcc00
    )

    embed.add_field(
        name="🎉 Người THẮNG",
        value=win_text or "Không có ai thắng",
        inline=False
    )

    embed.add_field(
        name="💀 Người THUA",
        value=lose_text or "Không có ai thua",
        inline=False
    )

    casino["active"] = False
    casino["tai"] = {}
    casino["xiu"] = {}

    await ctx.send(embed=embed)
# ================= SLASH HELP =================
@bot.tree.command(name="help", description="Xem hướng dẫn")
async def help_slash(interaction: discord.Interaction):
    embed = discord.Embed(title="🎮 MENU BOT", color=0x00ffcc)

    embed.add_field(name="!balance", value="Xem tiền", inline=False)
    embed.add_field(name="!daily", value="Nhận tiền", inline=False)
    embed.add_field(name="!top", value="Top server", inline=False)
    embed.add_field(name="!quiz", value="Chơi quiz", inline=False)
    embed.add_field(name="!opensong", value="Chơi tài xỉu", inline=False)
    await interaction.response.send_message(embed=embed)

# 🔐 TOKEN
bot.run("MTQ5NjY1MDk0MDE2MDE1MTcwMw.GSogjC._gBjOLVKcOn3DpFvm4ncKVyl2DXywidUL2SXVE")
