import discord
from discord.ext import commands
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import os

# ─────────────────────────────────────────
#  TOKEN preso dalle variabili Railway
# ─────────────────────────────────────────
TOKEN = os.environ.get("TOKEN")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))

# ─────────────────────────────────────────
#  Memoria account già mostrati (si resetta al riavvio)
# ─────────────────────────────────────────
già_mostrati = set()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}

BASE_URL = "https://www.eldorado.gg/fortnite-accounts/g/2295"


async def scrape_eldorado(numero: int = 5) -> list[dict]:
    """
    Scrapa eldorado.gg e ritorna solo account NON ancora mostrati.
    """
    url = f"{BASE_URL}?sort=price_asc"
    tutti = []

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return []
            html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select(
        "div.item-card, article.offer-card, "
        "div[class*='offer'], div[class*='listing'], div[class*='card']"
    )

    if not cards:
        cards = soup.find_all(
            "div",
            class_=lambda c: c and any(x in c.lower() for x in ["card", "offer", "item", "listing"])
        )

    for card in cards:
        try:
            titolo_tag = card.find(
                ["h2", "h3", "h4", "span"],
                class_=lambda c: c and "title" in c.lower()
            )
            titolo = titolo_tag.get_text(strip=True) if titolo_tag else "N/D"

            prezzo_tag = card.find(
                ["span", "div", "p"],
                class_=lambda c: c and "price" in c.lower()
            )
            prezzo = prezzo_tag.get_text(strip=True) if prezzo_tag else "N/D"

            livello = "N/D"
            for tag in card.find_all(["span", "div", "li", "p"]):
                testo = tag.get_text(strip=True).lower()
                if any(x in testo for x in ["level", "livello", "lv "]):
                    livello = tag.get_text(strip=True)
                    break

            skin = "N/D"
            for tag in card.find_all(["span", "div", "li", "p"]):
                testo = tag.get_text(strip=True).lower()
                if any(x in testo for x in ["skin", "outfit", "cosmetic"]):
                    skin = tag.get_text(strip=True)[:120]
                    break

            link_tag = card.find("a", href=True)
            if link_tag:
                href = link_tag["href"]
                link = href if href.startswith("http") else "https://www.eldorado.gg" + href
            else:
                link = BASE_URL

            # Usa il link come ID univoco — salta se già mostrato
            if link not in già_mostrati and titolo != "N/D":
                tutti.append({
                    "titolo": titolo,
                    "prezzo": prezzo,
                    "livello": livello,
                    "skin": skin,
                    "link": link,
                })

        except Exception:
            continue

    # Segna come mostrati e ritorna solo il numero richiesto
    nuovi = tutti[:numero]
    for acc in nuovi:
        già_mostrati.add(acc["link"])

    return nuovi


def crea_embed(account: dict, indice: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎮 Account #{indice} — {account['titolo'][:80]}",
        url=account["link"],
        color=0x00BFFF,
    )
    embed.add_field(name="💰 Prezzo", value=account["prezzo"], inline=True)
    embed.add_field(name="⭐ Livello", value=account["livello"], inline=True)
    embed.add_field(name="👗 Skin", value=account["skin"] or "N/D", inline=False)
    embed.add_field(
        name="🔗 Link",
        value=f"[Vedi su Eldorado]({account['link']})",
        inline=False,
    )
    embed.set_footer(text="eldorado.gg • Fortnite Accounts")
    return embed


# ─────────────────────────────────────────
#  COMANDI
# ─────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅ Bot online come {bot.user}")


@bot.command(name="cerca", aliases=["search", "fortnite"])
async def cerca(ctx, numero: int = 5):
    """
    !cerca [numero]
    Mostra account Fortnite da eldorado.gg — non ripete quelli già mostrati.
    """
    numero = max(1, min(numero, 10))
    msg = await ctx.send("🔍 Ricerca in corso su eldorado.gg...")

    try:
        accounts = await asyncio.wait_for(scrape_eldorado(numero), timeout=15)
    except asyncio.TimeoutError:
        await msg.edit(content="⏰ Timeout: eldorado.gg troppo lento. Riprova.")
        return

    await msg.delete()

    if not accounts:
        await ctx.send(
            "❌ Nessun account nuovo trovato.\n"
            "Potrebbero essere finiti i risultati, oppure eldorado sta bloccando le richieste.\n"
            "Usa `!reset` per ricominciare da capo."
        )
        return

    await ctx.send(f"✅ **{len(accounts)}** account nuovi trovati:")
    for i, acc in enumerate(accounts, start=1):
        await ctx.send(embed=crea_embed(acc, i))
        await asyncio.sleep(0.5)


@bot.command(name="reset")
async def reset(ctx):
    """Resetta la memoria degli account già mostrati."""
    già_mostrati.clear()
    await ctx.send("🔄 Memoria resettata! Il prossimo `!cerca` mostrerà di nuovo tutti gli account.")


@bot.command(name="aiuto")
async def aiuto(ctx):
    embed = discord.Embed(title="📖 Comandi", color=0x7289DA)
    embed.add_field(name="!cerca [numero]", value="Cerca account Fortnite (default: 5)", inline=False)
    embed.add_field(name="!reset", value="Resetta la lista account già visti", inline=False)
    await ctx.send(embed=embed)


# ─────────────────────────────────────────
bot.run(TOKEN)
