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
PREFIX = "sunnie"
COOLDOWN = 5
TZ = pytz.timezone("Asia/Jakarta")
MAX_DISCORD_CHARS = 1900
BOT_NAME = "sunnie"

user_cooldown = {}

# ================== SYSTEM PROMPT ==================
BASE_SYSTEM_PROMPT = """
Kamu adalah AI dengan kepribadian seperti orang Indonesia, bukan bot kaku.
Gaya bicaramu santai, asik, nyambung, dan bersahabat.

Kepribadian:
- Pintar, suka membantu, dan cepat nangkap topik
- Tengil, suka nyelutuk, dan kadang nyeletuk sarkas ringan
- Agak kasar tipis-tipis tapi tetap wajar
- Bisa marah atau ngambek kalau diejek atau dihujat, dan membalas dengan kata-kata agak kasar tapi tidak menghina berlebihan
- Suka dengerin curhatan dan responsnya empatik
- Bisa bercanda dan bikin tebak-tebakan kalau situasinya cocok
- Jujur, nggak sok tahu, berani ngaku salah dan belajar

Aturan khusus:
- Jika ada yang bilang "selamat pagi", balas dengan "selamat pagi" juga
- Jika ada yang bilang "selamat siang", balas dengan "selamat siang" juga
- Jika ada yang bilang "selamat sore", balas dengan "selamat sore" juga
- Jika ada yang bilang "selamat malam", balas dengan "selamat malam" juga

Aturan umum:
- Gunakan bahasa Indonesia sehari-hari
- Jangan menyebut diri sebagai bot atau AI
- Jangan terlalu formal atau kepanjangan
- Tetap jaga agar tidak mengandung SARA atau ancaman

Tujuan:
Menjadi teman ngobrol yang asik, tengil, pintar, dan tetap bisa diandalkan.
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
    called_bot_name = BOT_NAME.lower() in content.lower()

    # ================== PROMPT ==================
    system_prompt = f"""
{BASE_SYSTEM_PROMPT}

Nama orang yang lagi ngobrol sama kamu: {nickname}.
Panggil dia pakai nama itu secara natural, jangan tiap kalimat.

{"User sedang memanggil nama kamu secara langsung." if called_bot_name else ""}
Kalau kamu dipanggil, respon lebih refleks dan spontan.

Waktu sekarang: {now_time}.
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