import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from tinydb import TinyDB, Query

# تنظیمات
BOT_TOKEN = "7615458928:AAHYe7qSpmAbI4hkCwUk19_0kONm5XJ0TUM"
ADMIN_ID = 6387942633  # آی‌دی عددی ادمین
CHANNEL_USERNAME = "hottof"  # فقط نام بدون @

# راه‌اندازی
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
db = TinyDB("users.json")
files_db = TinyDB("files.json")
logging.basicConfig(level=logging.INFO)

# کیبورد عضویت
def join_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME}"))
    kb.add(InlineKeyboardButton("بررسی عضویت", callback_data="check_join"))
    return kb

# بررسی عضویت
async def is_member(user_id):
    try:
        member = await bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# پنل ادمین
def admin_panel():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("آمار کاربران", callback_data="stats"),
        InlineKeyboardButton("فایل‌های آپلودشده", callback_data="list_files")
    )
    return kb

# فرمان /start
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    now = datetime.utcnow().isoformat()

    if not db.contains(Query().id == user_id):
        db.insert({"id": user_id, "time": now})

    if not await is_member(user_id):
        await message.answer("لطفاً اول عضو کانال شوید:", reply_markup=join_keyboard())
        return

    if user_id == ADMIN_ID:
        await message.answer("خوش آمدید به پنل مدیریت", reply_markup=admin_panel())
    else:
        await message.answer("لطفاً فایل خود را ارسال کنید:")

# بررسی عضویت
@dp.callback_query_handler(lambda c: c.data == "check_join")
async def check_join(call: types.CallbackQuery):
    if await is_member(call.from_user.id):
        await call.message.edit_text("عضویت تایید شد. حالا فایل خود را ارسال کنید.")
    else:
        await call.answer("هنوز عضو نیستید!", show_alert=True)

# گرفتن فایل از کاربر
@dp.message_handler(content_types=types.ContentType.DOCUMENT)
async def handle_doc(message: types.Message):
    if not await is_member(message.from_user.id):
        await message.answer("لطفاً ابتدا عضو کانال شوید.", reply_markup=join_keyboard())
        return

    file = message.document
    file_id = file.file_id
    file_name = file.file_name

    files_db.insert({
        "file_id": file_id,
        "name": file_name,
        "downloads": 0,
        "uploader": message.from_user.id,
        "time": datetime.utcnow().isoformat()
    })

    bot_username = (await bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={file_id}"
    await message.answer(f"فایل ذخیره شد!\nلینک اشتراک‌گذاری:\n{link}")

# باز کردن فایل از لینک
@dp.message_handler(lambda m: m.text.startswith("/start ") and len(m.text.split()) == 2)
async def get_file_from_link(message: types.Message):
    file_id = message.text.split()[1]

    if not await is_member(message.from_user.id):
        await message.answer("اول عضو کانال شوید:", reply_markup=join_keyboard())
        return

    result = files_db.search(Query().file_id == file_id)
    if result:
        files_db.update({"downloads": result[0]["downloads"] + 1}, Query().file_id == file_id)
        await bot.send_document(message.chat.id, file_id, caption=f"نام فایل: {result[0]['name']}")
    else:
        await message.answer("فایل یافت نشد.")

# لیست فایل‌ها برای ادمین
@dp.callback_query_handler(lambda c: c.data == "list_files")
async def show_files(call: types.CallbackQuery):
    bot_username = (await bot.get_me()).username
    files = files_db.all()

    if not files:
        await call.message.answer("هیچ فایلی آپلود نشده.")
        return

    for f in files:
        link = f"https://t.me/{bot_username}?start={f['file_id']}"
        text = (
            f"نام فایل: {f['name']}\n"
            f"تعداد دانلود: {f['downloads']}\n"
            f"لینک مستقیم:\n{link}"
        )
        await call.message.answer(text)

# آمار کاربران
@dp.callback_query_handler(lambda c: c.data == "stats")
async def show_stats(call: types.CallbackQuery):
    users = db.all()
    now = datetime.utcnow()
    d24 = len([u for u in users if datetime.fromisoformat(u['time']) >= now - timedelta(days=1)])
    d7 = len([u for u in users if datetime.fromisoformat(u['time']) >= now - timedelta(days=7)])
    d30 = len([u for u in users if datetime.fromisoformat(u['time']) >= now - timedelta(days=30)])
    await call.message.answer(
        f"آمار کاربران:\n"
        f"24 ساعت اخیر: {d24}\n"
        f"7 روز اخیر: {d7}\n"
        f"30 روز اخیر: {d30}\n"
        f"کل: {len(users)}"
    )

# اجرای ربات
if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
