import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler
from openai import OpenAI

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

PAINTING_URL = "https://raw.githubusercontent.com/paninsergey1965-lgtm/jadekey-art/main/56368897-14E3-49FF-908F-FFC3C3E5127A.png"

QUOTES = [
    "Умный с блеском выходит из ситуации, в которую мудрый никогда не попадёт.",
    "Жизнь — это не повод для беспокойства.",
    "Судьба готовится на медленном огне.",
    "Созревший плод не кричит о своей спелости.",
    "Плевать я хотел на то, что думают про плевки.",
]

SYSTEM_PROMPT = "Ты Бронислав Виногродский — китаевед, переводчик Дао Дэ Цзин и Чжуан-цзы. Говоришь без пафоса, иногда грубовато: хрен там, ну и чё, плевать я хотел. Короткие рубленые фразы после длинных. Любишь парадоксальные формулы: жизнь — это не повод для беспокойства, умный с блеском выходит из ситуации в которую мудрый никогда не попадёт. Проблемы называешь болезнью а не чертой. Используешь бытовые образы — кот вокруг коробки, рыбак который не бросает сеть в каждую лужу. Не даёшь советов — предлагаешь посмотреть самому. Говоришь на русском. Отвечаешь коротко — 3-5 предложений."

conversation_history = {}
message_counter = {}
MAX_HISTORY = 10

def get_history(user_id):
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    return conversation_history[user_id]

def add_to_history(user_id, role, content):
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > MAX_HISTORY * 2:
        conversation_history[user_id] = history[-MAX_HISTORY * 2:]

def get_keyboard():
    keyboard = [
        [InlineKeyboardButton("✨ Мудрость", callback_data="wisdom"),
         InlineKeyboardButton("🖌 Нарисуй", callback_data="draw")],
        [InlineKeyboardButton("🔄 Забыть всё", callback_data="clear")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    message_counter[user_id] = 0
    await update.message.reply_photo(
        photo=PAINTING_URL,
        caption=(
            "鼎 化生于火，成德于心\n"
            "Превращение рождается из огня — добродетель созревает в сердце.\n\n"
            "Это не чат-бот. Это зеркало.\n\n"
            "Спрашивай о том, что действительно беспокоит.\n"
            "Или просто говори. Мудрый не ищет ответов —\n"
            "он учится задавать правильные вопросы.\n\n"
            "Пиши или говори голосом.\n\n"
            "Слушаю."
        ),
        reply_markup=get_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "wisdom":
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Скажи одну короткую мудрость — свою любимую формулу. Одно-два предложения."}
        ]
        response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
        text = response.choices[0].message.content
        await query.message.reply_text(text, reply_markup=get_keyboard())

    elif query.data == "draw":
        await query.message.reply_text("Рисую...")
        history = get_history(user_id)
        context_text = " ".join([m["content"] for m in history[-4:]]) if history else "daoist philosophy, change, the way"
        prompt_msg = [{"role": "user", "content": "Based on this conversation, write a short image description for Chinese ink wash painting style. English only, 1-2 sentences. Context: " + context_text}]
        prompt_response = client.chat.completions.create(model="gpt-4o-mini", messages=prompt_msg)
        image_prompt = "Traditional Chinese painting, warm colors, red and gold accents, rich ink details, emotional, vibrant, in the style of classic gongbi and xieyi, " + prompt_response.choices[0].message.content
        image_response = client.images.generate(model="gpt-image-1", prompt=image_prompt, size="1024x1024", n=1)
        import base64
        img_bytes = base64.b64decode(image_response.data[0].b64_json)
        await query.message.reply_photo(photo=img_bytes, reply_markup=get_keyboard())

    elif query.data == "clear":
        conversation_history[user_id] = []
        message_counter[user_id] = 0
        await query.message.reply_text("Забыл всё. Начнём заново.", reply_markup=get_keyboard())

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    await file.download_to_drive("voice.ogg")
    with open("voice.ogg", "rb") as f:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=f)
    text = transcript.text
    add_to_history(user_id, "user", text)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(user_id)
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply_text = response.choices[0].message.content
    add_to_history(user_id, "assistant", reply_text)
    tts = client.audio.speech.create(model="tts-1", voice="echo", input=reply_text)
    tts.stream_to_file("reply.mp3")
    await update.message.reply_voice(voice=open("reply.mp3", "rb"), reply_markup=get_keyboard())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    add_to_history(user_id, "user", text)
    message_counter[user_id] = message_counter.get(user_id, 0) + 1
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + get_history(user_id)
    response = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    reply_text = response.choices[0].message.content
    add_to_history(user_id, "assistant", reply_text)
    await update.message.reply_text(reply_text, reply_markup=get_keyboard())
    if message_counter[user_id] % 5 == 0:
        quote = random.choice(QUOTES)
        await update.message.reply_photo(
            photo=PAINTING_URL,
            caption=f"_{quote}_",
            parse_mode="Markdown"
        )

app = Application.builder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.run_polling()
