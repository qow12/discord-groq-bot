import os
import time
import discord
import pytz
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime

# ================== ENV ==================
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ================== GROQ ==================
client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.1-8b-instant"

# ================== DISCORD ==================
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# ================== CONFIG ==================
PREFIX = "orca"
COOLDOWN = 5
TZ = pytz.timezone("Asia/Jakarta")
MAX_DISCORD_CHARS = 1900

user_cooldown = {}

# ================== SYSTEM PROMPT ==================
BASE_SYSTEM_PROMPT = """
Kamu adalah AI berbahasa Indonesia dengan gaya sangat santai, savage, blak-blakan, dan nyeplos.
Gunakan bahasa nongkrong, ceplas-ceplos, dan agak kasar secukupnya (tidak menghina SARA).
Jawaban harus langsung ke inti, anti muter, anti sok pinter.
Kalau pertanyaan ngaco, bilang ngaco.
Kalau bisa lebih efisien, sindir dikit.
Tetap logis, relevan, dan up to date, tapi jangan kaku—kayak temen jujur.
Kalau user galau atau capek, empatik tapi nyentil halus.
"""

# ================== UTILS ==================
def split_message(text, limit=MAX_DISCORD_CHARS):
    return [text[i:i+limit] for i in range(0, len(text), limit)]

# ================== EVENTS ==================
@bot.event
async def on_ready():
    print(f"{bot.user} online 🚀")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # DETEKSI PREFIX ATAU REPLY KE BOT
    is_prefix = message.content.lower().startswith(PREFIX)
    is_reply_to_bot = (
        message.reference
        and isinstance(message.reference.resolved, discord.Message)
        and message.reference.resolved.author == bot.user
    )

    if not is_prefix and not is_reply_to_bot:
        return

    # ================== COOLDOWN ==================
    user_id = message.author.id
    now = time.time()

    if user_id in user_cooldown and now - user_cooldown[user_id] < COOLDOWN:
        remaining = int(COOLDOWN - (now - user_cooldown[user_id]))
        await message.reply(
            f"santai bentar 😅 {remaining}s lagi",
            mention_author=False
        )
        return

    user_cooldown[user_id] = now

    # ================== CONTENT ==================
    if is_prefix:
        content = message.content[len(PREFIX):].strip()
    else:
        content = message.content.strip()

    if not content:
        await message.reply("iya kenapa 😅", mention_author=False)
        return

    # ================== USER INFO ==================
    nickname = message.author.display_name
    now_time = datetime.now(TZ).strftime("%A, %d %B %Y %H:%M WIB")

    # ================== PROMPT ==================
    system_prompt = f"""
{BASE_SYSTEM_PROMPT}

Nama orang yang sedang berbicara denganmu adalah: {nickname}.
Panggil dia dengan nama itu secara natural, jangan berlebihan.

Waktu sekarang: {now_time}.
Balas seolah-olah ngobrol langsung dengannya.
"""

    # ================== GROQ ==================
    async with message.channel.typing():
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.6,
                max_tokens=220,
                top_p=0.9
            )

            reply = response.choices[0].message.content
            if not reply:
                reply = "gue bengong bentar 😅 coba ulangi"

            # ================== SEND ==================
            for part in split_message(reply.strip()):
                await message.reply(
                    part,
                    mention_author=False
                )

        except Exception as e:
            print("GROQ ERROR:", repr(e))
            await message.reply(
                "lagi error njir 😅 coba bentar lagi",
                mention_author=False
            )

# ================== RUN ==================
bot.run(DISCORD_TOKEN)