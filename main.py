import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import ReplyKeyboardMarkup
import random
from config import BOT_TOKEN
import json
import time
import datetime
import requests
import base64


class Text2ImageAPI:

    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, model, width=1024, height=1024, images=1):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}"
            }
        }

        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=5):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['images']

            attempts -= 1
            time.sleep(delay)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    markup = ReplyKeyboardMarkup([['Сгенерировать изображение'], ['Поменять размер']], one_time_keyboard=True,
                                 resize_keyboard=True)
    await update.message.reply_text('Что бы вы хотели сделать?', reply_markup=markup)


async def text(update, context):
    global size
    if update.message.text == 'Поменять размер':
        await size_image(update, context)
    elif update.message.text == '768x1024':
        size = (768, 1024)
        await update.message.reply_text('Разрешение успешно изменено на 768x1024')
        await close(update, context)
    elif update.message.text == '1024x768':
        size = (1024, 768)
        await update.message.reply_text('Разрешение успешно изменено на 1024x768')
        await close(update, context)
    elif update.message.text == '1024x1024':
        size = (1024, 1024)
        await update.message.reply_text('Разрешение успешно изменено на 1024x1024')
        await close(update, context)
    else:
        await update.message.reply_text('Используйте /image <something> для генерации')


async def generate_image(update, context):
    promt = ' '.join(context.args)
    await update.message.reply_text(f'Делается "{promt}"')
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', '9E9E96FF8D8E84CA66468EE4299FA764',
                        'A518C79988CAA90C30C976EA5B4C05B0')
    model_id = api.get_model()
    global size
    x, y = size
    uuid = api.generate(f"{promt}", model_id, width=x, height=y)
    images = api.check_generation(uuid)
    l = '''image\\{(datetime.date.today())}\\{datetime.datetime.now().strftime('%H-%M-%S')}.png'''
    with open(f"image\\generation.png", "wb") as file:
        file.write(base64.b64decode(images[0]))

    await update.message.reply_photo(open(f"image\\generation.png", "rb"))
    # await update.message.delete()

async def size_image(update, context):
    markup = ReplyKeyboardMarkup([['768x1024', '1024x768', '1024x1024']], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text('Какой размер?', reply_markup=markup)


async def close(update, context):
    await start(update, context)


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    global size
    size = (1024, 1024)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("size", size_image))
    application.add_handler(CommandHandler("image", generate_image))
    application.add_handler(CommandHandler("close", close))
    application.run_polling()


if __name__ == '__main__':
    main()
    # https://t.me/yalic_bot
