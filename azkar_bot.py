
import json
import random
import logging
import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from telegram import Update
from telegram.error import Forbidden, BadRequest
from telegram.ext import Application, CommandHandler, ContextTypes

# ================== الإعدادات ==================
import os 
TOKEN = os.getenv("BOT_TOKEN") # توكن البوت من @BotFather
TZ = ZoneInfo("Africa/Algiers") # غيّر التوقيت حسب بلدك
DHIKR_EVERY_MIN = 60 # ذكر عشوائي كل كم دقيقة
AYAH_EVERY_MIN = 180 # آية عشوائية كل كم دقيقة
MORNING_TIME = dt.time(6, 0, tzinfo=TZ) # أذكار الصباح
EVENING_TIME = dt.time(17, 30, tzinfo=TZ) # أذكار المساء
CHATS_FILE = Path("chats.json")
CITY = "Algiers" # المدينة (بالإنجليزية): Algiers, Oran, Constantine, Annaba...
COUNTRY = "Algeria"
METHOD = 19 # طريقة الحساب: 19 = وزارة الشؤون الدينية الجزائرية
# ===============================================

logging.basicConfig(level=logging.INFO)

ADHKAR = [
"سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ",
"لَا إِلَٰهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَىٰ كُلِّ شَيْءٍ قَدِيرٌ",
"أَسْتَغْفِرُ اللَّهَ الْعَظِيمَ وَأَتُوبُ إِلَيْهِ",
"لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ",
"اللَّهُمَّ صَلِّ وَسَلِّمْ عَلَىٰ نَبِيِّنَا مُحَمَّدٍ ﷺ",
"حَسْبِيَ اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ عَلَيْهِ تَوَكَّلْتُ وَهُوَ رَبُّ الْعَرْشِ الْعَظِيمِ",
"سُبْحَانَ اللَّهِ، وَالْحَمْدُ لِلَّهِ، وَلَا إِلَٰهَ إِلَّا اللَّهُ، وَاللَّهُ أَكْبَرُ",
"اللَّهُمَّ إِنَّكَ عَفُوٌّ تُحِبُّ الْعَفْوَ فَاعْفُ عَنِّي",
"رَبِّ اغْفِرْ لِي وَتُبْ عَلَيَّ إِنَّكَ أَنتَ التَّوَّابُ الرَّحِيمُ",
"يَا حَيُّ يَا قَيُّومُ بِرَحْمَتِكَ أَسْتَغِيثُ",
]

MORNING_TEXT = (
"🌅 أذكار الصباح\n\n"
"أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ، "
"لَا إِلَٰهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ.\n\n"
"اللَّهُمَّ بِكَ أَصْبَحْنَا، وَبِكَ أَمْسَيْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ النُّشُورُ.\n\n"
"📖 لا تنسَ قراءة آية الكرسي والمعوذات (3 مرات)."
)

EVENING_TEXT = (
"🌇 أذكار المساء\n\n"
"أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ، "
"لَا إِلَٰهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ.\n\n"
"اللَّهُمَّ بِكَ أَمْسَيْنَا، وَبِكَ أَصْبَحْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ الْمَصِيرُ.\n\n"
"📖 لا تنسَ قراءة آية الكرسي والمعوذات (3 مرات)."
)


# ---------- تخزين المجموعات ----------
def load_chats() -> set:
if CHATS_FILE.exists():
try:
return set(json.loads(CHATS_FILE.read_text()))
except Exception:
return set()
return set()


def save_chats(chats: set):
CHATS_FILE.write_text(json.dumps(list(chats)))


CHATS = load_chats()


# ---------- جلب آية عشوائية ----------
async def get_random_ayah() -> str:
n = random.randint(1, 6236)
url = f"https://api.alquran.cloud/v1/ayah/{n}/quran-uthmani"
async with httpx.AsyncClient(timeout=15) as client:
r = await client.get(url)
r.raise_for_status()
d = r.json()["data"]
return f"📖 ﴿{d['text']}﴾\n\n[سورة {d['surah']['name'].replace('سُورَةُ ', '')} - الآية {d['numberInSurah']}]"


# ---------- الإرسال لكل المجموعات ----------
async def broadcast(context: ContextTypes.DEFAULT_TYPE, text: str):
for chat_id in list(CHATS):
try:
await context.bot.send_message(chat_id, text)
except (Forbidden, BadRequest):
CHATS.discard(chat_id) # البوت طُرد أو المجموعة محذوفة
save_chats(CHATS)
except Exception as e:
logging.warning("send failed %s: %s", chat_id, e)


async def job_dhikr(context: ContextTypes.DEFAULT_TYPE):
await broadcast(context, "🤍 " + random.choice(ADHKAR))


async def job_ayah(context: ContextTypes.DEFAULT_TYPE):
try:
await broadcast(context, await get_random_ayah())
except Exception as e:
logging.warning("ayah failed: %s", e)

卂爪丨几乇:
async def job_morning(context: ContextTypes.DEFAULT_TYPE):
await broadcast(context, MORNING_TEXT)


async def job_evening(context: ContextTypes.DEFAULT_TYPE):
await broadcast(context, EVENING_TEXT)


# ---------- مواقيت الصلاة ----------
PRAYERS = {
"Fajr": "الفجر",
"Dhuhr": "الظهر",
"Asr": "العصر",
"Maghrib": "المغرب",
"Isha": "العشاء",
}


async def get_prayer_times(city: str = CITY) -> dict:
today = dt.datetime.now(TZ).strftime("%d-%m-%Y")
url = f"https://api.aladhan.com/v1/timingsByCity/{today}"
params = {"city": city, "country": COUNTRY, "method": METHOD}
async with httpx.AsyncClient(timeout=15) as client:
r = await client.get(url, params=params)
r.raise_for_status()
t = r.json()["data"]["timings"]
return {k: t[k][:5] for k in ("Fajr", "Sunrise", "Dhuhr", "Asr", "Maghrib", "Isha")}


async def job_prayer(context: ContextTypes.DEFAULT_TYPE):
name = PRAYERS[context.job.data]
await broadcast(
context,
f"🕌 حان الآن موعد صلاة {name} حسب توقيت {CITY}\n\n🤍 حيَّ على الصلاة، حيَّ على الفلاح",
)


async def schedule_prayers(context: ContextTypes.DEFAULT_TYPE):
"""تجلب مواقيت اليوم وتجدول إشعار كل صلاة."""
try:
times = await get_prayer_times()
except Exception as e:
logging.warning("prayer times failed: %s", e)
context.job_queue.run_once(schedule_prayers, when=300) # إعادة المحاولة بعد 5 دقائق
return
now = dt.datetime.now(TZ)
for key in PRAYERS:
for old in context.job_queue.get_jobs_by_name(f"prayer_{key}"):
old.schedule_removal()
h, m = map(int, times[key].split(":"))
when = now.replace(hour=h, minute=m, second=0, microsecond=0)
if when > now:
context.job_queue.run_once(job_prayer, when=when, data=key, name=f"prayer_{key}")


# ---------- الأوامر ----------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
chat = update.effective_chat
if chat.type == "private":
return True
member = await chat.get_member(update.effective_user.id)
return member.status in ("administrator", "creator")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text(
"السلام عليكم 🌙\n"
"/start_azkar - تفعيل الإرسال التلقائي (للمشرفين)\n"
"/stop_azkar - إيقاف الإرسال التلقائي (للمشرفين)\n"
"/dhikr - ذكر الآن\n"
"/ayah - آية الآن\n"
"/prayer - مواقيت الصلاة (مثال: /prayer Oran)"
)


async def cmd_prayer(update: Update, context: ContextTypes.DEFAULT_TYPE):
city = " ".join(context.args) if context.args else CITY
try:
t = await get_prayer_times(city)
except Exception:
return await update.message.reply_text("تعذّر جلب المواقيت، تأكد من اسم المدينة (بالإنجليزية).")
await update.message.reply_text(
f"🕌 مواقيت الصلاة - {city}\n\n"
f"الفجر: {t['Fajr']}\n"
f"الشروق: {t['Sunrise']}\n"
f"الظهر: {t['Dhuhr']}\n"
f"العصر: {t['Asr']}\n"
f"المغرب: {t['Maghrib']}\n"
f"العشاء: {t['Isha']}"
)


async def cmd_start_azkar(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not await is_admin(update, context):
return await update.message.reply_text("هذا الأمر للمشرفين فقط.")
CHATS.add(update.effective_chat.id)
save_chats(CHATS)
await update.message.reply_text("✅ تم التفعيل، سأرسل الأذكار والآيات تلقائياً. تقبّل الله منا ومنكم.")


async def cmd_stop_azkar(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not await is_admin(update, context):
return await update.message.reply_text("هذا الأمر للمشرفين فقط.")
CHATS.discard(update.effective_chat.id)
save_chats(CHATS)
await update.message.reply_text("⏹ تم إيقاف الإرسال التلقائي.")


async def cmd_dhikr(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text("🤍 " + random.choice(ADHKAR))

卂爪丨几乇:
async def cmd_ayah(update: Update, context: ContextTypes.DEFAULT_TYPE):
try:
await update.message.reply_text(await get_random_ayah())
except Exception:
await update.message.reply_text("تعذّر جلب الآية الآن، حاول لاحقاً.")


def main():
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", cmd_start))
app.add_handler(CommandHandler("start_azkar", cmd_start_azkar))
app.add_handler(CommandHandler("stop_azkar", cmd_stop_azkar))
app.add_handler(CommandHandler("dhikr", cmd_dhikr))
app.add_handler(CommandHandler("ayah", cmd_ayah))
app.add_handler(CommandHandler("prayer", cmd_prayer))

jq = app.job_queue
jq.run_repeating(job_dhikr, interval=DHIKR_EVERY_MIN * 60, first=60)
jq.run_repeating(job_ayah, interval=AYAH_EVERY_MIN * 60, first=120)
jq.run_daily(job_morning, time=MORNING_TIME)
jq.run_daily(job_evening, time=EVENING_TIME)
jq.run_once(schedule_prayers, when=5) # عند تشغيل البوت
jq.run_daily(schedule_prayers, time=dt.time(0, 5, tzinfo=TZ)) # تجديد المواقيت كل يوم

app.run_polling()


if name == "main":
main()