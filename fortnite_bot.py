import discord
from discord.ext import commands
import aiohttp
from bs4 import BeautifulSoup
import asyncio
import os
import random

TOKEN = os.environ.get("TOKEN")

già_mostrati = set()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Lista di User-Agent diversi per sembrare browser reali
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

BASE_URL = "https://www.eldorado.gg/fortnite-accounts/g/2295"


async def scrape_eldorado(numero: int = 5) -> list[dict]:
    url = f"{BASE_URL}?sort=price_asc"

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,it;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }

    tutti = []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                status = resp.status
                html = await resp.text()

        if status != 200:
            return []

        soup = BeautifulSoup(html, "html.parser")

        # Prova tutti i possibili selettori
        cards = (
            soup.select("div.item-card") or
            soup.select("article.offer-card") or
            soup.select("[class*='OfferCard']") or
            soup.select("[class*='offer-card']") or
            soup.select("[class*='item-card']") or
            soup.select("[class*='listing']") or
            soup.select("a[href*='/fortnite-accounts/']")
        )

        # Fallback: cerca tutti i link che portano a listing
        if not cards:
            cards = soup.find_all("a", href=lambda h: h and "/fortnite-accounts/" in h and "/g/" not in h)

        for card in cards:
            try:
                # Recupera testo completo della card
                testo_completo = card.get_text(" | ", strip=True)

                titolo = testo_completo[:100] if testo_completo else "Account Fortnite"

                # Cerca prezzo con simbolo $
                prezzo = "N/D"
                for tag in card.find_all(True):
                    t = tag.get_text(strip=True)
                    if "$" in t and len(t) < 20:
                        prezzo = t
                        break

                # Cerca livello
                livello = "N/D"
                for tag in card.find_all(True):
                    t = tag.get_text(strip=True).lower()
                    if any(x in t for x in ["level", "lv ", "lvl"]) and len(t) < 30:
                        livello = tag.get_text(strip=True)
                        break

                # Cerca skin
                skin = "N/D"
                for tag in card.find_all(True):
                    t = tag.get_text(strip=True).lower()
                    if any(x in t for x in ["skin", "outfit", "cosmetic"]) and len(t) < 150:
                        skin = tag.get_text(strip=True)[:120]
                        break

                # Link
                if card.name == "a":
                    href = card.get("href", "")
                else:
                    a = card.find("a", href=True)
                    href = a["href"] if a else ""

                link = ("https://www.eldorado.gg" + href) if href.startswith("/") else href
                if not link:
                    link = BASE_URL

                if link not in già_mostrati:
                    tutti.append({
                        "titolo": titolo,
                        "prezzo": prezzo,
                        "livello": livello,
                        "skin": skin,
                        "link": link,
                    })

            except Exception:
                continue

    except Exception:
        return []

    nuovi = tutti[:numero]
    for acc in nuovi:
        già_mostrati.add(acc["link"])

    return nuovi


def crea_embed(account: dict, indice: int) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎮 Account #{indice}",
        url=account["link"],
        color=0x00BFFF,
    )
    embed.add_field(name="📝 Titolo", value=account["titolo"][:200] or "N/D", inline=False)
    embed.add_field(name="💰 Prezzo", value=account["prezzo"], inline=True)
    embed.add_field(name="⭐ Livello", value=account["livello"], inline=True)
    embed.add_field(name="👗 Skin", value=account["skin"] or "N/D", inline=False)
    embed.add_field(name="🔗 Link", value=f"[Vedi su Eldorado]({account['link']})", inline=False)
    embed.set_footer(text="eldorado.gg • Fortnite Accounts")
    return embed


@bot.event
async def on_ready():
    print(f"✅ Bot online come {bot.user}")


@bot.command(name="cerca", aliases=["search", "fortnite"])
async def cerca(ctx, numero: int = 5):
    numero = max(1, min(numero, 10))
    msg = await ctx.send("🔍 Ricerca in corso su eldorado.gg...")

    try:
        accounts = await asyncio.wait_for(scrape_eldorado(numero), timeout=25)
    except asyncio.TimeoutError:
        await msg.edit(content="⏰ Timeout: eldorado.gg troppo lento. Riprova tra poco.")
        return

    await msg.delete()

    if not accounts:
        await ctx.send(
            "❌ Nessun risultato trovato.\n"
            "eldorado.gg potrebbe star bloccando le richieste temporaneamente.\n"
            "Riprova tra qualche minuto oppure usa `!reset` e riprova."
        )
        return

    await ctx.send(f"✅ **{len(accounts)}** account trovati:")
    for i, acc in enumerate(accounts, start=1):
        await ctx.send(embed=crea_embed(acc, i))
        await asyncio.sleep(0.5)


@bot.command(name="reset")
async def reset(ctx):
    già_mostrati.clear()
    await ctx.send("🔄 Memoria resettata!")


@bot.command(name="aiuto")
async def aiuto(ctx):
    embed = discord.Embed(title="📖 Comandi", color=0x7289DA)
    embed.add_field(name="!cerca [numero]", value="Cerca account Fortnite (default: 5)", inline=False)
    embed.add_field(name="!reset", value="Resetta la lista account già visti", inline=False)
    await ctx.send(embed=embed)


bot.run(TOKEN)
