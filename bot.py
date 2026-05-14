import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# --- ԱՅՍՏԵՂ ՏԵՂԱԴՐԻՐ ՔՈ TOKEN-Ը ---
# Օրինակ՝ API_TOKEN = '8696364106:AAGLxICg4P4yBvREeH-cb5TbyJZWBkq-yho'
API_TOKEN = 'ՔՈ_TOKEN_Ը_ԱՅՍՏԵՂ'

# Լոգավորում (որ տեսնենք՝ ինչ է կատարվում Render-ի կոնսոլում)
logging.basicConfig(level=logging.INFO)

# Բոտի և դիսպետչերի սկզբնավորում
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Տվյալների պահպանում (այս պահին RAM-ում)
queue = []        # Օգտատերեր, ովքեր սպասում են զույգի
users_chat = {}   # Ով ում հետ է խոսում {user_id: partner_id}

# Ստեղծում ենք կոճակները
def get_keyboard():
    buttons = [
        [KeyboardButton(text="/search"), KeyboardButton(text="/stop")],
        [KeyboardButton(text="Կիսվել կոնտակտով", request_contact=True)]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# /start հրահանգը
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Բարի գալուստ անանուն չաթ։\n\n"
        "🔍 /search - Գտնել զրուցակից\n"
        "🛑 /stop - Ավարտել զրույցը",
        reply_markup=get_keyboard()
    )

# Զրուցակից փնտրելու հրահանգը
@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in users_chat:
        await message.answer("Դուք արդեն չաթի մեջ եք։")
        return

    if user_id in queue:
        await message.answer("Դուք արդեն հերթում եք։ Սպասեք...")
        return

    if queue:
        partner_id = queue.pop(0)
        users_chat[user_id] = partner_id
        users_chat[partner_id] = user_id
        
        await bot.send_message(user_id, "Զրուցակիցը գտնվեց։ Կարող եք գրել...")
        await bot.send_message(partner_id, "Զրուցակիցը գտնվեց։ Կարող եք գրել...")
    else:
        queue.append(user_id)
        await message.answer("Փնտրում եմ զրուցակից... Խնդրում եմ սպասել։")

# Զրույցը դադարեցնելու հրահանգը
@dp.message(Command("stop"))
async def cmd_stop(message: types.Message):
    user_id = message.from_user.id
    partner_id = users_chat.get(user_id)

    if partner_id:
        del users_chat[user_id]
        del users_chat[partner_id]
        await bot.send_message(user_id, "Չաթն ավարտվեց։")
        await bot.send_message(partner_id, "Զրուցակիցն ավարտեց չաթը։")
    elif user_id in queue:
        queue.remove(user_id)
        await message.answer("Փնտրումը չեղարկվեց։")
    else:
        await message.answer("Դուք հիմա ոչ մեկի հետ չեք խոսում։")

# Հաղորդագրությունների փոխանցման տրամաբանությունը
@dp.message()
async def forward_message(message: types.Message):
    user_id = message.from_user.id
    partner_id = users_chat.get(user_id)

    if not partner_id:
        if message.text not in ["/search", "/start", "/stop"]:
            await message.answer("Զրույց սկսելու համար սեղմեք /search")
        return

    try:
        if message.text:
            await bot.send_message(partner_id, message.text)
        elif message.photo:
            await bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
        elif message.video:
            await bot.send_video(partner_id, message.video.file_id, caption=message.caption)
        elif message.voice:
            await bot.send_voice(partner_id, message.voice.file_id)
        elif message.contact:
            await bot.send_contact(partner_id, phone_number=message.contact.phone_number, first_name=message.contact.first_name)
        elif message.sticker:
            await bot.send_sticker(partner_id, message.sticker.file_id)
        elif message.animation:
            await bot.send_animation(partner_id, message.animation.file_id)
            
    except Exception as e:
        logging.error(f"Error: {e}")
        await message.answer("Հաղորդագրությունը չհասավ զրուցակցին։")

# Բոտի գործարկում
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
