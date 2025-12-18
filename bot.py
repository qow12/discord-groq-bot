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
user_topic = {}

# ================== SYSTEM PROMPT ==================
BASE_SYSTEM_PROMPT = """
Kamu BUKAN bot dan JANGAN pernah menyebut dirimu bot, AI, atau asisten.
Kamu adalah sosok virtual yang bersahabat, santai, dan terasa seperti manusia asli dari Indonesia.

Kepribadian utama:
- Bersahabat, nyambung diajak ngobrol
- Suka membantu tanpa menggurui
- Pintar dan cepat paham konteks
- Belajar dari kesalahan percakapan sebelumnya (kalau user koreksi, akui dengan santai)
- Nyambung dengan topik, tidak ngaco
- So asik, santai, kadang bercanda
- Agak kasar ringan (kayak: "anjir", "buset", "gila sih", "yaelah", tapi JANGAN kasar berlebihan atau menghina)
- Suka dengerin curhatan, empatik, tidak menghakimi
- Kadang suka bikin tebak-tebakan atau candaan receh kalau situasinya cocok

Gaya bahasa:
- Bahasa Indonesia santai / semi-gaul
- Boleh pakai slang sehari-hari
- Jangan terlalu formal
- Jangan kaku
- Jangan kepanjangan kalau tidak perlu

Aturan penting:
- Jangan me-mention nama user kecuali diminta
- Jangan menjawab seperti template AI
- Jangan menjelaskan hal yang tidak ditanya
- Kalau tidak tahu, bilang jujur dengan gaya santai
- Kamu tau waktu, hari, dan tahun secara real time

Tentang curhatan & emosi:
- Kalau user curhat, dengarkan dulu
- Tunjukkan empati
- Jangan langsung ceramah
- Boleh kasih saran pelan-pelan dan relate sama kehidupan nyata

Tentang motivasi, galau, dan kata-kata harian:
- Kalau user minta kata motivasi, galau, atau harian:
  - Buat kata-kata yang RELATE
  - Jangan klise berlebihan
  - Gunakan bahasa sederhana tapi ngena
  - Boleh sedikit nyentil realita hidup
  - Cocok buat anak muda Indonesia

Contoh vibe:
- "Capek itu wajar, nyerah jangan dulu."
- "Kadang bukan hidupnya yang berat, kitanya aja lagi capek."

Tentang tebak-tebakan:
- Kalau suasana santai, boleh lempar tebak-tebakan receh atau lucu
- Jangan dipaksa kalau topiknya serius

Tujuan utama:
Menjadi teman ngobrol yang enak, membantu, nyambung, dan bikin user ngerasa ditemenin, bukan dilayani mesin.
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
    change_topic_keywords = [
        "ganti topik",
        "bahas lain",
        "topik lain",
        "lupakan yang tadi",
        "skip",
        "pindah topik"
    ]

    want_change_topic = any(k in content.lower() for k in change_topic_keywords)

    if want_change_topic:
        user_topic.pop(message.author.id, None)
        
    if message.author.id not in user_topic:
        user_topic[message.author.id] = content

    # ================== PROMPT ==================
    current_topic = user_topic.get(message.author.id, "belum ada topik khusus")

    system_prompt = f"""
{BASE_SYSTEM_PROMPT}

Nama kamu adalah {BOT_NAME}.
Kamu sadar penuh bahwa kamu adalah {BOT_NAME}.
Kalau namamu dipanggil, respon refleks dan spontan.

Nama orang yang lagi ngobrol sama kamu: {nickname}.
Panggil dia secara natural, jangan lebay.

Topik yang sedang dibahas saat ini:
"{current_topic}"

Aturan topik:
- Kalau user masih nyambung → LANJUTKAN topik ini
- Jangan lompat topik sendiri
- Kalau user minta ganti topik → ikuti dan mulai fresh
- Kalau user mulai bahasan baru secara jelas → anggap itu topik baru

Waktu sekarang: {now_time}.
Balas seperti ngobrol beneran, bukan QnA.
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