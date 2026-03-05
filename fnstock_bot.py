import discord
from discord.ext import commands
import os

TOKEN        = os.environ.get("TOKEN")
PAGAMENTO_CH = int(os.environ.get("PAGAMENTO_CH", "0"))
STAFF_ROLE   = int(os.environ.get("STAFF_ROLE", "0"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

account_counter = 1


def is_staff(member: discord.Member) -> bool:
    if STAFF_ROLE == 0:
        return member.guild_permissions.administrator
    return any(r.id == STAFF_ROLE for r in member.roles) or member.guild_permissions.administrator


class AcquistaView(discord.ui.View):
    def __init__(self, acc_id: int):
        super().__init__(timeout=None)
        self.acc_id = acc_id

    @discord.ui.button(label="🛒  BUY NOW", style=discord.ButtonStyle.primary)
    async def acquista(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = interaction.guild.get_channel(PAGAMENTO_CH)
        if ch:
            msg = (
                f"💳 To purchase **Account #{self.acc_id:03d}**, "
                f"go to {ch.mention} and follow the instructions!\n"
                f"Then open a ticket in **#support** with the ID **#{self.acc_id:03d}**."
            )
        else:
            msg = (
                f"💳 To purchase **Account #{self.acc_id:03d}**, "
                f"go to **#payment-methods** and open a ticket!"
            )
        await interaction.response.send_message(msg, ephemeral=True)


class AccountNormaleModal(discord.ui.Modal, title="Add Normal Account"):
    prezzo   = discord.ui.TextInput(label="Price in euros (e.g. 35.00)",              placeholder="35.00",                             required=True,  max_length=10)
    livello  = discord.ui.TextInput(label="Account level (e.g. 150)",                 placeholder="150",                               required=True,  max_length=10)
    num_skin = discord.ui.TextInput(label="Skins & V-Bucks (e.g. 24 skins, 1500 vb)",placeholder="24 skins, 1500 vbucks",             required=True,  max_length=60)
    skins    = discord.ui.TextInput(label="Included skins (comma separated)",         placeholder="Skull Trooper, Black Knight...",    required=True,  max_length=500, style=discord.TextStyle.paragraph)
    foto     = discord.ui.TextInput(label="Photo link (https://i.imgur.com/...)",     placeholder="https://i.imgur.com/abc1234.png",   required=False, max_length=300)

    async def on_submit(self, interaction: discord.Interaction):
        await pubblica(interaction, self.prezzo.value, self.livello.value,
                       self.num_skin.value, self.skins.value, "", self.foto.value, False)


class AccountFeaturedModal(discord.ui.Modal, title="Add Featured Account"):
    prezzo   = discord.ui.TextInput(label="Price in euros (e.g. 95.00)",              placeholder="95.00",                                        required=True,  max_length=10)
    livello  = discord.ui.TextInput(label="Account level (e.g. 412)",                 placeholder="412",                                          required=True,  max_length=10)
    num_skin = discord.ui.TextInput(label="Skins & V-Bucks (e.g. 34 skins, 2800 vb)",placeholder="34 skins, 2800 vbucks",                        required=True,  max_length=60)
    skins    = discord.ui.TextInput(label="Included skins (comma separated)",         placeholder="Skull Trooper, Ghoul Trooper...",              required=True,  max_length=500, style=discord.TextStyle.paragraph)
    foto     = discord.ui.TextInput(label="Photo link (https://i.imgur.com/...)",     placeholder="https://i.imgur.com/abc1234.png",              required=False, max_length=300)

    async def on_submit(self, interaction: discord.Interaction):
        await pubblica(interaction, self.prezzo.value, self.livello.value,
                       self.num_skin.value, self.skins.value, "", self.foto.value, True)


class AccountFeaturedPackModal(discord.ui.Modal, title="Add Featured + Pack"):
    prezzo   = discord.ui.TextInput(label="Price in euros (e.g. 95.00)",              placeholder="95.00",                                        required=True,  max_length=10)
    livello  = discord.ui.TextInput(label="Account level (e.g. 412)",                 placeholder="412",                                          required=True,  max_length=10)
    num_skin = discord.ui.TextInput(label="Skins & V-Bucks (e.g. 34 skins, 2800 vb)",placeholder="34 skins, 2800 vbucks",                        required=True,  max_length=60)
    skins    = discord.ui.TextInput(label="Included skins (comma separated)",         placeholder="Skull Trooper, Ghoul Trooper...",              required=True,  max_length=500, style=discord.TextStyle.paragraph)
    pack     = discord.ui.TextInput(label="Included packs (comma separated)",         placeholder="Darkfire Bundle, Frozen Legends Pack...",      required=True,  max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        await pubblica(interaction, self.prezzo.value, self.livello.value,
                       self.num_skin.value, self.skins.value, self.pack.value, "", True)


async def pubblica(interaction, prezzo, livello, num_skin_vb, skins, pack, foto, featured):
    global account_counter
    acc_id = account_counter
    account_counter += 1

    embed = discord.Embed(
        title=("⭐ FEATURED ACCOUNT" if featured else "🎮 ACCOUNT AVAILABLE") + f" — ID #{acc_id:03d}",
        color=0xf5c842 if featured else 0x8b3cf7,
    )

    foto = foto.strip()
    if foto and foto.startswith("http"):
        embed.set_image(url=foto)

    embed.add_field(name="💰 Price",          value=f"**€{prezzo.strip()}**",  inline=True)
    embed.add_field(name="🏆 Level",           value=f"Lv. {livello.strip()}", inline=True)
    embed.add_field(name="🎨 Skins & V-Bucks", value=num_skin_vb.strip(),      inline=True)
    embed.add_field(name="👗 Included Skins",  value=skins.strip(),            inline=False)

    if pack and pack.strip():
        embed.add_field(name="📦 Included Packs", value=pack.strip(), inline=False)

    if featured and interaction.guild and interaction.guild.icon:
        embed.set_author(name="⭐ FEATURED ACCOUNT — FNStock", icon_url=interaction.guild.icon.url)

    embed.set_footer(text="✅ Verified by FNStock Staff · 🔒 Email change included")

    announce = "🔥 **New FEATURED account available!**" if featured else "🆕 **New account available!**"
    await interaction.response.send_message(content=announce, embed=embed, view=AcquistaView(acc_id))


class TipoAccountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="⭐ Featured (no pack)", style=discord.ButtonStyle.success)
    async def featured(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AccountFeaturedModal())

    @discord.ui.button(label="⭐ Featured + Pack", style=discord.ButtonStyle.success)
    async def featured_pack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AccountFeaturedPackModal())

    @discord.ui.button(label="🎮 Normal", style=discord.ButtonStyle.primary)
    async def normale(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AccountNormaleModal())


@bot.event
async def on_ready():
    print(f"✅ FNStock Bot online — {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} commands synced")
    except Exception as e:
        print(f"❌ Sync error: {e}")


@bot.tree.command(name="aggiungi", description="[STAFF] Add a new Fortnite account")
async def aggiungi(interaction: discord.Interaction):
    if not is_staff(interaction.user):
        await interaction.response.send_message("❌ You don't have permission.", ephemeral=True)
        return
    embed = discord.Embed(title="📋 Account type", description="Choose the account type:", color=0x8b3cf7)
    await interaction.response.send_message(embed=embed, view=TipoAccountView(), ephemeral=True)


@bot.tree.command(name="reset_counter", description="[ADMIN] Reset account ID counter")
async def reset_counter(interaction: discord.Interaction):
    global account_counter
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Admins only.", ephemeral=True)
        return
    account_counter = 1
    await interaction.response.send_message("🔄 Counter reset to #001.", ephemeral=True)


@bot.tree.command(name="info", description="FNStock Bot info")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(title="⚡ FNStock Bot", color=0x00c8ff)
    embed.add_field(name="👑 Staff",    value="`/aggiungi` — add an account",        inline=False)
    embed.add_field(name="🛒 Buyers",  value="Click **BUY NOW** on any account",     inline=False)
    embed.add_field(name="🎫 Support", value="Open a ticket in **#support**",        inline=False)
    embed.set_footer(text="FNStock · Verified Fortnite Accounts")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.command(name="sync")
async def sync(ctx):
    if not ctx.author.guild_permissions.administrator:
        return
    synced = await bot.tree.sync()
    await ctx.send(f"✅ {len(synced)} commands synced.", delete_after=5)


bot.run(TOKEN)
