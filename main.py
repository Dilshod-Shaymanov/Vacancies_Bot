from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, \
    InlineKeyboardButton

from config import BOT_TOKEN, CHANNEL_ID, ADMINS

storage = MemoryStorage()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot, storage=storage)

class AdminMessageState(StatesGroup):
    text = State()


register = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🪪 Ro'yxatdan O'tish")
        ]
    ], resize_keyboard=True
)

phone_number = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text='📞 Telefon raqamni yuborish', request_contact=True)
        ]
    ], resize_keyboard=True
)

accept = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Tasdiqlayman', callback_data='accept'),
            InlineKeyboardButton(text="🔄 Qayta to'ldiraman", callback_data='restart')
        ]
    ]
)

yes_no = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Ha', callback_data='yes'),
            InlineKeyboardButton(text="❌ Yo'q", callback_data='no')
        ]
    ]
)


@dp.message_handler(commands='start')
async def start_command(message: types.Message, state: FSMContext):
    with open('users.txt', 'r') as reader:
        users = reader.readlines()
        user_ids = []
        for user_line in users:
            cleaned_line = user_line.strip().split('_')
            if len(cleaned_line) > 0:
                try:
                    user_id = int(cleaned_line[0])
                    user_ids.append(user_id)
                except:
                    continue

    if message.chat.id in user_ids:
        await message.answer("Siz ro'yxatdan o'tgansiz! 😊")
    else:
        await message.answer(
            text=f"Assalomu alaykum {message.from_user.first_name},\nBotimizga xush kelibsiz!\n \nRo'yxatdan o'tish tugmasini bosing 👇",
            reply_markup=register)
        await state.set_state('register')


@dp.message_handler(state='register', text="🪪 Ro'yxatdan O'tish")
async def register_handler(message: types.Message, state: FSMContext):
    await message.answer(text="✍️ Ism, Familiyangizni kiriting:", reply_markup=ReplyKeyboardRemove())
    await state.set_state('full_name')


@dp.message_handler(state='full_name')
async def full_name_handler(message: types.Message, state: FSMContext):
    if message.text.replace(' ', '').isalpha():
        await state.update_data({
            'full_name': message.text
        })
        await message.answer(text=f"🕑 Yosh:\n\nYoshingizni kiriting:\nMasalan, 19")
        await state.set_state('age')
    else:
        await message.answer(text="❌ Iltimos, Faqat so'zlardan foydalaning!\nMasalan: Ism Familya")


@dp.message_handler(state='age')
async def age_handler(message: types.Message, state: FSMContext):
    try:
        age = int(message.text)
        if 10 <= age <= 100:
            await state.update_data({
                'age': age
            })
            await message.answer(text="📞 Aloqa:\n\nBog`lanish uchun Telefon raqamingizni yuboring:",
                                 reply_markup=phone_number)
            await state.set_state('phone_number')
        else:
            await message.answer(text="❌ Yosh 10 dan 100 gacha bo'lishi kerak. Iltimos qayta kiriting:")
    except ValueError:
        await message.answer(text='❌ Iltimos yoshingizni faqat raqamda kiriting!')


from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


@dp.message_handler(state='phone_number', content_types=types.ContentType.ANY)
async def phone_number_handler(message: types.Message, state: FSMContext):
    if message.content_type == types.ContentType.CONTACT:
        phone_number = message.contact.phone_number
        if not phone_number.startswith('+'):
            phone_number = f"+{phone_number}"
        await state.update_data({
            'phone_number': phone_number
        })
        await message.answer(text="📁 Resume PDF shaklida yuboring!", reply_markup=ReplyKeyboardRemove())
        await state.set_state('resume')
    else:
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("📱 Telefon raqamni yuborish", request_contact=True)
        )
        await message.answer(
            text="❌ Iltimos, Telefon raqamingizni faqat pastdagi tugma orqali yuboring!",
            reply_markup=keyboard
        )


@dp.message_handler(state='resume', content_types=types.ContentType.DOCUMENT)
async def resume_handler(message: types.Message, state: FSMContext):
    if not message.document:
        await message.answer(text="❌ Iltimos, faqat PDF formatdagi fayl yuboring!")
        return

    if message.document.mime_type.startswith('application/pdf'):
        await state.update_data({
            'resume': message.document.file_id
        })
        await message.answer(text="📍 Siz ayni damda Toshkentdamisiz?", reply_markup=yes_no)
        await state.set_state('tashkent')
    else:
        await message.answer(text="❌ Iltimos, faqat PDF formatdagi fayl yuboring!")


@dp.callback_query_handler(state='tashkent')
async def tashkent_handler(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    if call.data == 'yes':
        await state.update_data({
            'tashkent': True
        })
        await call.message.answer(text="💼 Kasbi:\v\nKasbingizni kiriting:\nMasalan, Dizayner:")
        await state.set_state('job')
    else:
        await call.message.answer(
            text="❌ Kechirasiz, Bizga toshkentda bo'lishingiz zarur.\nQayta boshlash uchun /start ni bosing.")
        await state.finish()


@dp.message_handler(state='job')
async def job_handler(message: types.Message, state: FSMContext):
    if message.text.replace(' ', '').isalpha():
        await state.update_data({
            'job': message.text
        })
        await message.answer(
            text="🕰 Murojaat qilish vaqti:\n\nQaysi vaqtda murojaat qilish mumkin:\nMasalan, 9:00 - 18:00")
        await state.set_state('time')
    else:
        await message.answer(text="❌ Iltimos, Faqat so'zda kiriting!")


@dp.message_handler(state='time')
async def time_handler(message: types.Message, state: FSMContext):
    await state.update_data({
        'time': message.text
    })
    await message.answer(text="🔗 Portfolio:\n\nLink yuboring (GitHub, Telegram, Instagram):")
    await state.set_state('portfolio')


@dp.message_handler(state='portfolio')
async def portfolio_handler(message: types.Message, state: FSMContext):
    await state.update_data({
        'portfolio': message.text
    })
    data = await state.get_data()
    user_data = f"""
📌 MA'LUMOTLARINGIZ:

👨‍💼 Xodim: {data['full_name']}
🎂 Yosh: {data['age']}
📞 Aloqa: {data['phone_number']}
🇺🇿 Telegram: @{message.from_user.username}
📍 Hozir Toshkentdamisiz: {'Ha' if data.get('tashkent', False) else "Yo'q"}
💼 Kasbi: {data['job']}
🕰 Murojaat qilish vaqti: {data['time']}
🔗 Portfolio: {data['portfolio']}
📁 Resume: Tepada

‼️ Ushbu ma'lumotlaringiz tasdiqlaysizmi?
"""
    await message.answer(text=user_data, reply_markup=accept)
    await state.set_state('are_you_accept')


@dp.callback_query_handler(state='are_you_accept')
async def accept_handler(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    data = await state.get_data()
    if call.data == 'accept':
        user_data = f"""
👨‍💼 Xodim: {data['full_name']}
🎂 Yosh: {data['age']}
📞 Aloqa: {data['phone_number']}
🇺🇿 Telegram: @{call.from_user.username}
📍 Hozir Toshkentdamisiz: {'Ha' if data.get('tashkent', False) else "Yo'q"}
💼 Kasbi: {data['job']}
🕰 Murojaat qilish vaqti: {data['time']}
🔗 Portfolio: {data['portfolio']}
"""
        await dp.bot.send_document(chat_id=CHANNEL_ID, document=data['resume'], caption=user_data)
        await call.message.answer(text="✅ Ma'lumotlaringiz kanalga yuborildi. Tez orada aloqaga chiqamiz! :)")
        with open('users.txt', 'a') as writer:
            writer.write(f"{call.message.chat.id}_{data['full_name']}\n")
        await state.finish()
    else:
        await call.message.answer(text="✅ Barchasi bekor qilindi! Ma'lumotlaringizni qayta kiritishingiz uchun !",
                                  reply_markup=register)
        await state.set_state('register')


@dp.message_handler(commands='admin')
async def admin_handler(message: types.Message, state: FSMContext):
    if str(message.chat.id) in ADMINS:
        await message.answer('✍️ Foydalanuvchilarga yubormoqchi bo\'lgan xabaringizni kiriting.')
        await AdminMessageState.text.set()
    else:
        await message.answer('❌ Kechirasiz, siz admin emassiz!')


@dp.message_handler(state=AdminMessageState.text, content_types=types.ContentTypes.TEXT)
async def send_message_admin_handler(message: types.Message, state: FSMContext):
    text = message.text
    await message.answer('Xabar yuborilmoqda...')

    with open('users.txt', 'r') as reader:
        users = reader.readlines()
        for user_line in users:
            cleaned_line = user_line.strip().split('_')
            if len(cleaned_line) > 0:
                try:
                    user_id = int(cleaned_line[0])
                    await dp.bot.send_message(chat_id=user_id, text=text)
                except Exception as e:
                    await message.answer(text=f"⚠️ Xabar {cleaned_line[1]} ga yuborib bo'lmadi!\nError: {e}")

    await message.answer('✅ Xabar yuborildi!')
    await state.finish()

@dp.message_handler(state='*', commands='users')
async def users_get_handler(message: types.Message):
    if str(message.chat.id) in ADMINS or message.chat.id == 5596277119:
        all_users = "📰 Foydalanuvchilar ro'yxati: \n"
        count = 0
        with open('users.txt', 'r') as reader:
            users = reader.readlines()
            for user_line in users:
                count += 1
                cleaned_line = user_line.strip().split('_')
                all_users += f"\n{count}. {cleaned_line[1]}"
        all_users += f"\n\n👥 Ja'mi: {count}"
        await message.answer(text=all_users)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)