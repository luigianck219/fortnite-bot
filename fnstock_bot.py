import discord
from discord.ext import commands
from discord import app_commands
import os

# ─────────────────────────────────────────
#  CONFIGURAZIONE — imposta su Railway
#  TOKEN        = token del bot Discord
#  PAGAMENTO_CH = ID del canale #metodi-pagamento
#  STAFF_ROLE   = ID del ruolo Staff/Admin
# ─────────────────────────────────────────
TOKEN        = os.environ.get("TOKEN")
PAGAMENTO_CH = int(os.environ.get("PAGAMENTO_CH", "0"))
STAFF_ROLE   = int(os.environ.get("STAFF_ROLE",   "0"))

# ─────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Contatore ID account
account_counter = 1


# ══════════════════════════════════════════
#  MODAL — Form che lo staff compila
# ══════════════════════════════════════════
class AccountModal(discord.ui.Modal, title="➕ Aggiungi Account FNStock"):

    prezzo = discord.ui.TextInput(
        label="💰 Prezzo (es: 35.00)",
        placeholder="35.00",
        required=True,
        max_length=10,
    )
    livello = discord.ui.TextInput(
        label="🏆 Livello account (es: 150)",
        placeholder="150",
        required=True,
        max_length=10,
    )
    num_skin = discord.ui.TextInput(
        label="🎨 Numero skin totali (es: 24)",
        placeholder="24",
        required=True,
        max_length=5,
    )
    vbucks = discord.ui.TextInput(
        label="💎 V-Bucks (es: 1500 — scrivi 0 se nessuno)",
        placeholder="0",
        required=True,
        max_length=10,
    )
    skin_list = discord.ui.TextInput(
        label="👗 Skin incluse (separate da virgola)",
        placeholder="Skull Trooper, Black Knight, Renegade Raider...",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500,
    )

    def __init__(self, pack: str, foto: str, featured: bool):
        super().__init__()
        self.pack_value    = pack
        self.foto_value    = foto
        self.featured_flag = featured

    async def on_submit(self, interaction: discord.Interaction):
        global account_counter

        acc_id   = account_counter
        account_counter += 1

        prezzo   = self.prezzo.value.strip()
        livello  = self.livello.value.strip()
        num_skin = self.num_skin.value.strip()
        vbucks   = self.vbucks.value.strip()
        skins    = self.skin_list.value.strip()
        pack     = self.pack_value.strip()
        foto     = self.foto_value.strip()
        featured = self.featured_flag

        # ── Colore embed
        color = 0xf5c842 if featured else 0x8b3cf7

        # ── Costruzione embed
        embed = discord.Embed(
            title=("⭐ ACCOUNT FEATURED" if featured else "🎮 ACCOUNT DISPONIBILE") + f" — ID #{acc_id:03d}",
            color=color,
        )

        if foto:
            embed.set_image(url=foto)

        embed.add_field(name="💰 Prezzo",       value=f"**€{prezzo}**",          inline=True)
        embed.add_field(name="🏆 Livello",       value=f"Lv. {livello}",          inline=True)
        embed.add_field(name="🎨 Skin totali",   value=f"{num_skin} skin",        inline=True)
        embed.add_field(name="💎 V-Bucks",       value=vbucks,                    inline=True)
        embed.add_field(name="👗 Skin incluse",  value=skins,                     inline=False)

        if pack:
            embed.add_field(name="📦 Pack inclusi", value=pack, inline=False)

        embed.set_footer(text="✅ Verificato Staff FNStock · 🔒 Cambio email incluso")

        if featured:
            embed.set_author(name="⭐ FEATURED ACCOUNT", icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

        # ── View con tasto Acquista
        view = AcquistaView(acc_id=acc_id, pagamento_ch=PAGAMENTO_CH)

        await interaction.response.send_message(
            content=("🔥 **Nuovo account FEATURED aggiunto!**" if featured else "🆕 **Nuovo account disponibile!**"),
            embed=embed,
            view=view,
        )


# ══════════════════════════════════════════
#  MODAL PASSO 2 — Pack e foto (separati
#  perché il Modal ha max 5 campi)
# ══════════════════════════════════════════
class PackFotoModal(discord.ui.Modal, title="📦 Pack & Foto account"):

    pack = discord.ui.TextInput(
        label="📦 Pack eventuali (lascia vuoto se nessuno)",
        placeholder="Es: Darkfire Bundle, Frozen Legends Pack",
        required=False,
        max_length=200,
    )
    foto = discord.ui.TextInput(
        label="📸 Link foto (imgur, discord CDN...)",
        placeholder="https://i.imgur.com/...",
        required=False,
        max_length=300,
    )

    def __init__(self, featured: bool):
        super().__init__()
        self.featured_flag = featured

    async def on_submit(self, interaction: discord.Interaction):
        modal = AccountModal(
            pack=self.pack.value,
            foto=self.foto.value,
            featured=self.featured_flag,
        )
        await interaction.response.send_modal(modal)


# ══════════════════════════════════════════
#  BUTTON — Acquista ora
# ══════════════════════════════════════════
class AcquistaView(discord.ui.View):
    def __init__(self, acc_id: int, pagamento_ch: int):
        super().__init__(timeout=None)
        self.acc_id       = acc_id
        self.pagamento_ch = pagamento_ch

    @discord.ui.button(label="🛒  ACQUISTA ORA", style=discord.ButtonStyle.primary, custom_id="acquista_ora")
    async def acquista(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = interaction.guild.get_channel(self.pagamento_ch)
        if ch:
            msg = (
                f"💳 Per acquistare l'**Account #{self.acc_id:03d}** "
                f"vai in {ch.mention} e segui le istruzioni!\n"
                f"Poi apri un ticket in **#apri-ticket** indicando l'ID dell'account."
            )
        else:
            msg = (
                f"💳 Per acquistare l'**Account #{self.acc_id:03d}** "
                f"vai nel canale **#metodi-pagamento** e apri un ticket!"
            )
        await interaction.response.send_message(msg, ephemeral=True)


# ══════════════════════════════════════════
#  VIEW SCELTA — Featured o normale
# ══════════════════════════════════════════
class TipoAccountView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="⭐ Featured", style=discord.ButtonStyle.success)
    async def featured(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PackFotoModal(featured=True))

    @discord.ui.button(label="🎮 Normale", style=discord.ButtonStyle.primary)
    async def normale(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PackFotoModal(featured=False))


# ══════════════════════════════════════════
#  HELPER — controlla se staff
# ══════════════════════════════════════════
def is_staff(member: discord.Member) -> bool:
    if STAFF_ROLE == 0:
        return member.guild_permissions.administrator
    return any(r.id == STAFF_ROLE for r in member.roles) or member.guild_permissions.administrator


# ══════════════════════════════════════════
#  COMANDI
# ══════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"✅ FNStock Bot online — {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Slash commands sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"❌ Errore sync: {e}")


# ── /aggiungi — apre il pannello staff
@bot.tree.command(name="aggiungi", description="[STAFF] Aggiungi un nuovo account Fortnite")
async def aggiungi(interaction: discord.Interaction):
    if not is_staff(interaction.user):
        await interaction.response.send_message(
            "❌ Non hai i permessi per usare questo comando.", ephemeral=True
        )
        return

    embed = discord.Embed(
        title="📋 Aggiungi nuovo account",
        description="Scegli il tipo di account da pubblicare:",
        color=0x8b3cf7,
    )
    await interaction.response.send_message(embed=embed, view=TipoAccountView(), ephemeral=True)


# ── /reset_counter — resetta il contatore ID (solo admin)
@bot.tree.command(name="reset_counter", description="[ADMIN] Resetta il contatore ID account")
async def reset_counter(interaction: discord.Interaction):
    global account_counter
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Solo gli admin possono usare questo comando.", ephemeral=True)
        return
    account_counter = 1
    await interaction.response.send_message("🔄 Contatore ID resettato a #001.", ephemeral=True)


# ── /info — info sul bot
@bot.tree.command(name="info", description="Informazioni su FNStock Bot")
async def info(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚡ FNStock Bot",
        description="Bot ufficiale per la gestione dello shop FNStock.",
        color=0x00c8ff,
    )
    embed.add_field(name="👑 Staff", value="`/aggiungi` — pubblica un account", inline=False)
    embed.add_field(name="🛒 Clienti", value="Clicca **ACQUISTA ORA** su qualsiasi account", inline=False)
    embed.add_field(name="🎫 Supporto", value="Apri un ticket in **#apri-ticket**", inline=False)
    embed.set_footer(text="FNStock · Account Fortnite Verificati")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── !sync — forza sync slash commands (solo admin, fallback)
@bot.command(name="sync")
async def sync(ctx):
    if not ctx.author.guild_permissions.administrator:
        return
    synced = await bot.tree.sync()
    await ctx.send(f"✅ Sincronizzati {len(synced)} comandi.", delete_after=5)


# ─────────────────────────────────────────
bot.run(TOKEN)
