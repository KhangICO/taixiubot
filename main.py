import discord
from discord.ext import commands
import random, json, os, asyncio, datetime

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

# ================= DATA =================
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


# ================= QUIZ DATA =================
quiz_data = [
    {"q": "2 + 2 = ?", "a": "4"},
    {"q": "Thủ đô Việt Nam?", "a": "Hà Nội"},
    {"q": "5 x 6 = ?", "a": "30"},
]


# ================= CASINO =================
casino = {
    "active": False,
    "tai": {},
    "xiu": {},
    "message": None
}


# ================= QUIZ =================
class QuizView(discord.ui.View):
    def __init__(self, q, user_id):
        super().__init__(timeout=15)
        self.q = q
        self.user_id = user_id
        self.locked = False

    async def handle(self, interaction, choice):
        if self.locked:
            return await interaction.response.send_message("❌ Đã có kết quả!", ephemeral=True)

        self.locked = True

        for b in self.children:
            b.disabled = True

        user = get_user(interaction.user.id)

        if choice == self.q["a"]:
            reward = random.randint(100, 300)
            user["money"] += reward
            text = f"🎉 ĐÚNG +{reward}"
            color = 0x00ff00
        else:
            text = f"❌ SAI | Đáp án: {self.q['a']}"
            color = 0xff0000

        save(data)

        embed = discord.Embed(title="🧠 RESULT", description=text, color=color)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="A", style=discord.ButtonStyle.primary)
    async def a(self, i, b): await self.handle(i, self.q["a"])

    @discord.ui.button(label="B", style=discord.ButtonStyle.primary)
    async def b(self, i, b): await self.handle(i, self.q["a"])

    @discord.ui.button(label="C", style=discord.ButtonStyle.primary)
    async def c(self, i, b): await self.handle(i, self.q["a"])

    @discord.ui.button(label="D", style=discord.ButtonStyle.primary)
    async def d(self, i, b): await self.handle(i, self.q["a"])


@bot.command()
async def quiz(ctx):
    q = random.choice(quiz_data)

    embed = discord.Embed(
        title="🧠 QUIZ",
        description=q["q"],
        color=0x00ffcc
    )

    view = QuizView(q, ctx.author.id)
    msg = await ctx.send(embed=embed, view=view)

    for i in range(15, 0, -1):
        await asyncio.sleep(1)
        if view.locked:
            return
        embed.set_footer(text=f"⏱ {i}s")
        await msg.edit(embed=embed, view=view)

    if not view.locked:
        view.locked = True
        for b in view.children:
            b.disabled = True

        await msg.edit(
            embed=discord.Embed(
                title="⏰ HẾT GIỜ",
                description=f"Đáp án: {q['a']}",
                color=0xff0000
            ),
            view=view
        )


# ================= CASINO =================
class CasinoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎲 TÀI", style=discord.ButtonStyle.success)
    async def tai(self, i, b):
        await join_game(i, "tai")

    @discord.ui.button(label="🎲 XỈU", style=discord.ButtonStyle.danger)
    async def xiu(self, i, b):
        await join_game(i, "xiu")


async def join_game(interaction, choice):
    if not casino["active"]:
        return await interaction.response.send_message("❌ Không có phòng", ephemeral=True)

    uid = str(interaction.user.id)

    if uid in casino["tai"] or uid in casino["xiu"]:
        return await interaction.response.send_message("❌ Đã chọn rồi", ephemeral=True)

    bet = random.randint(50, 300)
    casino[choice][uid] = bet

    await update_ui(interaction.channel)

    await interaction.response.send_message(f"✅ Chọn {choice.upper()}", ephemeral=True)


async def update_ui(channel):
    tai = casino["tai"]
    xiu = casino["xiu"]

    embed = discord.Embed(title="🎰 CASINO LIVE", color=0x00ffcc)

    embed.add_field(
        name="TÀI",
        value="\n".join([f"<@{u}> {b}" for u, b in tai.items()]) or "None",
        inline=True
    )

    embed.add_field(
        name="XỈU",
        value="\n".join([f"<@{u}> {b}" for u, b in xiu.items()]) or "None",
        inline=True
    )

    if casino["message"]:
        await casino["message"].edit(embed=embed, view=CasinoView())


@bot.command()
async def casino(ctx):
    if casino["active"]:
        return await ctx.send("❌ Đang có phòng")

    casino["active"] = True
    casino["tai"] = {}
    casino["xiu"] = {}

    embed = discord.Embed(
        title="🎰 CASINO START",
        description="Chọn Tài hoặc Xỉu",
        color=0x00ffcc
    )

    msg = await ctx.send(embed=embed, view=CasinoView())
    casino["message"] = msg

    for i in range(15, 0, -1):
        await asyncio.sleep(1)
        embed.description = f"⏱ {i}s"
        await msg.edit(embed=embed)

    await end_casino(ctx)


async def end_casino(ctx):
    dice = [random.randint(1, 6) for _ in range(3)]
    total = sum(dice)
    result = "tai" if total >= 11 else "xiu"

    winners = casino[result]

    for uid, bet in winners.items():
        data[uid]["money"] += bet * 2

    save(data)

    casino["active"] = False
    casino["tai"] = {}
    casino["xiu"] = {}

    await ctx.send(
        f"🏁 {dice} = {total} → {result.upper()}"
    )


# ================= BASIC =================
@bot.command()
async def balance(ctx):
    user = get_user(ctx.author.id)
    await ctx.send(user["money"])


bot.run("MTQ5NjY1MDk0MDE2MDE1MTcwMw.GSogjC._gBjOLVKcOn3DpFvm4ncKVyl2DXywidUL2SXVE")
