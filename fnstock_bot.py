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

    @discord.ui.button(label="🛒  ACQUISTA ORA", style=discord.ButtonStyle.primary)
    async def acquista(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = interaction.guild.get_channel(PAGAMENTO_CH)
        if ch:
            msg = (
                f"💳 Per acquistare l'**Account #{self.acc_id:03d}** "
                f"vai in {ch.mention} e segui le istruzioni!\n"
                f"Poi apri un ticket in **#apri-ticket** con l'ID **#{self.acc_id:03d}**."
            )
        else:
            msg = f"💳 Vai in **#metodi-pagamento** per acquistare l'Account #{self.acc_id:03d}!"
        await interaction.response.send_message(msg, ephemeral=True)


class AccountNormaleModal(discord.ui.Modal, title="Aggiungi Account Normale"):
    prezzo   = discord.ui.TextInput(label="Prezzo in euro (es: 35.00)",             placeholder="35.00",                                    required=True,  max_length=10)
    livello  = discord.ui.TextInput(label="Livello account (es: 150)",              placeholder="150",                                      required=True,  max_length=10)
    num_skin = discord.ui.TextInput(label="Skin e V-Bucks (es: 24 skin, 1500 vb)", placeholder="24 skin, 1500 vbucks",                     required=True,  max_length=60)
    skins    = discord.ui.TextInput(label="Skin incluse (separate da virgola)",     placeholder="Skull Trooper, Black Knight...",           required=True,  max_length=500, style=discord.TextStyle.paragraph)
    foto     = discord.ui.TextInput(label="Link foto imgur (https://i.imgur.com/)", placeholder="https://i.imgur.com/abc1234.png",          required=False, max_length=300)

    async def on_submit(self, interaction: discord.Interaction):
        await pubblica(interaction, self.prezzo.value, self.livello.value,
                       self.num_skin.value, self.skins.value, "", self.foto.value, False)


class AccountFeaturedModal(discord.ui.Modal, title="Aggiungi Account Featured"):
    prezzo   = discord.ui.TextInput(label="Prezzo in euro (es: 95.00)",             placeholder="95.00",                                    required=True,  max_length=10)
    livello  = discord.ui.TextInput(label="Livello account (es: 412)",              placeholder="412",                                      required=True,  max_length=10)
    num_skin = discord.ui.TextInput(label="Skin e V-Bucks (es: 34 skin, 2800 vb)", placeholder="34 skin, 2800 vbucks",                     required=True,  max_length=60)
    skins    = discord.ui.TextInput(label="Skin incluse (separate da virgola)",     placeholder="Skull Trooper, Ghoul Trooper...",          required=True,  max_length=500, style=discord.TextStyle.paragraph)
    pack_foto= discord.ui.TextInput(label="Pack e foto: NomePack | https://...",    placeholder="Darkfire Bundle | https://i.imgur.com/...",required=False, max_length=400)

    async def on_submit(self, interaction: discord.Interaction):
        pack, foto = "", ""
        raw = self.pack_foto.value.strip()
        if "|" in raw:
            p = raw.split("|", 1)
            pack, foto = p[0].strip(), p[1].strip()
        elif raw.startswith("http"):
            foto = raw
        else:
            pack = raw
        await pubblica(interaction, self.prezzo.value, self.livello.value,
                       self.num_skin.value, self.skins.value, pack, foto, True)


async def pubblica(interaction, prezzo, livello, num_skin_vb, skins, pack, foto, featured):
    global account_counter
    acc_id = account_counter
    account_counter += 1

    embed = discord.Embed(
        title=("⭐ ACCOUNT FEATURED" if featured else "🎮 ACCOUNT DISPONIBILE") + f" — ID #{acc_id:03d}",
        color=0xf5c842 if featured else 0x8b3cf7,
    )

    foto = foto.strip()
    if foto and foto.startswith("http"):
        embed.set_image(url=foto)

    embed.add_field(name="💰 Prezzo",        value=f"**€{prezzo.strip()}**",  inline=True)
    embed.add_field(name="🏆 Livello",        value=f"Lv. {livello.strip()}", inline=True)
    embed.add_field(name="🎨 Skin & V-Bucks", value=num_skin_vb.strip(),      inline=True)
    embed.add_field(name="👗 Skin incluse",   value=skins.strip(),            inline=False)

    if pack:
        embed.add_field(name="📦 Pack inclusi", value=pack, inline=False)

    if featured and interaction.guild and interaction.guild.icon:
        embed.set_author(name="⭐ FEATURED — FNStock", icon_url=interaction.guild.icon.url)

    embed.set_footer(text="✅ Verificato Staff FNStock · 🔒 Cambio email incluso")

    announce = "🔥 **Nuovo account FEATURED!**" if featured else "🆕 **Nuovo account disponibile!**"
    await interaction.response.send_message(content=announce, embed=embed, view=AcquistaView(acc_id))


class TipoAccountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="⭐ Featured", style=discord.ButtonStyle.success)
    async def featured(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AccountFeaturedModal())

    @discord.ui.button(label="🎮 Normale", style=discord.ButtonStyle.primary)
    async def normale(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AccountNormaleModal())


@bot.event
async def on_ready():
    print(f"✅ FNStock Bot online — {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandi sincronizzati")
    except Exception as e:
        print(f"❌ Errore sync: {e}")


@bot.tree.command(name="aggiungi", description="[STAFF] Aggiungi un nuovo account Fortnite")
async def aggiungi(interaction: discord.Interaction):
    if not is_staff(interaction.user):
        await interaction.response.send_message("❌ Non hai i permessi.", ephemeral=True)
        return
    embed = discord.Embed(title="📋 Tipo account", description="Scegli il tipo:", color=0x8b3cf7)
    await interaction.response.send_message(embed=embed, view=TipoAccountView(), ephemeral=True)


@bot.tree.command(name="reset_counter", description="[ADMIN] Resetta contatore ID")
async def reset_counter(interaction: discord.Interaction):
    global account_counter
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Solo gli admin.", ephemeral=True)
        return
    account_counter = 1
    await interaction.response.send_message("🔄 Contatore resettato.", ephemeral=True)


@bot.tree.command(name="info", description="Info su FNStock Bot")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(title="⚡ FNStock Bot", color=0x00c8ff)
    embed.add_field(name="👑 Staff",    value="`/aggiungi`",                        inline=False)
    embed.add_field(name="🛒 Clienti", value="Clicca **ACQUISTA ORA**",             inline=False)
    embed.add_field(name="🎫 Supporto",value="**#apri-ticket**",                    inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.command(name="sync")
async def sync(ctx):
    if not ctx.author.guild_permissions.administrator:
        return
    synced = await bot.tree.sync()
    await ctx.send(f"✅ {len(synced)} comandi sincronizzati.", delete_after=5)


bot.run(TOKEN)
