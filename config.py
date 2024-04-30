from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

BOT_TOKEN = os.environ.get('TOKEN', None)
BOT_USERNAME = ''  # https://t.me/BOTUSERNAME Нужно для генерации реферальной ссылки
otstuk_chat = -732422972
ADMINS_ID = [1165126773]  # можно добавить много через запятую. Пример  [798661023, 798661023, 798661023]
# DATABASE
