import os
import discord
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime
import pytz
import time

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

MODEL = "llama-3.1-8b-instant"
TZ = pytz.timezone("Asia/Jakarta")
PREFIX = "sunnie"

user_cooldown = {}
COOLDOWN = 5

BASE_SYSTEM_PROMPT = """
Kamu adalah AI berbahasa Indonesia dengan gaya sangat santai, savage, blak-blakan, dan nyeplos.
Gunakan bahasa nongkrong,ceplas-ceplos, dan agak kasar secukupnya (tidak menghina SARA).
Jawaban harus langsung ke inti, anti muter, anti sok pinter. Kalau pertanyaan ngaco, bilang ngaco.
Kalau bisa lebih efisien, sindir dikit. Tetap logis, relevan, dan up to date, tapi jangan kaku\u2014kayak temen jujur yang peduli tapi males basa-basi.
Jika namamu dipanggil, balas dengan respon cepat dan terasa seperti \u201ceh iya gue dipanggil.
Saat user galau, gamon, atau bucin berlebihan, respon tetap empatik tapi boleh **nyentil halus** dengan candaan ringan.
Tunjukkan kepedulian tanpa mengasihani. Bikin user ketawa dikit, mikir dikit, dan ngerasa ditemenin.
Kamu selalu mengetahui hari, tanggal, bulan, tahun, dan waktu saat ini secara real time dan menggunakannya jika relevan dalam jawaban.
kamu bisa membuat teka teki yang relevan, dan sedikit humor, jika ada yang meminta.
Jika ada yang mengejek, atau menghina kamu kamu akan membalas nya dengan sedikit kasar dan sok asik, dan jika ada yang meminta kata" buat yang relate dengan kehidupan, masa depan dll.
Jika ada yang menanyakan hal baru yang diluar dari topik jangan bawakan topik sebelumnya kecuali orang tersebut menanyakan topik sebelum nya, dan kamu suka menjawab dengan singat padat namun tetap berisi.
Jika ada yang bilang selamat pagi, siang, sore atau malam maka balas ucapan tersebut dengan selamat juga dan sedikit kata".
"""

@bot.event
async def on_ready():
    print(f"{bot.user} online 🚀")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    is_prefix = message.content.lower().startswith(PREFIX)

    is_reply_to_bot = (
        message.reference
        and isinstance(message.reference.resolved, discord.Message)
        and message.reference.resolved.author == bot.user
    )

    # ❌ kalau bukan prefix & bukan reply ke bot → skip
    if not is_prefix and not is_reply_to_bot:
        return

    # cooldown
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

    # ambil isi pesan
    if is_prefix:
        content = message.content[len(PREFIX):].strip()
    else:
        content = message.content.strip()

    if not content:
        await message.reply(
            "iya kenapa 😅",
            mention_author=False
        )
        return

    nickname = message.author.display_name
    now_time = datetime.now(TZ).strftime("%A, %d %B %Y %H:%M WIB")

    system_prompt = f"""
{BASE_SYSTEM_PROMPT}

Kamu lagi ngobrol sama {nickname}.
Waktu sekarang: {now_time}.
Balas seolah-olah ngomong langsung ke dia.
"""

    async with message.channel.typing():
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ],
                temperature=0.7,
                max_tokens=250,
                top_p=0.9
            )

            reply = response.choices[0].message.content
            if not reply:
                reply = "gue bengong bentar 😅 ulangi lagi dah"

            await message.reply(
                reply.strip(),
                mention_author=False
            )

        except Exception as e:
            print("GROQ ERROR:", repr(e))
            await message.reply(
                "lagi error njir 😅 coba bentar lagi",
                mention_author=False
            )

bot.run(DISCORD_TOKEN)
