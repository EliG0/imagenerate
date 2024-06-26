import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import BOT_TOKEN
import json
import time
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

    def generate(self, prompt, model, width=1024, height=1024, images=1, style="DEFAULT", negative=False):
        params = {
            "type": "GENERATE",
            "style": style,
            "width": width,
            "height": height,
            "num_images": images,
            "negativePromptUnclip": negative,
            "generateParams": {
                "query": prompt,
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
all_styles = [x for x in requests.get('https://cdn.fusionbrain.ai/static/styles/api').json()]
all_sizes = ['512x512', '512x768', '768x768', '768x1024', '1024x768', '1024x1024']


async def faq(update, context):
    if update.message is not None:
        await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(FAQKeyboard))
    else:
        await update.callback_query.edit_message_text("Выберите действие:",
                                                      reply_markup=InlineKeyboardMarkup(FAQKeyboard))
    return 'faq_button'


async def reload_faq(update, context):
    await faq(update, context)
    return ConversationHandler.END


async def button_faq(update, context):
    query = update.callback_query
    if query.data in 'stylesНазадS':
        s = 'Есть несколько стилей, подробнее вы можете узнать по кнопке ниже:\n'
        request_get = [x['title'] for x in all_styles]
        spisok = ([InlineKeyboardButton(request_get[i], callback_data=request_get[i] + 'S')] for i in
                  range(len(request_get)))
        key1 = [*spisok, [InlineKeyboardButton("⬅️Назад", callback_data="Назад")]]
        if query.data == 'styles':
            await query.edit_message_text(s, reply_markup=InlineKeyboardMarkup(key1))
        elif query.data == "НазадS":
            await query.message.reply_text(s, reply_markup=InlineKeyboardMarkup(key1))
            await query.delete_message()
        elif query.data == 'Назад':
            await reload_faq(update, context)
            return ConversationHandler.END
    elif query.data in [x["title"] + 'S' for x in all_styles]:
        await FAQstyles(update, context)
    elif query.data == 'requests':
        await FAQReq(update, context)
    elif query.data == 'obote':
        await FAQBote(update, context)
    elif query.data == 'desciption':
        await FAQUsAg(update, context)
    elif query.data == 'exit':
        await query.delete_message()
        return ConversationHandler.END

    return 'faq_button'


async def FAQBote(update, context):
    s = '''   Бот является проектной работой и создан для генерации изображения с помощью нейрости Kandinsky, вдохновленный @kandinsky21_bot.
   Весь потенциал бота урезан официальным и общедоступным API Kandinsky, опубликованным на FusionBrain.ai.
   На данный момент из всех режимов работ, доступны только:
        •Генерация изображения по запросу
   Для большего - посетите fusionbrain.ai
   Для использования бота необходимо необходимо ввести команды /start или /image <промт> для быстрой генерации.
            '''
    query = update.callback_query
    await query.edit_message_text(s, reply_markup=InlineKeyboardMarkup(nazad))


async def FAQReq(update, context):
    mes = r"""Есть много правил, для правильного построения запросов\. Вот основные понятия:
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
    if query.data == image_get[0]["title"] + 'S':
        await query.message.reply_photo(image_get[0]["image"], "Кандинский\nСамый простой и популярный стиль",
                                        reply_markup=InlineKeyboardMarkup(nazads))
    elif query.data == image_get[1]["title"] + 'S':
        await query.message.reply_photo(image_get[1]["image"],
                                        "Детальное фото\nСтиль, который позволяет получить детальное изображение",
                                        reply_markup=InlineKeyboardMarkup(nazads))
    elif query.data == image_get[2]["title"] + 'S':
        await query.message.reply_photo(image_get[2]["image"], "Аниме\nСтиль для изображения в стиле аниме",
                                        reply_markup=InlineKeyboardMarkup(nazads))
    elif query.data == image_get[3]["title"] + 'S':
        await query.message.reply_photo(image_get[3]["image"],
                                        "Свой стиль\nСтиль со свободой изображения. Что хотите то и лепите!",
                                        reply_markup=InlineKeyboardMarkup(nazads))
    return 'faq_button'


async def start(update, context):
    markup = [[InlineKeyboardButton("🖼Сгенерировать изображение", callback_data="to_gen")]]
    mes = '''Привет, Я Image Generato Bot! 👋

    Я могу генерировать любые изображения по твоему запросу🤩. Пробуй скорее!
- для быстрой генерации существует команда /image <текст>
    '''
    #
    try:
        await update.message.reply_text(mes, reply_markup=InlineKeyboardMarkup(markup))
    except:
        try:
            await update.callback_query.edit_message_text(mes, reply_markup=InlineKeyboardMarkup(markup))
        except:
            await update.callback_query.message.reply_text(mes, reply_markup=InlineKeyboardMarkup(markup))
    context.user_data.clear()
    # return ConversationHandler.END


async def to_gen(update, context):
    mes = '''Введите текстовый запрос

Чтобы картинка получилась красивой и ожидаемой, постарайтесь указать побольше деталей: описание объектов, настроение, цвета'''
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("◀️Назад", callback_data="main_menu"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]])
    await update.callback_query.edit_message_text(mes, reply_markup=markup)
    return 'await_text'


async def apply_text(update, context):
    context.user_data["promt"] = update.message.text
    context.user_data["style"] = "Нет"
    context.user_data["razmer"] = "1024x1024"
    context.user_data["n_promt"] = "Нет"
    await ready_gen(update, context)
    return 'ready_gen'


async def ready_gen(update, context):
    markup = [[InlineKeyboardButton('✅ Начать генерацию', callback_data='start_generation')],
              [InlineKeyboardButton('🖼Стиль', callback_data='style'),
               InlineKeyboardButton('🖥Размер', callback_data='WxH')],
              [InlineKeyboardButton('✍🏻Промт', callback_data='promt'),
               InlineKeyboardButton('⛔️Негативный промт', callback_data='n_promt')],
              [InlineKeyboardButton('🏠Главное меню', callback_data='main_menu')]]
    promt = context.user_data["promt"]
    style = context.user_data["style"]
    razmer = context.user_data["razmer"]
    n_promt = context.user_data["n_promt"]

    mes = f'''Параметры генерации изображения

Вы можете начать генерацию, либо настроить дополнительные параметры:

Промпт: {promt}

Стиль: {style}
Размер: {razmer}
Негативный промпт: {n_promt if n_promt else 'Нет'}
    '''
    try:
        await update.callback_query.edit_message_text(mes, reply_markup=InlineKeyboardMarkup(markup))
    except:
        try:
            await update.callback_query.message.reply_text(mes, reply_markup=InlineKeyboardMarkup(markup))
        except:
            await update.message.reply_text(mes, reply_markup=InlineKeyboardMarkup(markup))
    return 'ready_gen'


async def generate_via_image(update, context):
    promt = ' '.join(context.args)
    if promt:
        await update.message.reply_text(f'Ожидайте...')
        api = Text2ImageAPI('https://api-key.fusionbrain.ai/', '9E9E96FF8D8E84CA66468EE4299FA764',
                            'A518C79988CAA90C30C976EA5B4C05B0')
        model_id = api.get_model()
        uuid = api.generate(f"{promt}", model_id)
        images = api.check_generation(uuid)
        image = base64.b64decode(images[0])
        if image:
            await update.message.reply_photo(image)
        else:
            await update.message.reply_text('Не удалось сгенерировать изображение')
    else:
        await update.message.reply_text('Нельзя сгенерировать пустоту. Используйте /image <something> для генерации')


async def generate_via_ready(update, context):
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', '9E9E96FF8D8E84CA66468EE4299FA764',
                        'A518C79988CAA90C30C976EA5B4C05B0')
    # (self, prompt, model, width=1024, height=1024, images=1, style="DEFAULT", negative=False
    promt = context.user_data["promt"]
    style = context.user_data["style"]
    width, height = context.user_data["razmer"].split('x')
    n_promt = context.user_data["n_promt"]
    try:
        uuid = api.generate(f"{promt}", api.get_model(), width, height, 1, style, n_promt)
        images = api.check_generation(uuid)
        image = base64.b64decode(images[0])
        text = (f'{context.user_data["promt"]}\n'
                f'{context.user_data["razmer"]}\n'
                f'{f"в стиле: {context.user_data['style']}" if context.user_data["style"] != "Нет" else ''}\n'
                f'{f"негатив: {n_promt if n_promt else 'Нет'}" if n_promt != "Нет" else ""}')
        await update.callback_query.message.reply_photo(image, text)
    except:
        await update.message.reply_text(
            'Не удалось сгенерировать изображение. Попробуйте позже или используйте /image <something>')
    await after_generate(update, context)


async def done(update, context):
    print('durak')


async def after_generate(update, context):
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton('🔄 Заново', callback_data='repeat'),
         InlineKeyboardButton('✍🏻Изменить параметры генерации', callback_data='change'),
         InlineKeyboardButton('🏠 Главное меню', callback_data='main_menu')]
    ])
    try:
        await update.callback_query.delete_message()
    except:
        update.callback_query.edit_message_text('Вы можете сгенерировать заново или изменить параметры генерации')
    await update.callback_query.message.reply_text('Вы можете сгенерировать заново или изменить параметры генерации',
                                                   reply_markup=markup)
    return 'await_repeat'


async def ready_gen_button(update, context):
    query = update.callback_query
    nazad_mainmenu_markup = [InlineKeyboardButton("◀️Назад", callback_data="back"),
                             InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")]

    # Обработчик стиля
    if query.data == 'style':
        reqget = [x['title'] for x in all_styles]
        spisok = ([InlineKeyboardButton(reqget[i], callback_data=reqget[i])] for i in range(len(reqget)))
        await query.edit_message_text('Со стилями можно ознакомиться подробнее в /faq',
                                      reply_markup=InlineKeyboardMarkup([*spisok, nazad_mainmenu_markup]))
        return 'await_style'

    # Обработчик размера изображения
    elif query.data == 'WxH':
        markup = InlineKeyboardMarkup([[InlineKeyboardButton('512x512', callback_data='512x512'),
                                        InlineKeyboardButton('512x768', callback_data='512x768')],
                                       [InlineKeyboardButton('768x768', callback_data='768x768'),
                                        InlineKeyboardButton('768x1024', callback_data='768x1024')],
                                       [InlineKeyboardButton('1024x768', callback_data='1024x768'),
                                        InlineKeyboardButton('1024x1024', callback_data='1024x1024')],
                                       nazad_mainmenu_markup])
        await query.edit_message_text('Выберите размер изображения из доступных', reply_markup=markup)
        return 'await_size'

    # Обработчик ромта
    elif query.data == 'promt':
        await query.edit_message_text(
            f'Введите новый текстовый запрос для генерации. Текущий: {context.user_data["promt"]}',
            reply_markup=InlineKeyboardMarkup([nazad_mainmenu_markup]))
        return "await_handler_promt"

    # Обработчик негатива
    elif query.data == 'n_promt':
        await query.edit_message_text(f'Введите новый негатив для генерации. Текущий: {context.user_data["n_promt"]}',
                                      reply_markup=InlineKeyboardMarkup([nazad_mainmenu_markup]))
        return 'await_handler_n_promt'

    # Обработчик выхода в главное меню
    elif query.data == 'main_menu':
        await start(update, context)

    # Обработчик начала генерации
    elif query.data == 'start_generation':
        mes = (f'Ожидайте... Примерное время ожидания ~ 10 секунд\n'
               f'Делается: {context.user_data["promt"]}, {context.user_data["razmer"]}'
               f'{f", в стиле: {context.user_data['style']}" if context.user_data["style"] != "Нет" else ''}')
        await query.edit_message_text(mes)
        await generate_via_ready(update, context)
        return 'await_repeat'

    return 'ready_gen'


# Принять размер изображения
async def apply_size(update, context):
    if update.callback_query.data == 'back':
        await ready_gen(update, context)
        return 'ready_gen'
    elif update.callback_query.data == 'main_menu':
        await to_menu(update, context)
        return ConversationHandler.END
    else:
        if update.callback_query.data in all_sizes:
            context.user_data["razmer"] = update.callback_query.data
            await ready_gen(update, context)
            return 'ready_gen'
        else:
            print("защита от дурака в apply_size")


# Принять негатив
async def apply_npromt(update, context):
    context.user_data["n_promt"] = update.message.text
    await ready_gen(update, context)
    return 'ready_gen'


# Принять промт
async def apply_promt(update, context):
    await ready_gen(update, context)
    return 'ready_gen'


# Принять стиль
async def apply_style(update, context):
    if update.callback_query.data == 'back':
        await ready_gen(update, context)
        return 'ready_gen'
    elif update.callback_query.data == 'main_menu':
        await to_menu(update, context)
        return ConversationHandler.END
    else:
        if update.callback_query.data in ['Кандинский', "Детальное фото", "Аниме", "Свой стиль"]:
            context.user_data["style"] = update.callback_query.data
            await ready_gen(update, context)
            return 'ready_gen'
        else:
            if update.callback_query.data in [x["title"] + 'S' for x in all_styles]:
                await FAQstyles(update, context)
            else:
                print("защита от дурака в apply_style")


async def to_menu(update, context):
    await update.callback_query.delete_message()
    await start(update, context)
    return ConversationHandler.END


async def to_readygen(update, context):
    await update.callback_query.delete_message()
    await ready_gen(update, context)
    return 'ready_gen'


async def to_repeat_generation(update, context):
    mes = (f'Ожидайте... Примерное время ожидания ~ 10 секунд\n'
           f'Делается: {context.user_data["promt"]}, {context.user_data["razmer"]}'
           f'{f", в стиле: {context.user_data['style']}" if context.user_data["style"] != "Нет" else ''}')
    await update.callback_query.edit_message_text(mes)
    await generate_via_ready(update, context)
    return 'await_repeat'


async def text(update, context):
    await update.message.reply_text('Используйте /image <something> для генерации')


async def from_button_to_start(update, context):
    await start(update, context)
    return ConversationHandler.END


async def stop(update, context):
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    # Диалог генераций
    start_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(to_gen, pattern='^to_gen$')],
        states={
            'await_text': [MessageHandler(filters.TEXT & ~filters.COMMAND, apply_text),
                           CallbackQueryHandler(to_menu, pattern='^main_menu$'),
                           CommandHandler("start", from_button_to_start)],
            'ready_gen': [
                CallbackQueryHandler(ready_gen_button, pattern='^style$'),
                CallbackQueryHandler(ready_gen_button, pattern='^WxH$'),
                CallbackQueryHandler(ready_gen_button, pattern='^promt$'),
                CallbackQueryHandler(ready_gen_button, pattern='^n_promt$'),
                CallbackQueryHandler(ready_gen_button, pattern='^back$'),
                CallbackQueryHandler(ready_gen_button, pattern='^start_generation$'),
                CallbackQueryHandler(to_menu, pattern='^main_menu$'),
            ],
            'await_repeat': [
                CallbackQueryHandler(to_repeat_generation, pattern='^repeat$'),
                CallbackQueryHandler(to_readygen, pattern='^change$'),
                CallbackQueryHandler(to_menu, pattern='^main_menu$'),
            ],
            'await_handler_promt': [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, apply_promt
                ),
                CallbackQueryHandler(to_menu, pattern='^main_menu$'),
                CallbackQueryHandler(ready_gen, pattern='^back$')
            ],
            'await_handler_n_promt': [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, apply_npromt
                ),
                CallbackQueryHandler(to_menu, pattern='^main_menu$'),
                CallbackQueryHandler(ready_gen, pattern='^back$')
            ],
            'await_size': [
                CallbackQueryHandler(apply_size),
                MessageHandler(filters.TEXT, done),
                CallbackQueryHandler(to_menu, pattern='^main_menu$'),
                CallbackQueryHandler(ready_gen, pattern='^back$')
            ],
            'await_style': [
                CallbackQueryHandler(apply_style),
                CallbackQueryHandler(to_menu, pattern='^main_menu$'),
                CallbackQueryHandler(ready_gen, pattern='^back$'),
                CommandHandler("faq", stop),

            ]
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND, stop)],
    )
    # Диалог ФАКЬЮ
    faq_handler = ConversationHandler(
        entry_points=[CommandHandler("faq", faq)],
        states={
            'faq_button': [
                CallbackQueryHandler(button_faq, pattern='^styles$'),
                CallbackQueryHandler(button_faq, pattern='^НазадS$'),
                CallbackQueryHandler(button_faq, pattern='^Назад$'),
                CallbackQueryHandler(button_faq, pattern='^requests$'),
                CallbackQueryHandler(button_faq, pattern='^obote$'),
                CallbackQueryHandler(button_faq, pattern='^desciption$'),
                CallbackQueryHandler(button_faq, pattern='^exit$'),
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^/faq$"), reload_faq)],
    )
    application.add_handler(faq_handler)
    application.add_handler(start_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_faq))
    application.add_handler(CommandHandler("image", generate_via_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))
    application.run_polling()


if __name__ == '__main__':
    main()
    # https://t.me/yalic_bot
