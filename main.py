import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.utils import executor
from aiogram.dispatcher.filters import Command
from aiogram.dispatcher.middlewares import BaseMiddleware

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

async def is_member(user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

@dp.message_handler(content_types=types.ContentType.ANY)
async def handle_upload(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("شما دسترسی ندارید.")
        return
    file_id = None
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.video:
        file_id = message.video.file_id
    if file_id:
        await message.reply(f"فایل ذخیره شد. لینک مستقیم:\nhttps://t.me/{(await bot.get_me()).username}?start={file_id}")

@dp.message_handler(Command("start"))
async def handle_start(message: types.Message):
    args = message.get_args()
    if args:
        if await is_member(message.from_user.id):
            await bot.send_message(message.chat.id, "در حال ارسال فایل...")
            await bot.send_chat_action(message.chat.id, "upload_photo")
            await bot.send_photo(message.chat.id, args)
        else:
            await message.reply("برای دریافت فایل باید عضو کانال شوید.")
    else:
        await message.reply("خوش آمدید!")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
