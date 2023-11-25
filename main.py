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
import httpx
import json
import os
from typing import Optional
from telegram import Message
from googletrans import Translator, LANGUAGES

trans = Translator()
# SOURCE_LANG = 'en'
dest_lang = 'en'

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

handler = logging.FileHandler(filename='MuscleMate.log', mode='a')
logger = logging.getLogger(__name__)
logger.addHandler(handler)

MUSCLE_GROUP, INTENSITY, FEEDBACK, ASK_AGAIN = range(4)
GENDER, HEIGHT, WEIGHT, STEPS = range(4, 8)
WORKOUT_FREQUENCY, WORKOUT_TYPE = range(8, 10)
MAIN_MENU = 10
WORKOUT_AREA = 11
USER_PROFILE, BMR = range(12, 14)
AGE = 14

openai.api_key = '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'

USER_DATA_FILE = "user_data.json"


def load_user_data(user_id):
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            return data.get(str(user_id), {})
    return {}


def save_user_data(user_id, data):
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            all_data = json.load(f)
    else:
        all_data = {}
    all_data[str(user_id)] = data
    with open(USER_DATA_FILE, "w") as f:
        json.dump(all_data, f)


def get_dest_lang(update: Update) -> str:
    dest_lang = update.message.from_user.language_code
    if dest_lang == '' or dest_lang not in LANGUAGES:
        dest_lang = 'en'
    return dest_lang


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: Optional[Message] = None) -> int:
    query = update.callback_query
    dest_lang = get_dest_lang(update)
    calorie_button = trans.translate(text="Calorie Tracking", src='en', dest=dest_lang)
    workout_button = trans.translate(text="Workouts", src='en', dest=dest_lang)
    user_button = trans.translate(text="User Profile", src='en', dest=dest_lang)
    more_button = trans.translate(text="More Features", src='en', dest=dest_lang)
    keyboard = [
        [InlineKeyboardButton(calorie_button, callback_data='calorie_tracking')],
        [InlineKeyboardButton(workout_button, callback_data='workouts')],
        [InlineKeyboardButton(user_button, callback_data='user_profile')],
        [InlineKeyboardButton(more_button, callback_data='more_features')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    main_menu = trans.translate(text="Main Menu:", src='en', dest=dest_lang)
    if message:
        await message.reply_text(main_menu, reply_markup=reply_markup)
    else:
        await update.message.reply_text(main_menu, reply_markup=reply_markup)
    return MAIN_MENU


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    dest_lang = get_dest_lang(update)
    choice = query.data
    if choice == 'calorie_tracking':
        # Transition to CALORIE_TRACKING state (define this state and its handling later)
        pass
    elif choice == 'workouts':
        single_button = trans.translate(text="Single Muscle Group", src='en', dest=dest_lang)
        compound_button = trans.translate(text="Compound Workouts", src='en', dest=dest_lang)
        workout_keyboard = [
            [InlineKeyboardButton(single_button, callback_data='single_muscle_group'),
             InlineKeyboardButton(compound_button, callback_data='compound')]
        ]
        workout_markup = InlineKeyboardMarkup(workout_keyboard)
        workout_type_mes = trans.translate(text="Choose a workout type:", src='en', dest=dest_lang)
        await query.message.reply_text(workout_type_mes, reply_markup=workout_markup)
        return WORKOUT_AREA
    elif choice == 'user_profile':
        return await user_profile(update, context, query.message)
    elif choice == 'more_features':
        # Transition to MORE_FEATURES state (define this state and its handling later)
        pass
    return MAIN_MENU  # Remain in MAIN_MENU state for unrecognized choices


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = get_dest_lang(update)
    logger.info(f"User {user.id} started the conversation.")
    context.user_data.update(load_user_data(user.id))
    start_mes = trans.translate(
        text="Let\'s start by collecting some information.\nWhat is your gender? (Male / Female / Other)", src='en',
        dest=dest_lang)
    await update.message.reply_text(start_mes)
    return GENDER  # Transition to GENDER state


async def gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    gender = update.message.text
    logger.info(f"Gender of {user.id}: {gender}")
    context.user_data['gender'] = gender.lower()
    dest_lang = get_dest_lang(update)
    age_mes = trans.translate(text="What is your age?", src='en', dest=dest_lang)
    await update.message.reply_text(age_mes)
    return AGE


async def age_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = get_dest_lang(update)
    age = update.message.text
    invalid_age_mes = trans.translate(text="Please enter a valid age.", src='en', dest=dest_lang)
    try:
        age = int(age)  # Make sure age is a valid number
        if 0 < age < 120:  # Sanity check for age
            logger.info(f"Age of {user.id}: {age}")
            context.user_data['age'] = age
            height_mes = trans.translate(text="What is your height in cm?", src='en', dest=dest_lang)
            await update.message.reply_text(height_mes)
            return HEIGHT
        else:
            await update.message.reply_text(invalid_age_mes)
            return AGE  # Repeat the AGE state if the input is not valid
    except ValueError:
        await update.message.reply_text(invalid_age_mes)
        return AGE


async def height_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = get_dest_lang(update)
    height = update.message.text
    invalid_height_mes = trans.translate(text="Please enter a valid height.", src='en', dest=dest_lang)
    try:
        height = int(height)
        if 120 < height < 230:
            logger.info(f"Height of {user.id}: {height}")
            context.user_data['height'] = height
            weight_mes = trans.translate(text='What is your weight in kg?', src='en', dest=dest_lang)
            await update.message.reply_text(weight_mes)
            return WEIGHT  # Transition to WEIGHT state
        else:
            await update.message.reply_text(invalid_height_mes)
            return HEIGHT
    except ValueError:
        await update.message.reply_text(invalid_height_mes)
        return HEIGHT


async def weight_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = get_dest_lang(update)
    weight = update.message.text
    invalid_weight_mes = trans.translate(text="Please enter a valid weight.", src='en', dest=dest_lang)
    try:
        weight = float(weight)
        if 30 < weight < 200:
            logger.info(f"Weight of {user.id}: {weight}")
            context.user_data['weight'] = weight
            steps_mes = trans.translate(text='On average, how many steps do you take per day?', src='en',
                                        dest=dest_lang)
            await update.message.reply_text('On average, how many steps do you take per day?')
            return STEPS  # Transition to STEPS state
        else:
            await update.message.reply_text(invalid_weight_mes)
            return WEIGHT
    except ValueError:
        await update.message.reply_text(invalid_weight_mes)
        return WEIGHT


async def steps_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = get_dest_lang(update)
    steps = update.message.text
    invalid_steps_mes = trans.translate(text="Please enter a valid number of steps.", src='en', dest=dest_lang)
    try:
        steps = int(steps)
        if 0 <= steps <= 100000:
            logger.info(f"Average steps per day of {user.id}: {steps}")
            context.user_data['steps'] = steps
            await update.message.reply_text(
                trans.translate(text='How many times do you workout per week?', src='en', dest=dest_lang))
            return WORKOUT_FREQUENCY
        else:
            await update.message.reply_text(invalid_steps_mes)
            return STEPS
    except ValueError:
        await update.message.reply_text(invalid_steps_mes)
        return STEPS


async def workout_frequency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = get_dest_lang(update)
    workout_frequency = update.message.text
    try:
        if int(workout_frequency) <= 0:
            workout_frequency = max(0, int(workout_frequency))
            context.user_data['workout_frequency'] = workout_frequency
            logger.info(f"Workout frequency of {user.id}: {workout_frequency}")
            save_user_data(user.id, context.user_data)
            await calculate_bmr(update, context)
            await update.message.reply_text(
                trans.translate(text="Transitioning to the main menu.", src='en', dest=dest_lang))
            return await show_main_menu(update, context)
    except ValueError:
        await update.message.reply_text(
            trans.translate(text="Please enter a valid number of workouts.", src='en', dest=dest_lang))
        return WORKOUT_FREQUENCY
    await update.message.reply_text(
        trans.translate(text='What type of workouts do you usually do? (Cardio / Lifting / Both)', src='en',
                        dest=dest_lang))
    return WORKOUT_TYPE


async def workout_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = get_dest_lang(update)
    workout_type = update.message.text
    workout_type = trans.translate(text=workout_type, dest='en')
    logger.info(f"Workout type of {user.id}: {workout_type}")
    context.user_data['workout_type'] = workout_type.lower()
    save_user_data(user.id, context.user_data)  # Save all collected data to file
    await calculate_bmr(update, context)
    transition_mes = trans.translate(text="Transitioning to the main menu.", src='en', dest=dest_lang)
    await update.message.reply_text(transition_mes)
    return await show_main_menu(update, context)


async def muscle_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    dest_lang = get_dest_lang(update)
    query = update.callback_query
    muscle_group = query.data

    logger.info(f"User {user.id} selected muscle group: {muscle_group}")
    context.user_data['muscle_group'] = muscle_group
    keyboard = [
        [InlineKeyboardButton(trans.translate(text="Low intensity", src='en', dest=dest_lang), callback_data='low'),
         InlineKeyboardButton(trans.translate(text="Medium intensity", src='en', dest=dest_lang),
                              callback_data='medium'),
         InlineKeyboardButton(trans.translate(text="High intensity", src='en', dest=dest_lang), callback_data='high')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(trans.translate(text='Choose an intensity level:', src='en', dest=dest_lang),
                                   reply_markup=reply_markup)
    return INTENSITY


async def workout_area_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    dest_lang = get_dest_lang(update)
    query = update.callback_query
    workout_type = query.data
    logger.info(f"User {user.id} selected workout type: {workout_type}")

    if workout_type == 'single_muscle_group':
        keyboard = [
            [InlineKeyboardButton(trans.translate(text="Chest", src='en', dest=dest_lang), callback_data='chest'),
             InlineKeyboardButton(trans.translate(text="Back", src='en', dest=dest_lang), callback_data='back')],
            [InlineKeyboardButton(trans.translate(text="Legs", src='en', dest=dest_lang), callback_data='legs'),
             InlineKeyboardButton(trans.translate(text="Arms", src='en', dest=dest_lang), callback_data='arms')],
            [InlineKeyboardButton(trans.translate(text="Butt", src='en', dest=dest_lang), callback_data='butt'),
             InlineKeyboardButton(trans.translate(text="Abs", src='en', dest=dest_lang), callback_data='abs')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(trans.translate(text='Choose a muscle group:', src='en', dest=dest_lang),
                                       reply_markup=reply_markup)
        return MUSCLE_GROUP
    else:  # compound workouts
        keyboard = [
            [InlineKeyboardButton(trans.translate(text="Full Body", src='en', dest=dest_lang),
                                  callback_data='full_body'),
             InlineKeyboardButton(trans.translate(text="Upper Body", src='en', dest=dest_lang),
                                  callback_data='upper_body'),
             InlineKeyboardButton(trans.translate(text="Lower Body", src='en', dest=dest_lang),
                                  callback_data='lower_body')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(trans.translate(text="Choose a workout:", src='en', dest=dest_lang),
                                       reply_markup=reply_markup)
        return MUSCLE_GROUP


async def intensity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    dest_lang = get_dest_lang(update)
    query = update.callback_query
    intensity = query.data
    logger.info(f"User {user.id} selected intensity: {intensity}")
    muscle_group = context.user_data['muscle_group']

    await context.bot.send_chat_action(chat_id=query.message.chat_id, action='typing')

    processing_message = await query.message.reply_text(
        trans.translate(text='Processing your request. This may take a couple of minutes...', src='en', dest=dest_lang))

    async with httpx.AsyncClient(timeout=120000.0) as client:  # Use httpx.AsyncClient to make asynchronous requests
        if muscle_group in ['chest', 'back', 'legs', 'arms', 'butt', 'abs']:
            # Single muscle group workout request
            request_content = f"Provide a workout plan for {muscle_group} muscles with {intensity} intensity."
        else:
            # Compound workout request
            request_content = f"Provide a {muscle_group} workout plan with {intensity} intensity."

        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openai.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a fitness coach."},
                    {"role": "user", "content": request_content}
                ],
            },
        )
    response_data = response.json()
    workout_suggestion = response_data['choices'][0]['message']['content'].strip()
    await processing_message.edit_text(trans.translate(text=workout_suggestion, src='en', dest=dest_lang))

    feedback_keyboard = [
        [InlineKeyboardButton("Good", callback_data='good'),
         InlineKeyboardButton("Bad", callback_data='bad')]
    ]
    feedback_markup = InlineKeyboardMarkup(feedback_keyboard)
    await query.message.reply_text(trans.translate(text='How was the workout plan?', src='en', dest=dest_lang),
                                   reply_markup=feedback_markup)
    return FEEDBACK


async def feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    dest_lang = get_dest_lang(update)
    query = update.callback_query
    feedback = query.data  # This will be 'good' or 'bad' based on the button pressed
    logger.info(f"User {user.id} gave feedback: {feedback}")
    await query.message.reply_text(
        trans.translate(text="Thank you for your feedback! Redirecting to the main menu.", src='en', dest=dest_lang))
    return await show_main_menu(update, context, query.message)


async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, message: Optional[Message] = None) -> int:
    user_data = context.user_data
    dest_lang = get_dest_lang(update)
    profile_info = (
        f"{trans.translate(text='Gender', src='en', dest=dest_lang)}: {user_data.get('gender')}\n"
        f"{trans.translate(text='Height', src='en', dest=dest_lang)}: {user_data.get('height')} cm\n"
        f"{trans.translate(text='Weight', src='en', dest=dest_lang)}: {user_data.get('weight')} kg\n"
        f"{trans.translate(text='Steps per day', src='en', dest=dest_lang)}: {user_data.get('steps')}\n"
        f"{trans.translate(text='Workout Frequency', src='en', dest=dest_lang)}: {user_data.get('workout_frequency')} "
        f"{trans.translate(text='times per week', src='en', dest=dest_lang)}\n"
        f"{trans.translate(text='Workout Type', src='en', dest=dest_lang)}: {user_data.get('workout_type')}\n"
        f"BMR: {user_data.get('bmr')} {trans.translate(text='kcal/day', src='en', dest=dest_lang)}"
    )
    keyboard = [
        [InlineKeyboardButton(trans.translate(text='Return', src='en', dest=dest_lang), callback_data='return')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if message:
        await message.reply_text(profile_info, reply_markup=reply_markup)
    else:
        await update.message.reply_text(profile_info, reply_markup=reply_markup)
    return USER_PROFILE


async def user_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    choice = query.data
    if choice == 'return':
        return await show_main_menu(update, context, query.message)
    return USER_PROFILE


async def calculate_bmr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[Message]:
    # Assuming age is already collected and saved in user_data
    age = context.user_data.get('age', 25)  # Replace 25 with actual age
    gender = context.user_data.get('gender')
    height = float(context.user_data.get('height').replace(',', '.'))
    weight = float(context.user_data.get('weight').replace(',', '.'))

    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:  # Assuming female for any other input
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    context.user_data['bmr'] = bmr
    save_user_data(update.effective_user.id, context.user_data)  # Save updated data to file


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = get_dest_lang(update)
    logger.info(f"User {user.id} canceled the conversation.")
    # logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        trans.translate(text="Bye! I hope we can talk again some day.", src='en', dest=dest_lang),
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    application = Application.builder().token("6668637502:AAEp-lxUpp2f3XKghLzeDSClw7ALZ6Ll0xY").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_callback,
                                             pattern='^(calorie_tracking|workouts|user_profile|more_features)$')],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender_callback)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height_callback)],
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_callback)],
            STEPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, steps_callback)],
            WORKOUT_FREQUENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, workout_frequency_callback)],
            WORKOUT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, workout_type_callback)],
            MUSCLE_GROUP: [CallbackQueryHandler(muscle_group_callback,
                                                pattern='^(chest|back|legs|arms|butt|abs|full_body|upper_body'
                                                        '|lower_body)$')],
            INTENSITY: [CallbackQueryHandler(intensity_callback, pattern='^(low|medium|high)$')],
            FEEDBACK: [CallbackQueryHandler(feedback_callback, pattern='^(good|bad)$')],  # Add this line
            WORKOUT_AREA: [CallbackQueryHandler(workout_area_callback, pattern='^(single_muscle_group|compound)$')],
            USER_PROFILE: [CallbackQueryHandler(user_profile_callback, pattern='^return$')],  # Add this line
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
