import discord
from discord.ext import commands
import aiohttp
import asyncio
import os

TOKEN = os.environ.get("TOKEN")

già_mostrati = set()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

G2A_API = "https://www.g2a.com/search/api/v3/products"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.g2a.com/",
}


async def cerca_g2a(query: str, numero: int = 5) -> list[dict]:
    params = {
        "search": query,
        "itemsPerPage": 20,
        "page": 1,
        "currency": "EUR",
        "language": "en",
    }

    risultati = []

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(G2A_API, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        prodotti = data.get("products", data.get("data", data.get("items", [])))
        if not prodotti and isinstance(data, list):
            prodotti = data

        for p in prodotti:
            try:
                # ID univoco
                pid = str(p.get("id", p.get("slug", p.get("uuid", ""))))
                if pid in già_mostrati:
                    continue

                nome = p.get("name", p.get("title", "N/D"))
                
                # Prezzo
                prezzo_raw = p.get("minPrice", p.get("price", p.get("lowestPrice", "N/D")))
                prezzo = f"€{prezzo_raw}" if prezzo_raw != "N/D" else "N/D"

                # Valutazione
                rating = p.get("rating", p.get("reviewsRating", "N/D"))
                if rating != "N/D":
                    rating = f"⭐ {round(float(rating), 1)}/5"

                # Link
                slug = p.get("slug", p.get("url", ""))
                if slug.startswith("http"):
                    link = slug
                elif slug:
                    link = f"https://www.g2a.com/{slug}"
                else:
                    link = "https://www.g2a.com"

                # Immagine
                immagine = p.get("imageUrl", p.get("image", p.get("coverImageUrl", None)))

                risultati.append({
                    "id": pid,
                    "nome": nome,
                    "prezzo": prezzo,
                    "rating": rating,
                    "link": link,
                    "immagine": immagine,
                })

                if len(risultati) >= numero:
                    break

            except Exception:
                continue

    except Exception:
        return []

    for r in risultati:
        già_mostrati.add(r["id"])

    return risultati


def crea_embed(prodotto: dict, indice: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎮 #{indice} — {prodotto['nome'][:90]}",
        url=prodotto["link"],
        color=0xF77F00,
    )
    embed.add_field(name="💰 Prezzo", value=prodotto["prezzo"], inline=True)
    embed.add_field(name="⭐ Rating", value=prodotto["rating"], inline=True)
    embed.add_field(name="🔗 Link", value=f"[Vedi su G2A]({prodotto['link']})", inline=False)
    if prodotto.get("immagine"):
        embed.set_thumbnail(url=prodotto["immagine"])
    embed.set_footer(text="G2A.com")
    return embed


@bot.event
async def on_ready():
    print(f"✅ Bot online come {bot.user}")


@bot.command(name="cerca", aliases=["fortnite", "search"])
async def cerca(ctx, *, query: str = "fortnite account"):
    """
    !cerca fortnite account
    !cerca fortnite stacked account
    !cerca fortnite rare skins
    """
    msg = await ctx.send(f"🔍 Cerco **{query}** su G2A...")

    try:
        prodotti = await asyncio.wait_for(cerca_g2a(query, 5), timeout=20)
    except asyncio.TimeoutError:
        await msg.edit(content="⏰ Timeout, riprova tra poco.")
        return

    await msg.delete()

    if not prodotti:
        await ctx.send(
            f"❌ Nessun risultato per **{query}**.\n"
            "Prova con `!cerca fortnite account` oppure `!reset` e riprova."
        )
        return

    await ctx.send(f"✅ **{len(prodotti)}** risultati per **{query}**:")
    for i, p in enumerate(prodotti, start=1):
        await ctx.send(embed=crea_embed(p, i))
        await asyncio.sleep(0.4)


@bot.command(name="reset")
async def reset(ctx):
    già_mostrati.clear()
    await ctx.send("🔄 Memoria resettata!")


@bot.command(name="aiuto")
async def aiuto(ctx):
    embed = discord.Embed(title="📖 Comandi", color=0xF77F00)
    embed.add_field(name="!cerca [ricerca]", value="Cerca su G2A\nEs: `!cerca fortnite account`\nEs: `!cerca fortnite rare skins`", inline=False)
    embed.add_field(name="!reset", value="Resetta la lista prodotti già visti", inline=False)
    await ctx.send(embed=embed)


bot.run(TOKEN)
