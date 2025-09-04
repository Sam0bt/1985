import discord
from discord.ext import commands
import aiohttp
import hashlib
import ssl
import time
import asyncio

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# -------- CONFIG --------
GUILD_ID = 1411780696015372350         # Sunucu ID
VERIFY_CHANNEL_ID = 1411783544564486146 # #verify kanal ID
WELCOME_CHANNEL_ID = 1412523847273549865
SECRET = "tB87#kPtkxqOS2"
WOS_API_URL = "https://wos-giftcode-api.centurygame.com/api/player"

# Sabit butonlu verify view
class VerifyModal(discord.ui.Modal, title="Oyuncu Doğrulama"):
    player_id = discord.ui.TextInput(
        label="Enter ID",
        placeholder="Please enter your WOS game ID",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        fid = str(self.player_id.value).strip()
        await interaction.response.defer(thinking=True)

        current_time = int(time.time() * 1000)
        form = f"fid={fid}&time={current_time}"
        sign = hashlib.md5((form + SECRET).encode('utf-8')).hexdigest()
        form = f"sign={sign}&{form}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(WOS_API_URL, headers=headers, data=form, ssl=ssl_context) as resp:
                    data = await resp.json()
                    if "data" not in data:
                        await interaction.followup.send("❌ ID is incorrect. Player not found.", ephemeral=True)
                        return

                    player_data = data["data"]
                    nickname = player_data.get("nickname", "none")
                    fid_value = player_data.get("fid", fid)
                    stove_level = player_data.get("stove_lv", 0)
                    avatar_image = player_data.get("avatar_image", None)
                    kid = data['data']['kid']

                    # Rolleri güncelle
                    guild = bot.get_guild(GUILD_ID)
                    member = guild.get_member(interaction.user.id)
                    verified_role = discord.utils.get(guild.roles, name="verified")
                    unverified_role = discord.utils.get(guild.roles, name="unverified")

                    if verified_role:
                        await member.add_roles(verified_role)
                    if unverified_role:
                        await member.remove_roles(unverified_role)

                    # Welcome embed
                    embed = discord.Embed(
                        title=f"🎉 Welcome {nickname} 🎉",
                        description=(
                            f"👤 **UserName:** {nickname}\n"
                            f"🏰 **Level (Stove):** {stove_level}\n"
                            f"🆔 **ID:** {fid_value}\n"
                            f"🌍 **State:** `{kid}`\n"
                        ),
                        color=discord.Color.green()
                    )
                    if avatar_image:
                        embed.set_image(url=avatar_image)
                    embed.set_footer(text="Whiteout Survival •State 1985")

                    welcome_channel = bot.get_channel(WELCOME_CHANNEL_ID)
                    await welcome_channel.send(embed=embed)
                    await interaction.followup.send("✅ Identity Verified!", ephemeral=True)

        except Exception as e:
            print(f"Hata: {e}")
            await interaction.followup.send("❌ Error", ephemeral=True)

# Butonlu view
class VerifyButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verification!", style=discord.ButtonStyle.green)
    async def start_verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = VerifyModal()
        await interaction.response.send_modal(modal)

# Bot açıldığında sabit verify mesajı gönder
@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")
    await bot.tree.sync()

    guild = bot.get_guild(GUILD_ID)
    verify_channel = bot.get_channel(VERIFY_CHANNEL_ID)
    if verify_channel:
        # Önce eski bot mesajlarını sil
        async for msg in verify_channel.history(limit=100):
            if msg.author == bot.user and "Verification!" in msg.content:
                await msg.delete()

        await verify_channel.send(
            "👋 Welcome! Click the button below to verify your Player ID:",
            view=VerifyButton()
        )

bot.run("")