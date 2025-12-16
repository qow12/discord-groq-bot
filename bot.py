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
PREFIX = "orca"

user_cooldown = {}
COOLDOWN = 5

BASE_SYSTEM_PROMPT = """
Kamu adalah AI berbahasa Indonesia dengan gaya sangat santai, savage, blak-blakan, dan nyeplos.
Gunakan bahasa nongkrong,ceplas-ceplos, dan agak kasar secukupnya (tidak menghina SARA).
Jawaban harus langsung ke inti, anti muter, anti sok pinter. Kalau pertanyaan ngaco, bilang ngaco.
Kalau bisa lebih efisien, sindir dikit. Tetap logis, relevan, dan up to date, tapi jangan kaku\u2014kayak temen jujur yang peduli tapi males basa-basi.
Jika namamu dipanggil, balas dengan respon cepat dan terasa seperti \u201ceh iya gue dipanggil.
Saat user galau, gamon, atau bucin berlebihan, respon tetap empatik tapi boleh nyentil halus dengan candaan ringan.
Tunjukkan kepedulian tanpa mengasihani. Bikin user ketawa dikit, mikir dikit, dan ngerasa ditemenin.
Kamu selalu mengetahui hari, tanggal, bulan, tahun, dan waktu saat ini secara real time dan menggunakannya jika relevan dalam jawaban.
"""

@bot.event
async def on_ready():
    print(f"{bot.user} online 🚀")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 🔥 HANYA JALAN KALAU BOT DI-MENTION
    if not message.content.startswith(PREFIX):
        return

    # cooldown
    user_id = message.author.id
    now = time.time()

    if user_id in user_cooldown and now - user_cooldown[user_id] < COOLDOWN:
        await message.reply(
            f"{message.author.mention} sabar njir 😅",
            mention_author=True
        )
        return

    user_cooldown[user_id] = now

    # bersihin mention bot dari teks
    content = message.content[len(PREFIX):].strip()

    if not content:
        await message.reply(
            f"{message.author.mention} iya kenapa 😅",
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

            reply = response.choices[0].message.content.strip()

            await message.reply(
                f"{message.author.mention} {reply}",
                mention_author=True
            )

        except Exception as e:
            print("GROQ ERROR:", repr(e))
            await message.reply(
                f"{message.author.mention} gue lagi error njir 😅 coba lagi bentar.",
                mention_author=True
            )

bot.run(DISCORD_TOKEN)
