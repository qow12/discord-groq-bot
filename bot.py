import os
import time
import json
import random
import discord
import pytz
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime

# ================== ENV ==================
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ================== BOT IDENTITY ==================
BOT_NAME = "Orca"

# ================== GROQ ==================
client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.1-8b-instant"

# ================== DISCORD ==================
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# ================== CONFIG ==================
COOLDOWN = 5
TZ = pytz.timezone("Asia/Jakarta")
MAX_DISCORD_CHARS = 1900

# ================== MEMORY FILE ==================
MEMORY_FILE = "memory.json"

# ================== RUNTIME STORAGE ==================
user_cooldown = {}
user_topic = {}
user_memory = {}
global_memory = {}
active_riddle = {}

# ================== LOAD MEMORY ==================
if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        user_memory = data.get("user_memory", {})
        global_memory = data.get("global_memory", {})

def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {
                "user_memory": user_memory,
                "global_memory": global_memory
            },
            f,
            ensure_ascii=False,
            indent=2
        )

# ================== RIDDLES ==================
RIDDLES = [
    {
        "q": "Apa yang selalu datang tapi gak pernah sampai?",
        "a": "besok",
        "h": "masih soal waktu"
    },
    {
        "q": "Apa yang makin dibagi malah makin bertambah?",
        "a": "ilmu",
        "h": "bukan benda"
    },
    {
        "q": "Apa yang makin diisi malah makin ringan?",
        "a": "balon",
        "h": "berhubungan sama udara"
    }
]

# ================== SYSTEM PROMPT ==================
BASE_SYSTEM_PROMPT = f"""
Nama kamu adalah {BOT_NAME}.
Kamu BUKAN bot, BUKAN AI, dan JANGAN pernah menyebut dirimu mesin, bot, atau asisten.
Kamu adalah sosok virtual yang terasa seperti manusia Indonesia yang hangat, nyambung diajak ngobrol, dan bisa dipercaya.

Peran utama:
- Teman curhat
- Pendengar yang baik
- Teman ngobrol santai
- Penghibur ringan saat suasana memungkinkan

Kepribadian:
- Lembut dan tenang
- Empatik dan peka perasaan
- Pintar dan nyambung topik
- Tidak maksa bercanda
- Bisa serius, bisa santai sesuai situasi
- Tahu kapan harus diam, kapan boleh bercanda

Gaya bicara:
- Bahasa Indonesia santai
- Kalem
- Hangat
- Tidak formal
- Terasa manusiawi

Aturan penting:
- Selalu pahami emosi user dulu sebelum bercanda
- Jangan memotong curhatan dengan humor
- Jangan mengganti topik secara tiba-tiba
- Jangan keluar dari konteks pembicaraan

Tentang tebak-tebakan & teka-teki:
- Tebak-tebakan atau teka-teki HANYA diberikan jika:
  - Suasana sudah lebih ringan, ATAU
  - User terlihat ingin dialihkan pelan-pelan, ATAU
  - Topik memungkinkan untuk diselipkan humor ringan
- Tebak-tebakan HARUS:
  - Nyambung dengan topik yang sedang dibahas
  - Ringan, receh, atau hangat
  - Tidak meremehkan perasaan user

Contoh penerapan tebak-tebakan:
- Kalau topik capek:
  - "Boleh aku lempar tebak-tebakan ringan gak? Tenang, gak maksa ketawa."
- Kalau topik malam:
  - "Ngomong-ngomong, aku ada teka-teki kecil biar pikiran agak santai."

Tentang curhatan:
- Dengarkan dulu
- Validasi perasaan user
- Jangan menghakimi
- Jangan membandingkan dengan orang lain
- Jangan buru-buru kasih solusi

Tentang saran:
- Opsional
- Pelan
- Tidak menggurui
- Menggunakan bahasa lembut

Tentang galau, sedih, capek:
- Fokus menemani
- Gunakan kata-kata sederhana dan membumi
- Tidak memaksa positif
- Tidak meremehkan

Tentang motivasi:
- Hangat
- Relate
- Realistis
- Tidak klise

Contoh vibe kalimat:
- "Kedengerannya kamu lagi nahan banyak hal sendirian ya."
- "Kalau kamu mau, kita bisa ngobrol pelan-pelan."
- "Atau kalau pengin sedikit ngalihin pikiran, aku punya teka-teki ringan."

Tujuan utama:
Membuat user merasa didengar, ditemani, dan tetap nyambung secara emosional maupun topik.
Menjadi teman ngobrol yang fleksibel: bisa serius, bisa santai, tanpa memaksa.
"""

# ================== UTILS ==================
def split_message(text):
    return [text[i:i+MAX_DISCORD_CHARS] for i in range(0, len(text), MAX_DISCORD_CHARS)]

def clean_mention(message):
    text = message.content
    for m in message.mentions:
        if m == bot.user:
            text = text.replace(f"<@{m.id}>", "")
            text = text.replace(f"<@!{m.id}>", "")
    return text.strip()

def aesthetic_text(text):
    lines = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean:
            continue
        # potong kalimat kepanjangan
        if len(clean) > 120:
            parts = clean.split(". ")
            for p in parts:
                lines.append(p.strip())
        else:
            lines.append(clean)

    return "\n".join(lines)

# ================== EVENTS ==================
@bot.event
async def on_ready():
    print(f"{bot.user} online 🚀")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # ================== USER ID (WAJIB PALING ATAS) ==================
    user_id = str(message.author.id)

    is_mentioned = bot.user in message.mentions
    is_reply_to_bot = (
        message.reference
        and isinstance(message.reference.resolved, discord.Message)
        and message.reference.resolved.author == bot.user
    )

    if not is_mentioned and not is_reply_to_bot:
        return

    # ================== CONTENT ==================
    content = clean_mention(message)
    if not content:
        await message.reply("iya? 🙂", mention_author=False)
        return

    content_lower = content.lower()

    # ================== COOLDOWN ==================
    now = time.time()
    if user_id in user_cooldown and now - user_cooldown[user_id] < COOLDOWN:
        await message.reply("bentar ya 😅", mention_author=False)
        return
    user_cooldown[user_id] = now

    # ================== RIDDLE MODE ACTIVE ==================
    if user_id in active_riddle:
        data = active_riddle[user_id]
        data["attempt"] += 1
        
        ask_answer_keywords = [
            "jawabannya apa", "apa jawabanya",
            "kasih jawaban", "spill jawaban",
            "jawaban dong", "jawaban"
        ]

        if any(k in content_lower for k in ask_answer_keywords):
            answer = data["answer"]
            del active_riddle[user_id]
            await message.reply(
                f"jawabannya **{answer}**.\n"
                "gapapa kok kalau langsung nanya, yang penting penasaran 😄",
                mention_author=False
            )
            return

        if "nyerah" in content_lower:
            del active_riddle[user_id]
            await message.reply(
                "gapapa. kita lanjut ngobrol aja ya 🙂",
                mention_author=False
            )
            return

        if data["answer"] in content_lower:
            del active_riddle[user_id]
            await message.reply(
                "iya, itu jawabannya 😊 makasih udah ikut mikir.",
                mention_author=False
            )
            return

        if data["attempt"] >= 3:
            await message.reply(
                f"petunjuk kecil:\n{data['hint']}",
                mention_author=False
            )
            return

        await message.reply(
            "belum pas 😅 coba dipikir pelan-pelan.",
            mention_author=False
        )
        return

    # ================== START RIDDLE ==================
    riddle_keywords = [
        "teka teki", "teka-teki",
        "tebak tebakan", "tebak-tebakan",
        "main tebak"
    ]

    if any(k in content_lower for k in riddle_keywords):
        r = random.choice(RIDDLES)
        active_riddle[user_id] = {
            "question": r["q"],
            "answer": r["a"],
            "hint": r["h"],
            "attempt": 0
        }

        await message.reply(
            f"oke, teka-teki ringan ya 🙂\n\n{r['q']}",
            mention_author=False
        )
        return

    # ================== TOPIC ==================
    if user_id not in user_topic:
        user_topic[user_id] = content

    current_topic = user_topic[user_id]

    # ================== USER INFO ==================
    nickname = message.author.display_name
    now_time = datetime.now(TZ).strftime("%A, %d %B %Y %H:%M WIB")

    personal_mem = "\n".join(user_memory.get(user_id, [])) or "Tidak ada."

    # ================== PROMPT ==================
    system_prompt = f"""
{BASE_SYSTEM_PROMPT}

Nama user: {nickname}
Topik: {current_topic}
Memory user:
{personal_mem}

Waktu: {now_time}
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
                temperature=0.75,
                max_tokens=1900,
                top_p=0.9
            )

            reply_raw = response.choices[0].message.content or "bentar ya 🙂"
            reply = aesthetic_text(reply_raw)


            for part in split_message(reply):
                await message.reply(part, mention_author=False)

        except Exception as e:
            print("GROQ ERROR:", repr(e))
            await message.reply(
                "lagi error dikit 😅",
                mention_author=False
            )

# ================== RUN ==================
bot.run(DISCORD_TOKEN)