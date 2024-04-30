import aiogram.types
from aiogram import Bot, F, types, Router, Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.utils import deep_linking
from config import BOT_USERNAME, ADMINS_ID, otstuk_chat
from filters.filters import DeepLinkFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards.kb import again_kb, admin_kb, cancel_kb
from database.db import DB

client = Router()
dp = Dispatcher()

LINK = ''


class AnonStates(StatesGroup):
    get_message = State()
    send_again = State()
    send_text = State()
    answer_state = State()


def format_username(username):
    if username:
        return "@" + username
    return "None"


def get_id_info(user):
    if type(user) == str or type(user) == int:
        return '<a href="tg://user?id=' + str(user) + '">Пользователь</a>'
    return f"{user.mention_html(user.full_name)} (@{user.username})"


@client.message(CommandStart(), DeepLinkFilter())
async def deep_start(message: types.Message, state: FSMContext, bot: Bot):
    await DB.add_user(message.chat.id)
    await state.set_state(AnonStates.get_message)
    payload = message.text.split()[1]
    await bot.send_message(otstuk_chat,
                           "Новый пользователь!\n" +
                           get_id_info(message.from_user) + "\n" +
                           "Рефер: " + get_id_info(payload),
                           parse_mode='HTML')
    await state.update_data(to_send=payload)

    await message.answer("""
🚀 Здесь можно отправить анонимное сообщение человеку, который опубликовал эту ссылку.

Напишите сюда всё, что хотите ему передать и через несколько секунд он получит ваше сообщение, но не будет знать от кого.

Отправить можно фото, видео, текст, голосовые, видеосообщения (кружки), а также стикеры.

⚠️ Это полностью анонимно!""", reply_markup=cancel_kb())

    await state.set_state(AnonStates.get_message)


@client.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext, bot: Bot):
    await DB.add_user(message.chat.id)
    await bot.send_message(otstuk_chat,
                           "Новый пользователь!\n" +
                           get_id_info(message.from_user) + "\n" +
                           "Рефер: None",
                           parse_mode='HTML')
    await state.clear()
    LINK = deep_linking.create_deep_link(username=BOT_USERNAME, link_type='start', payload=str(message.from_user.id))[
           8:]
    text = f"""🚀 Начни получать анонимные сообщения прямо сейчас!

Твоя личная ссылка:
👉  <code>{LINK}</code>

Размести эту ссылку ☝️ в своём профиле Telegram/Instagram/TikTok или других соц сетях, чтобы начать получать сообщения 💬
"""
    await message.answer(text, parse_mode='HTML')


@dp.callback_query(F.data == 's')
@client.message(AnonStates.get_message, F.text)
async def get_message(message: types.Message, state: FSMContext, bot: Bot):
    payload = await state.get_data()
    text = f"""
<b>У тебя новое сообщение!</b>

{message.text}

↩️<i>Свайпни для ответа</i>"""

    await message.answer("Сообщение отправлено, ожидайте ответ!", reply_markup=again_kb())
    await bot.send_message(chat_id=payload['to_send'], text=text, parse_mode='HTML')
    await bot.send_message(chat_id=otstuk_chat,
                           text=get_id_info(message.from_user) + " отправил сообщение " + get_id_info(
                               payload["to_send"]) + " 👇", parse_mode='HTML')
    await bot.forward_message(chat_id=otstuk_chat, from_chat_id=message.chat.id, message_id=message.message_id)
    await state.set_state(AnonStates.send_again)

    cur_state = dp.fsm.get_context(bot=bot, chat_id=int(payload['to_send']), user_id=int(payload['to_send']))
    await cur_state.update_data(userid=message.from_user.id)
    await cur_state.update_data(messageid=message.message_id)
    await cur_state.set_state(AnonStates.answer_state)


@client.message(AnonStates.get_message)
async def get_message_other(message: types.Message, state: FSMContext, bot: Bot):
    payload = await state.get_data()

    text = f"""
<b>У тебя новое сообщение!</b>

↩️<i>Свайпни для ответа</i>"""
    await bot.send_message(chat_id=payload['to_send'], text=text, parse_mode='HTML')
    await bot.copy_message(chat_id=payload['to_send'], from_chat_id=message.chat.id, message_id=message.message_id)
    await bot.send_message(chat_id=otstuk_chat,
                           text=get_id_info(message.from_user) + " отправил сообщение " + get_id_info(
                               payload["to_send"]) + " 👇", parse_mode='HTML')
    await bot.forward_message(chat_id=otstuk_chat, from_chat_id=message.chat.id, message_id=message.message_id)

    cur_state = dp.fsm.get_context(bot=bot, chat_id=payload['to_send'], user_id=payload['to_send'])
    await cur_state.update_data(userid=message.from_user.id)
    await cur_state.update_data(messageid=message.message_id)
    await cur_state.set_state(AnonStates.answer_state)


@client.callback_query(F.data == 'send_again')
async def send_again(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.answer('Отправьте сообщение', reply_markup=cancel_kb())
    await state.set_state(AnonStates.send_text)
    await callback.answer()


@client.callback_query(F.data == 'cancel')
async def close(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.delete()
    await state.clear()
    LINK = deep_linking.create_deep_link(username=BOT_USERNAME, link_type='start', payload=str(callback.from_user.id))[
           8:]
    text = f"""🚀 Начни получать анонимные сообщения прямо сейчас!

        Твоя личная ссылка:
        👉  <code>{LINK}</code>

        Размести эту ссылку ☝️ в своём профиле Telegram/Instagram/TikTok или других соц сетях, чтобы начать получать сообщения 💬
        """
    await callback.message.answer(text, parse_mode='HTML')
    await callback.answer()


@client.message(AnonStates.send_text, F.text)
async def send_again(message: types.Message, state: FSMContext, bot: Bot):
    payload = await state.get_data()

    text = f"""
<b>У тебя новое сообщение!</b>

{message.text}

↩️<i>Свайпни для ответа</i>"""

    await message.answer("Сообщение отправлено, ожидайте ответ!", reply_markup=again_kb())
    await bot.send_message(chat_id=payload['to_send'], text=text, parse_mode='HTML')
    await bot.send_message(chat_id=otstuk_chat,
                           text=get_id_info(message.from_user) + " отправил сообщение " + get_id_info(
                               payload["to_send"]) + " 👇", parse_mode='HTML')
    await bot.forward_message(chat_id=otstuk_chat, from_chat_id=message.chat.id, message_id=message.message_id)

    cur_state = dp.fsm.get_context(bot=bot, chat_id=int(payload['to_send']), user_id=int(payload['to_send']))
    await cur_state.update_data(userid=message.from_user.id)
    await cur_state.update_data(messageid=message.message_id)
    await cur_state.set_state(AnonStates.answer_state)
    await state.update_data()


@client.message(AnonStates.send_text)
async def send_again_other(message: types.Message, state: FSMContext, bot: Bot):
    payload = await state.get_data()

    text = f"""
<b>У тебя новое анонимное сообщение!</b>

↩️<i>Свайпни для ответа</i>"""
    await bot.send_message(chat_id=payload['to_send'], text=text, parse_mode='HTML')
    await bot.copy_message(chat_id=payload['to_send'], from_chat_id=message.chat.id, message_id=message.message_id)
    await bot.send_message(chat_id=otstuk_chat,
                           text=get_id_info(message.from_user) + " отправил сообщение " + get_id_info(
                               payload["to_send"]) + " 👇", parse_mode='HTML')
    await bot.forward_message(chat_id=otstuk_chat, from_chat_id=message.chat.id, message_id=message.message_id)
    cur_state = dp.fsm.get_context(bot=bot, chat_id=int(payload['to_send']), user_id=int(payload['to_send']))
    await cur_state.update_data(userid=message.from_user.id)
    await cur_state.update_data(messageid=message.message_id)
    await cur_state.set_state(AnonStates.answer_state)


@client.message(AnonStates.answer_state)
async def answer_state_handler(message: types.Message, bot: Bot, state: FSMContext):
    if message.reply_to_message:
        data = await state.get_data()
        userid = data['userid']
        messageid = data['messageid']

        await bot.send_message(chat_id=userid, text=message.text, reply_to_message_id=messageid,
                               reply_markup=again_kb())
        await bot.send_message(chat_id=otstuk_chat,
                               text=get_id_info(message.from_user.id) + " отправил ответ " + get_id_info(userid) + " 👇",
                               parse_mode='HTML')
        await bot.forward_message(chat_id=otstuk_chat, from_chat_id=message.chat.id, message_id=message.message_id)
        await message.answer("Твой ответ успешно отправлен 😺", reply_markup=again_kb())
        await state.clear()
