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


# ══════════════════════════════════════════
#  BUY BUTTON
# ══════════════════════════════════════════
class AcquistaView(discord.ui.View):
    def __init__(self, acc_id: int):
        super().__init__(timeout=None)
        self.acc_id = acc_id

    @discord.ui.button(label="🛒  BUY NOW", style=discord.ButtonStyle.success)
    async def acquista(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = interaction.guild.get_channel(PAGAMENTO_CH)
        if ch:
            msg = (
                f"╔══════════════════════════╗\n"
                f"       🛒 **PURCHASE REQUEST**\n"
                f"╚══════════════════════════╝\n\n"
                f"You selected **Account #{self.acc_id:03d}**!\n\n"
                f"📌 Head over to {ch.mention} and follow the payment instructions.\n"
                f"🎫 Then open a ticket in **#support** mentioning ID **#{self.acc_id:03d}**.\n\n"
                f"⚡ *Thank you for choosing FNStock!*"
            )
        else:
            msg = (
                f"🛒 **Account #{self.acc_id:03d}** — Purchase Info\n\n"
                f"Go to **#payment-methods** and open a support ticket with ID **#{self.acc_id:03d}**!\n"
                f"⚡ *Thank you for choosing FNStock!*"
            )
        await interaction.response.send_message(msg, ephemeral=True)


# ══════════════════════════════════════════
#  MODALS — 4 tipi: Normal / Normal+Pack /
#           Featured / Featured+Pack
#  Tutti con foto
# ══════════════════════════════════════════

class NormalModal(discord.ui.Modal, title="🎮 Add Normal Account"):
    prezzo   = discord.ui.TextInput(label="💰 Price (e.g. 35.00)",                    placeholder="35.00",                            required=True,  max_length=10)
    livello  = discord.ui.TextInput(label="🏆 Level (e.g. 150)",                      placeholder="150",                              required=True,  max_length=10)
    num_skin = discord.ui.TextInput(label="🎨 Skins & V-Bucks (e.g. 24 skins, 1500)", placeholder="24 skins, 1500 vbucks",           required=True,  max_length=60)
    skins    = discord.ui.TextInput(label="👗 Included skins (comma separated)",      placeholder="Skull Trooper, Black Knight...",   required=True,  max_length=500, style=discord.TextStyle.paragraph)
    foto     = discord.ui.TextInput(label="📸 Photo link (https://i.imgur.com/...)",  placeholder="https://i.imgur.com/abc1234.png",  required=False, max_length=300)

    async def on_submit(self, interaction: discord.Interaction):
        await pubblica(interaction, self.prezzo.value, self.livello.value,
                       self.num_skin.value, self.skins.value, "", self.foto.value, False)


class NormalPackModal(discord.ui.Modal, title="🎮 Add Normal Account + Pack"):
    prezzo   = discord.ui.TextInput(label="💰 Price (e.g. 35.00)",                    placeholder="35.00",                                    required=True,  max_length=10)
    livello  = discord.ui.TextInput(label="🏆 Level (e.g. 150)",                      placeholder="150",                                      required=True,  max_length=10)
    num_skin = discord.ui.TextInput(label="🎨 Skins & V-Bucks (e.g. 24 skins, 1500)", placeholder="24 skins, 1500 vbucks",                   required=True,  max_length=60)
    skins    = discord.ui.TextInput(label="👗 Included skins (comma separated)",      placeholder="Skull Trooper, Black Knight...",           required=True,  max_length=400, style=discord.TextStyle.paragraph)
    pack_foto= discord.ui.TextInput(label="📦 Packs · 📸 Photo  (pack name, https://)",placeholder="Darkfire Bundle · https://i.imgur.com/...",required=False, max_length=350)

    async def on_submit(self, interaction: discord.Interaction):
        pack, foto = parse_pack_foto(self.pack_foto.value)
        await pubblica(interaction, self.prezzo.value, self.livello.value,
                       self.num_skin.value, self.skins.value, pack, foto, False)


class FeaturedModal(discord.ui.Modal, title="⭐ Add Featured Account"):
    prezzo   = discord.ui.TextInput(label="💰 Price (e.g. 95.00)",                    placeholder="95.00",                            required=True,  max_length=10)
    livello  = discord.ui.TextInput(label="🏆 Level (e.g. 412)",                      placeholder="412",                              required=True,  max_length=10)
    num_skin = discord.ui.TextInput(label="🎨 Skins & V-Bucks (e.g. 34 skins, 2800)", placeholder="34 skins, 2800 vbucks",           required=True,  max_length=60)
    skins    = discord.ui.TextInput(label="👗 Included skins (comma separated)",      placeholder="Skull Trooper, Ghoul Trooper...",  required=True,  max_length=500, style=discord.TextStyle.paragraph)
    foto     = discord.ui.TextInput(label="📸 Photo link (https://i.imgur.com/...)",  placeholder="https://i.imgur.com/abc1234.png",  required=False, max_length=300)

    async def on_submit(self, interaction: discord.Interaction):
        await pubblica(interaction, self.prezzo.value, self.livello.value,
                       self.num_skin.value, self.skins.value, "", self.foto.value, True)


class FeaturedPackModal(discord.ui.Modal, title="⭐ Add Featured Account + Pack"):
    prezzo   = discord.ui.TextInput(label="💰 Price (e.g. 95.00)",                    placeholder="95.00",                                       required=True,  max_length=10)
    livello  = discord.ui.TextInput(label="🏆 Level (e.g. 412)",                      placeholder="412",                                         required=True,  max_length=10)
    num_skin = discord.ui.TextInput(label="🎨 Skins & V-Bucks (e.g. 34 skins, 2800)", placeholder="34 skins, 2800 vbucks",                      required=True,  max_length=60)
    skins    = discord.ui.TextInput(label="👗 Included skins (comma separated)",      placeholder="Skull Trooper, Ghoul Trooper...",             required=True,  max_length=400, style=discord.TextStyle.paragraph)
    pack_foto= discord.ui.TextInput(label="📦 Packs · 📸 Photo  (pack name · https://)",placeholder="Darkfire Bundle · https://i.imgur.com/...",required=False, max_length=350)

    async def on_submit(self, interaction: discord.Interaction):
        pack, foto = parse_pack_foto(self.pack_foto.value)
        await pubblica(interaction, self.prezzo.value, self.livello.value,
                       self.num_skin.value, self.skins.value, pack, foto, True)


# ══════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════
def parse_pack_foto(raw: str):
    """Separa pack e foto dal campo combinato usando · o | come separatore"""
    raw = raw.strip()
    for sep in ["·", "|", "•"]:
        if sep in raw:
            parts = raw.split(sep, 1)
            left, right = parts[0].strip(), parts[1].strip()
            if right.startswith("http"):
                return left, right
            elif left.startswith("http"):
                return right, left
            else:
                return left, right
    if raw.startswith("http"):
        return "", raw
    return raw, ""


async def pubblica(interaction, prezzo, livello, num_skin_vb, skins, pack, foto, featured):
    global account_counter
    acc_id = account_counter
    account_counter += 1

    # ── Colori e stile
    if featured:
        color = 0xf5c842
        title = f"✦ FEATURED ACCOUNT  ·  ID #{acc_id:03d}"
        badge = "⭐ FEATURED"
    else:
        color = 0x7c3aed
        title = f"◈ ACCOUNT AVAILABLE  ·  ID #{acc_id:03d}"
        badge = "🎮 FOR SALE"

    embed = discord.Embed(title=title, color=color)

    # Immagine
    foto = foto.strip() if foto else ""
    if foto and foto.startswith("http"):
        embed.set_image(url=foto)

    # Thumbnail FNStock logo placeholder
    if interaction.guild and interaction.guild.icon:
        embed.set_thumbnail(url=interaction.guild.icon.url)

    # Campi principali
    embed.add_field(
        name="━━━━━━━━━━━━━━━━━━━━━━",
        value=(
            f"💰 **Price:** €{prezzo.strip()}\n"
            f"🏆 **Level:** Lv. {livello.strip()}\n"
            f"🎨 **Skins & V-Bucks:** {num_skin_vb.strip()}"
        ),
        inline=False
    )

    embed.add_field(
        name="👗  INCLUDED SKINS",
        value=f"```{skins.strip()}```",
        inline=False
    )

    if pack and pack.strip():
        embed.add_field(
            name="📦  INCLUDED PACKS",
            value=f"```{pack.strip()}```",
            inline=False
        )

    embed.add_field(
        name="━━━━━━━━━━━━━━━━━━━━━━",
        value="✅  Staff verified  ·  🔒  Email change included  ·  ⚡  Fast delivery",
        inline=False
    )

    if featured:
        embed.set_author(
            name=f"{badge} — FNStock",
            icon_url=interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
        )
    else:
        embed.set_author(name=f"{badge} — FNStock")

    embed.set_footer(text="FNStock · Premium Fortnite Accounts  |  Click BUY NOW to purchase")

    announce = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔥  **NEW FEATURED ACCOUNT AVAILABLE!**\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        if featured else
        "🆕  **New account just listed!**"
    )

    await interaction.response.send_message(content=announce, embed=embed, view=AcquistaView(acc_id))


# ══════════════════════════════════════════
#  VIEW SCELTA TIPO
# ══════════════════════════════════════════
class TipoAccountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="🎮 Normal", style=discord.ButtonStyle.primary, row=0)
    async def normale(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NormalModal())

    @discord.ui.button(label="🎮 Normal + Pack", style=discord.ButtonStyle.primary, row=0)
    async def normale_pack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NormalPackModal())

    @discord.ui.button(label="⭐ Featured", style=discord.ButtonStyle.success, row=1)
    async def featured(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FeaturedModal())

    @discord.ui.button(label="⭐ Featured + Pack", style=discord.ButtonStyle.success, row=1)
    async def featured_pack(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FeaturedPackModal())


# ══════════════════════════════════════════
#  COMANDI
# ══════════════════════════════════════════
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
    embed = discord.Embed(
        title="📋 Select Account Type",
        description=(
            "Choose the type of account you want to list:\n\n"
            "🎮 **Normal** — Standard account\n"
            "🎮 **Normal + Pack** — Standard with bundle packs\n"
            "⭐ **Featured** — Premium highlighted account\n"
            "⭐ **Featured + Pack** — Premium with bundle packs"
        ),
        color=0x8b3cf7
    )
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
    embed = discord.Embed(
        title="⚡ FNStock Bot",
        description="The official bot for FNStock — Premium Fortnite Accounts.",
        color=0x00c8ff
    )
    embed.add_field(name="👑 Staff",    value="`/aggiungi` — list a new account",    inline=False)
    embed.add_field(name="🛒 Buyers",  value="Click **BUY NOW** on any listing",     inline=False)
    embed.add_field(name="🎫 Support", value="Open a ticket in **#support**",        inline=False)
    embed.set_footer(text="FNStock · Premium Fortnite Accounts")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.command(name="sync")
async def sync(ctx):
    if not ctx.author.guild_permissions.administrator:
        return
    synced = await bot.tree.sync()
    await ctx.send(f"✅ {len(synced)} commands synced.", delete_after=5)


bot.run(TOKEN)
