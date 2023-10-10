import logging
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
import openai

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

MUSCLE_GROUP, INTENSITY = range(2)

openai.api_key = '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'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info(f"User {user.id} started the conversation.")
    keyboard = [
        [InlineKeyboardButton("Chest", callback_data='chest'),
         InlineKeyboardButton("Back", callback_data='back')],
        [InlineKeyboardButton("Legs", callback_data='legs'),
         InlineKeyboardButton("Arms", callback_data='arms')],
        [InlineKeyboardButton("Butt", callback_data='butt'),
         InlineKeyboardButton("Abs", callback_data='abs')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Choose a muscle group:', reply_markup=reply_markup)

    return MUSCLE_GROUP

async def muscle_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    query = update.callback_query
    muscle_group = query.data
    logger.info(f"User {user.id} selected muscle group: {muscle_group}")
    context.user_data['muscle_group'] = muscle_group
    keyboard = [
        [InlineKeyboardButton("Low", callback_data='low'),
         InlineKeyboardButton("Medium", callback_data='medium'),
         InlineKeyboardButton("High", callback_data='high')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('Choose an intensity level:', reply_markup=reply_markup)

    return INTENSITY

async def intensity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    query = update.callback_query
    intensity = query.data
    logger.info(f"User {user.id} selected intensity: {intensity}")
    muscle_group = context.user_data['muscle_group']

    await context.bot.send_chat_action(chat_id=query.message.chat_id, action='typing')

    processing_message = await query.message.reply_text('Processing your request. This may take a couple of minutes...')

    # Prepare the prompt for OpenAI in a conversation-like format
    prompt = f"""
    - - -
    User: Provide a workout plan for {muscle_group} muscles with {intensity} intensity.
    AI:"""

    # Fetch workout suggestion from OpenAI using gpt-3.5-turbo
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a fitness coach."},
            {"role": "user", "content": f"Provide a workout plan for {muscle_group} muscles with {intensity} intensity."}
        ]
    )
    workout_suggestion = response['choices'][0]['message']['content'].strip()
    await processing_message.edit_text(workout_suggestion)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info(f"User {user.id} canceled the conversation.")
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def main() -> None:
    application = Application.builder().token("6668637502:AAEp-lxUpp2f3XKghLzeDSClw7ALZ6Ll0xY").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MUSCLE_GROUP: [CallbackQueryHandler(muscle_group_callback, pattern='^(chest|back|legs|arms|butt|abs)$')],
            INTENSITY: [CallbackQueryHandler(intensity_callback, pattern='^(low|medium|high)$')]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
