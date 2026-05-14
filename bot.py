import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Լոգավորում
logging.basicConfig(level=logging.INFO)

API_TOKEN = '8696364106:AAG6UMdDpJ_r3m2j0JyTYf_dp4X6UMfIyw4'
ADMIN_ID = 8375974477  # Այստեղ գրիր քո ID-ն (առանց չակերտների)

storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)

# Տվյալների պահպանում
user_data = {}  # {user_id: 'male'/'female'}
waiting_users = []  # Ընդհանուր հերթ բոլորի համար
active_chats = {}   # {user_id: partner_id}

class Registration(StatesGroup):
    choosing_gender = State()

# --- ԿՈՃԱԿՆԵՐ ---
def get_gender_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("👦 Տղա"), KeyboardButton("👧 Աղջիկ"))
    return kb

def get_main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔍 Գտնել զրուցակից"))
    return kb

def get_chat_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("👤 Կիսվել կոնտակտով"), KeyboardButton("❌ Ավարտել"))
    return kb

# --- ՀՐԱՄԱՆՆԵՐ ---

@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.answer("Ողջոյն! Նախքան սկսելը, նշիր քո սեռը.", reply_markup=get_gender_kb())
        await Registration.choosing_gender.set()
    else:
        await message.answer("Բարի գալուստ հետ! Պատրա՞ստ ես շփման:", reply_markup=get_main_menu())

@dp.message_handler(commands=['stats'])
async def cmd_stats(message: types.Message):
    # Ստուգում ենք՝ արդյոք գրողը դու ես
    if message.from_user.id == ADMIN_ID:
        total = len(user_data)
        males = list(user_data.values()).count('male')
        females = list(user_data.values()).count('female')
        in_chat = len(active_chats) // 2
        waiting = len(waiting_users)
        
        stats_text = (
            f"📊 **Բոտի վիճակագրությունը**\n\n"
            f"👤 Օգտատերեր: {total}\n"
            f"👦 Տղաներ: {males}\n"
            f"👧 Աղջիկներ: {females}\n"
            f"💬 Ակտիվ զրույցներ: {in_chat}\n"
            f"⏳ Հերթի մեջ են: {waiting}"
        )
        await message.answer(stats_text, parse_mode="Markdown")
    else:
        # Եթե ուրիշ մարդ գրի, բոտը կպատասխանի սա
        await message.answer("Ներողություն, այս հրամանը հասանելի չէ ձեզ:")
@dp.message_handler(state=Registration.choosing_gender)
async def process_gender(message: types.Message, state: FSMContext):
    if message.text in ["👦 Տղա", "👧 Աղջիկ"]:
        gender = 'male' if "Տղա" in message.text else 'female'
        user_data[message.from_user.id] = gender
        await state.finish()
        await message.answer(f"Գրանցվեց: Դուք նշեցիք {message.text}: ✨", reply_markup=get_main_menu())
    else:
        await message.answer("Խնդրում եմ ընտրել կոճակներից մեկը:")

@dp.message_handler(lambda message: message.text in ["🔍 Գտնել զրուցակից", "/search"])
async def start_search(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in active_chats:
        await message.answer("Դուք արդեն զրույցի մեջ եք:")
        return

    if user_id in waiting_users:
        await message.answer("⏳ Դուք արդեն փնտրում եք զրուցակից...")
        return

    if waiting_users:
        # Միացնում ենք հերթի առաջին մարդուն՝ անկախ սեռից
        partner_id = waiting_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id
        
        await bot.send_message(user_id, "🎉 Զրուցակից գտնվեց! Կարող եք գրել:", reply_markup=get_chat_menu())
        await bot.send_message(partner_id, "🎉 Զրուցակից գտնվեց! Կարող եք գրել:", reply_markup=get_chat_menu())
    else:
        waiting_users.append(user_id)
        await message.answer("⏳ Փնտրում եմ զրուցակից...", 
                             reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add("❌ Չեղարկել"))

@dp.message_handler(lambda message: message.text in ["❌ Ավարտել", "/stop", "❌ Չեղարկել"])
async def stop_everything(message: types.Message):
    user_id = message.from_user.id
    
    # Եթե ակտիվ չաթում է
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await bot.send_message(user_id, "Զրույցն ավարտվեց:", reply_markup=get_main_menu())
        await bot.send_message(partner_id, "Զրուցակիցը դուրս եկավ չաթից:", reply_markup=get_main_menu())
    
    # Եթե հերթի մեջ է
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
        await message.answer("Փնտրումը չեղարկվեց:", reply_markup=get_main_menu())
    else:
        await message.answer("Դուք ակտիվ զրույց կամ հարցում չունեք:", reply_markup=get_main_menu())

@dp.message_handler(lambda message: message.text == "👤 Կիսվել կոնտակտով")
async def share_link(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        user = message.from_user
        link = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user_id}"
        
        await bot.send_message(partner_id, f"🌟 Զրուցակիցը կիսվեց իր կոնտակտով. {link}")
        await message.answer("✅ Քո հղումը ուղարկվեց:")

# Բոլոր տեսակի հաղորդագրությունների փոխանցում
@dp.message_handler(content_types=types.ContentTypes.ANY)
async def message_relay(message: types.Message):
    user_id = message.from_user.id
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        try:
            # Պատճենում ենք հաղորդագրությունը (տեքստ, նկար, ձայն և այլն)
            await message.copy_to(partner_id)
        except Exception:
            await message.answer("⚠️ Չհաջողվեց ուղարկել հաղորդագրությունը:")
    else:
        if message.text not in ["🔍 Գտնել զրուցակից", "❌ Չեղարկել"]:
            await message.answer("Զրույց սկսելու համար սեղմիր կոճակը 👇")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
