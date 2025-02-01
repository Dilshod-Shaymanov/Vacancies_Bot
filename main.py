from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, \
    InlineKeyboardButton

from config import BOT_TOKEN, CHANNEL_ID

storage = MemoryStorage()

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot, storage=storage)

users = []

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

@dp.message_handler(commands='start')
async def start_command(message: types.Message):
    if message.chat.id in users:
        raise await message.answer(text="❌ Siz avvalroq anketa to'ldirgansiz!", reply_markup=ReplyKeyboardRemove())
    await message.answer(text="😊 Assalomu alaykum. Botimizga xush kelibsiz. Ro'yxatdan o'tish tugmasini bosing.", reply_markup=register)

@dp.message_handler(text="🪪 Ro'yxatdan O'tish")
async def register_handler(message: types.Message, state: FSMContext):
    if message.chat.id in users:
        raise await message.answer(text="❌ Siz avvalroq anketa to'ldirgansiz!", reply_markup=ReplyKeyboardRemove())
    await message.answer(text="✍️ To'liq ismingizni kiriting.", reply_markup=ReplyKeyboardRemove())
    await state.set_state('full_name')

@dp.message_handler(state='full_name')
async def full_name_handler(message: types.Message, state: FSMContext):
    await state.update_data({
        'full_name': message.text
    })
    await message.answer(text=f"😊 Xurmatli {message.text}. Iltimos telefon raqamingizni tugma orqali yuboring!", reply_markup=phone_number)
    await state.set_state('phone_number')

@dp.message_handler(state='phone_number', content_types=types.ContentType.CONTACT)
async def phone_number_handler(message: types.Message, state: FSMContext):
    await state.update_data({
        'phone_number': message.contact.phone_number if message.contact.phone_number.startswith('+') else f"+{message.contact.phone_number}"
    })
    await message.answer(text='🕔 Yoshingizni yuboring: ', reply_markup=ReplyKeyboardRemove())
    await state.set_state('age')

@dp.message_handler(state='age')
async def age_handler(message: types.Message, state: FSMContext):
    try:
        if int(message.text) < 10:
            await message.answer(text='😕 Botni 10 yoshdan kichik yoshlilar ishlatishi mumkin emas!')
        else:
            await state.update_data({
                'age': message.text
            })
            await message.answer(text="📁 O'zingiz skillaringizni .pdf faylida resume qilib yuboring!")
            await state.set_state('resume')
    except ValueError:
        await message.answer(text='❌ Iltimos yoshingizni faqat raqamda kiriting ‼️')

@dp.message_handler(state='resume', content_types=types.ContentType.DOCUMENT)
async def resume_handler(message: types.Message, state: FSMContext):
    await state.update_data({
        'resume': message.document.file_id
    })
    await message.answer(text="🕔 Murojaat qilish vaqtini kiriting.\n‼️ Bu siz bilan bog'lanishimiz uchun juda muhim\nMasalan: 08:00 - 20:00")
    await state.set_state('time')

@dp.message_handler(state='time')
async def time_handler(message: types.Message, state: FSMContext):
    await state.update_data({
        'time': message.text
    })
    data = await state.get_data()
    user_data = f"""
Ma'lumotlaringiz 📌:

👨‍💼 To'liq ism: {data['full_name']}
📞 Telefon raqam: {data['phone_number']}
🎂 Yosh: {data['age']}
🕰 Murojaat qilish vaqti: {data['time']}
📁 Resume: Tepada

‼️ Ushbu ma'lumotlaringiz tasdiqlaysizmi?
"""
    await state.update_data({
        'full_name': data['full_name'],
        'phone_number': data['phone_number'],
        'age': data['age'],
        'time': data['time'],
        'resume': data['resume'],
    })
    await message.answer(text=user_data, reply_markup=accept)
    await state.set_state('are_you_accept')

@dp.callback_query_handler(state='are_you_accept')
async def accept_handler(call: types.CallbackQuery, state: FSMContext):
    await call.message.delete()
    data = await state.get_data()
    if call.data == 'accept':
        user_data = f"""
👨‍💼 To'liq ism: {data['full_name']}
📞 Telefon raqam: {data['phone_number']}
🎂 Yosh: {data['age']}
🕰 Murojaat qilish vaqti: {data['time']}
📁 Resume: Tepada
"""
        await dp.bot.send_document(chat_id=CHANNEL_ID, document=data['resume'])
        await dp.bot.send_message(chat_id=CHANNEL_ID, text=user_data)
        await call.message.answer(text="✅ Ma'lumotlaringiz kanalga yuborildi. Tez orada aloqaga chiqamiz! :)")
        users.append(call.message.chat.id)
    else:
        await call.message.answer(text="✅ Barchasi bekor qilindi! Ma'lumotlaringizni qayta kiritishingiz mumkin!")
    await state.finish()

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)