import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Լոգերի կարգավորում
logging.basicConfig(level=logging.INFO)

# --- ԿԱՐԵՎՈՐ: ԴԻՐ ՔՈ ՏՈԿԵՆԸ ԱՅՍՏԵՂ ---
API_TOKEN = '8696364106:AAGLxICg4P4yBvREeH-cb5TbyJZWBkq-yho'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Զրույցների պահպանման համար
waiting_users = []  # Մարդիկ, ովքեր սպասում են զրուցակցի
active_chats = {}   # Ակտիվ զրույցներ {user_id: partner_id}

# --- ԿՈՃԱԿՆԵՐ ---
def get_main_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔍 Գտնել զրուցակից"))
    return keyboard

def get_chat_menu():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("👤 Կիսվել կոնտակտով"), KeyboardButton("❌ Ավարտել"))
    return keyboard

# --- ՀՐԱՄԱՆՆԵՐ ---

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.answer(
        "Ողջոյն! Սա անանուն չաթ բոտ է: \nՍեղմիր կոճակը՝ զրուցակից գտնելու համար:",
        reply_markup=get_main_menu()
    )

@dp.message_handler(lambda message: message.text == "🔍 Գտնել զրուցակից" or message.text == "/search")
async def search_partner(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in active_chats:
        await message.answer("Դուք արդեն զրույցի մեջ եք:")
        return

    if user_id in waiting_users:
        await message.answer("Դուք արդեն փնտրում եք զրուցակից...")
        return

    if waiting_users:
        partner_id = waiting_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        
        await bot.send_message(user_id, "🎉 Զրուցակիցը գտնվեց! Կարող եք գրել:", reply_markup=get_chat_menu())
        await bot.send_message(partner_id, "🎉 Զրուցակիցը գտնվեց! Կարող եք գրել:", reply_markup=get_chat_menu())
    else:
        waiting_users.append(user_id)
        await message.answer("⏳ Փնտրում եմ զրուցակից...", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Չեղարկել"))

@dp.message_handler(lambda message: message.text == "❌ Ավարտել" or message.text == "/stop")
async def stop_chat(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        
        del active_chats[user_id]
        del active_chats[partner_id]
        
        await bot.send_message(user_id, "❌ Զրույցն ավարտվեց:", reply_markup=get_main_menu())
        await bot.send_message(partner_id, "❌ Զրուցակիցը դուրս եկավ չաթից:", reply_markup=get_main_menu())
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
        await message.answer("Չեղարկվեց:", reply_markup=get_main_menu())
    else:
        await message.answer("Դուք զրույցի մեջ չեք:", reply_markup=get_main_menu())

@dp.message_handler(lambda message: message.text == "👤 Կիսվել կոնտակտով" or message.text == "/share")
async def share_profile(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        user = message.from_user
        
        if user.username:
            link = f"https://t.me/{user.username}"
            text = f"🌟 Զրուցակիցը կիսվեց իր Telegram-ով. {link}"
        else:
            text = f"🌟 Զրուցակիցը կիսվեց իր պրոֆիլով. [Սեղմիր այստեղ](tg://user?id={user.id})"
        
        await bot.send_message(partner_id, text, parse_mode="Markdown")
        await message.answer("✅ Քո հղումը ուղարկվեց զրուցակցին:")
    else:
        await message.answer("Այս ֆունկցիան աշխատում է միայն զրույցի ժամանակ:")

# --- ՀԱՂՈՐԴԱԳՐՈՒԹՅՈՒՆՆԵՐԻ ՓՈԽԱՆՑՈՒՄ ---
@dp.message_handler(content_types=['text', 'photo', 'video', 'voice', 'sticker'])
async def forward_message(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        # Փոխանցում ենք հաղորդագրությունը
        if message.text:
            await bot.send_message(partner_id, message.text)
        elif message.photo:
            await bot.send_photo(partner_id, message.photo[-1].file_id)
        elif message.video:
            await bot.send_video(partner_id, message.video.file_id)
        elif message.voice:
            await bot.send_voice(partner_id, message.voice.file_id)
        elif message.sticker:
            await bot.send_sticker(partner_id, message.sticker.file_id)
    else:
        # Եթե մարդը պարզապես գրում է առանց չաթի
        if message.text not in ["🔍 Գտնել զրուցակից", "❌ Ավարտել", "❌ Չեղարկել"]:
            await message.answer("Զրուցակից գտնելու համար սեղմիր կոճակը 👇")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
