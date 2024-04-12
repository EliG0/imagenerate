import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes, \
    ConversationHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
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
FAQKeyboard = [
    [
        InlineKeyboardButton("🎨Стили", callback_data="styles")
    ],
    # [
    #     InlineKeyboardButton("💪🏻Возможности Бота", callback_data="2")
    # ],
    [
        InlineKeyboardButton("✏️Описание запросов", callback_data="requests")
    ],
    [
        InlineKeyboardButton("🤖О Боте", callback_data="obote")
    ],
    [
        InlineKeyboardButton("📄Пользовательское соглашение", callback_data="desciption"),
    ],
    [
        InlineKeyboardButton("Понятно ✅", callback_data="exit")
    ],
]
nazad = [[InlineKeyboardButton("Понятно ✅", callback_data="Назад")]]


async def faq(update, context):
    if update.message != None:
        await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(FAQKeyboard))
    else:
        await update.callback_query.edit_message_text("Выберите действие:",
                                                      reply_markup=InlineKeyboardMarkup(FAQKeyboard))


async def button_faq(update, context):
    query = update.callback_query
    await query.answer()

    if query.data in 'stylesНазадS':
        styles = [x for x in requests.get('https://cdn.fusionbrain.ai/static/styles/api').json()]
        s = 'Есть несколько стилей, подробнее вы можете узнать по кнопке ниже:\n'
        reqget = [x['title'] for x in styles]
        spisok = ([InlineKeyboardButton(reqget[i], callback_data=reqget[i])] for i in range(len(reqget)))
        key1 = [*spisok, [InlineKeyboardButton("⬅️Назад", callback_data="Назад")]]

    if query.data == 'styles':
        await query.edit_message_text(s, reply_markup=InlineKeyboardMarkup(key1))

    elif query.data in ['Кандинский', "Детальное фото", "Аниме", "Свой стиль"]:
        await FAQstyles(update, context)

    # elif query.data == '2':
    #     await query.edit_message_text("Возможности Бота", reply_markup=InlineKeyboardMarkup(nazad))

    elif query.data == 'requests':
        await FAQReq(update, context)

    elif query.data == 'obote':
        await FAQBote(update, context)

    elif query.data == 'desciption':
        await FAQUsAg(update, context)

    elif query.data == 'exit':
        await query.delete_message()

    elif query.data == 'Назад':
        await faq(update, context)

    elif query.data == "НазадS":
        await query.message.reply_text(s, reply_markup=InlineKeyboardMarkup(key1))
        await query.delete_message()


async def FAQBote(update, context):
    s = '''   Бот является проектной работой и создан для генерации изображения с помощью нейрости Kandinsky, вдохновленный @kandinsky21_bot.
   Весь потенциал бота урезан официальным и общедоступным API Kandinsky, опубликованным на FusionBrain.ai.
   На данный момент из всех режимов работ, доступны только:
        •Генерация изображения по запросу
   Для большего - посетите fusionbrain.ai
            '''
    query = update.callback_query
    await query.edit_message_text(s, reply_markup=InlineKeyboardMarkup(nazad))


async def FAQReq(update, context):
    mes = """Есть много правил, для правильного построения запросов\. Вот основные понятия:
    • Подробно опишите задачу ‒ Опишите, какой результат вы хотите получить
    • Добавьте тему или объект ‒ детально опишите главный объект
    • Добавьте больше деталей ‒ чем больше деталей будет содержать запрос, тем точнее полученный текст или изображение будет соответствовать вашим ожиданиям
    • Больше можно узнать на сайте [skillbox\.ru](https://skillbox.ru/media/code/prompty-dlya-neyrosetey-kak-pravilno-pisat-zaprosy-k-chatgpt-i-drugim-neyronnym-setyam/)
    """
    query = update.callback_query
    await query.edit_message_text(mes, parse_mode='MarkdownV2', disable_web_page_preview=True,
                                  reply_markup=InlineKeyboardMarkup(nazad))


async def FAQUsAg(update, context):
    mes = '''   Правила пользования ботом
    
   Начиная использование телеграм‒бота, вы соглашаетесь с [Пользовательским соглашением](https://www.sberbank.com/common/img/uploaded/files/promo/kandinskiy-terms/kandinskiy-terms-of-use.pdf) и [Политикой конфиденциальности](https://www.sberbank.ru/privacy/policy#pdn)
   Обращаем внимание, что текстовые запросы, а также графические объекты, которые вы создаете в этом боте, не должны нарушать законодательство Российской Федерации, законодательство страны использования Платформы и общепризнанные этические правила и нормы

   Вся ответственность за Пользовательский контент лежит на пользователе
'''
    query = update.callback_query
    await query.edit_message_text(mes, parse_mode='MarkdownV2', disable_web_page_preview=True,
                                  reply_markup=InlineKeyboardMarkup(nazad))


async def FAQstyles(update, context):
    query = update.callback_query
    nazads = [[InlineKeyboardButton("⬅️Назад", callback_data="НазадS")]]
    image_get = requests.get("https://cdn.fusionbrain.ai/static/styles/api").json()
    await query.delete_message()
    if query.data == image_get[0]["title"]:
        await query.message.reply_photo(image_get[0]["image"], "Кандинский\nСамый простой и популярный стиль",
                                        reply_markup=InlineKeyboardMarkup(nazads))
    elif query.data == image_get[1]["title"]:
        await query.message.reply_photo(image_get[1]["image"],
                                        "Детальное фото\nСтиль, который позволяет получить детальное изображение",
                                        reply_markup=InlineKeyboardMarkup(nazads))
    elif query.data == image_get[2]["title"]:
        await query.message.reply_photo(image_get[2]["image"], "Аниме\nСтиль для изображения в стиле аниме",
                                        reply_markup=InlineKeyboardMarkup(nazads))
    elif query.data == image_get[3]["title"]:
        await query.message.reply_photo(image_get[3]["image"],
                                        "Свой стиль\nСтиль со свободой изображения. Что хотите то и лепите!",
                                        reply_markup=InlineKeyboardMarkup(nazads))


async def start(update, context):
    # markup = ReplyKeyboardMarkup([['Сгенерировать изображение'], ['Поменять размер']], one_time_keyboard=True,                                 resize_keyboard=True)
    markup = [[InlineKeyboardButton("Сгенерировать изображение", callback_data="to_gen")]]
    mes = '''Привет, Я KandiBot! 👋
    
    Я могу генерировать любые изображения по твоему запросу🤩. Пробуй скорее!
    Введи /image <текст>
    '''
    # - для быстрой генерации существует команда /image <текст>
    await update.message.reply_text(mes)


async def to_gen(update, context):
    query = update.callback_query
    mes = '''Введите текстовый запрос

Чтобы картинка получилась красивой и ожидаемой, постарайтесь указать побольше деталей: описание объектов, настроение, цвета'''
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]])
    await query.edit_message_text(mes, reply_markup=markup)


async def ready_gen(update, context):
    mes = f'''Параметры генерации изображения

Вы можете начать генерацию, либо настроить дополнительные параметры:

Промпт: Милая лисичка

Стиль: Нет
Соотношение сторон: 1:1
Модель: Kandinsky 3.0
Негативный промпт: Нет
    '''


async def text(update, context):
    await update.message.reply_text('Используйте /image <something> для генерации')


async def generate_image(update, context):
    promt = ' '.join(context.args)
    if promt:

        await update.message.reply_text(f'Делается "{promt}"')
        api = Text2ImageAPI('https://api-key.fusionbrain.ai/', '9E9E96FF8D8E84CA66468EE4299FA764',
                            'A518C79988CAA90C30C976EA5B4C05B0')
        model_id = api.get_model()
        global size
        x, y = size
        uuid = api.generate(f"{promt}", model_id, width=x, height=y)
        images = api.check_generation(uuid)
        image = base64.b64decode(images[0])
        if image:
            await update.message.reply_photo(image)
        else:
            await update.message.reply_text('Не удалось сгенерировать изображение')
    else:
        await update.message.reply_text('Нельзя сгенерировать пустоту. Используйте /image <something> для генерации')


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    global size
    size = (1024, 1024)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("faq", faq))
    # conv_handler = ConversationHandler(
    #     entry_points=[CallbackQueryHandler(to_gen, pattern='^to_gen$')],
    #     states={
    #         1: [
    #             MessageHandler(filters.TEXT & ~filters.COMMAND),
    #             # MessageHandler(filters.Regex("^Something else...$"), custom_choice),
    #         ]
    #     },
    #     # fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    # )
    #
    # application.add_handler(conv_handler).
    application.add_handler(CallbackQueryHandler(button_faq))
    application.add_handler(CommandHandler("image", generate_image))
    application.run_polling()


if __name__ == '__main__':
    main()
    # https://t.me/yalic_bot
