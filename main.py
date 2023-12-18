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
import translators as trans
import sqlite3

dest_lang = 'en'
supported_languages = trans.get_languages()

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
TRACKING = 15
KCAL, CARDIO, LIFTING = range(16, 19)

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
    if update.message is None:
        return dest_lang
    dl = update.message.from_user.language_code
    if dl == '' or dl is None or dl not in supported_languages:
        dl = 'en'
    return dl


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: Optional[Message] = None) -> int:
    query = update.callback_query
    dest_lang = context.user_data['lang']
    calorie_button = trans.translate_text(query_text="Activity Tracking", translator='google',
                                          to_language=dest_lang)
    workout_button = trans.translate_text(query_text="Workouts", translator='google',
                                          to_language=dest_lang)
    user_button = trans.translate_text(query_text="User Profile", translator='google',
                                       to_language=dest_lang)
    # more_button = trans.translate_text(query_text="More Features", translator='google',
    # to_language=dest_lang)
    main_menu = trans.translate_text(query_text="Main Menu:", translator='google',
                                     to_language=dest_lang)
    keyboard = [
        [InlineKeyboardButton(calorie_button, callback_data='tracking')],
        [InlineKeyboardButton(workout_button, callback_data='workouts')],
        [InlineKeyboardButton(user_button, callback_data='user_profile')]
        # [InlineKeyboardButton(more_button, callback_data='more_features')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if message:
        mes = await message.reply_text(main_menu, reply_markup=reply_markup)
    else:
        mes = await update.message.reply_text(main_menu, reply_markup=reply_markup)

    return MAIN_MENU


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    dest_lang = context.user_data['lang']
    choice = query.data
    if choice == 'tracking':
        kcal = trans.translate_text(query_text='Add calories', translator='google', to_language=dest_lang)
        steps = trans.translate_text(query_text='Add steps', translator='google', to_language=dest_lang)
        cardio = trans.translate_text(query_text='Add cardio workout', translator='google', to_language=dest_lang)
        lifting = trans.translate_text(query_text='Add lifting workout', translator='google', to_language=dest_lang)
        burnt_kcal = trans.translate_text(query_text='Burnt calories', translator='google', to_language=dest_lang)
        mes = trans.translate_text(query_text='Choose an option below', translator='google', to_language=dest_lang)
        cb = trans.translate_text(query_text='Return to menu', translator='google', to_language=dest_lang)
        track_keyboard = [
            [InlineKeyboardButton(kcal, callback_data='kcal'), InlineKeyboardButton(steps, callback_data='steps')],
            [InlineKeyboardButton(cardio, callback_data='cardio'),
             InlineKeyboardButton(lifting, callback_data='lifting')],
            [InlineKeyboardButton(burnt_kcal, callback_data='burnt_kcal'),
             InlineKeyboardButton(cb, callback_data='return')]
        ]
        track_markup = InlineKeyboardMarkup(track_keyboard)
        await query.message.reply_text(mes + ":", reply_markup=track_markup)
        return TRACKING
    elif choice == 'workouts':
        single_button = trans.translate_text(query_text="Single Muscle Group", translator='google',
                                             to_language=dest_lang)
        compound_button = trans.translate_text(query_text="Compound Workouts", translator='google',
                                               to_language=dest_lang)
        workout_type_mes = trans.translate_text(query_text="Choose a workout type:", translator='google',
                                                to_language=dest_lang)
        workout_keyboard = [
            [InlineKeyboardButton(single_button, callback_data='single_muscle_group'),
             InlineKeyboardButton(compound_button, callback_data='compound')]
        ]
        workout_markup = InlineKeyboardMarkup(workout_keyboard)
        await query.message.reply_text(workout_type_mes + ":", reply_markup=workout_markup)
        return WORKOUT_AREA
    elif choice == 'user_profile':
        return await user_profile(update, context, query.message)
    return MAIN_MENU  # Remain in MAIN_MENU state for unrecognized choices


async def tracking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    dest_lang = context.user_data['lang']
    choice = query.data
    if choice == 'return':
        return await show_main_menu(update, context, query.message)
    elif choice == 'kcal':
        mes = trans.translate_text(query_text='Enter amount of eaten calories', translator='google',
                                   to_language=dest_lang)
        await query.message.reply_text(mes)
        return KCAL
    elif choice == 'steps':
        mes = trans.translate_text(query_text='Enter number of steps for today', translator='google',
                                   to_language=dest_lang)
        await query.message.reply_text(mes)
        return STEPS


async def kcal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    kcal = update.message.text
    kcal = int(kcal)
    add_kcal_record(user.id, kcal)
    mes = trans.translate_text(query_text='Calories added successfully. Returning to main menu.',
                               translator='google', to_language=dest_lang)
    await update.message.reply_text(mes)
    return await show_main_menu(update, context)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = get_dest_lang(update)
    logger.info(f"User {user.id} started the conversation.")
    context.user_data.update(load_user_data(user.id))
    context.user_data['lang'] = dest_lang
    user_data = await get_user(user.id)
    if len(user_data) == 0:
        start_mes = trans.translate_text(
            query_text="Let\'s start by collecting some information.\nWhat is your gender? (Male / Female / Other)",
            translator='google', to_language=dest_lang)
        await update.message.reply_text(start_mes)
        return GENDER  # Transition to GENDER state
    else:
        return await show_main_menu(update, context)


async def gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    gender = update.message.text
    logger.info(f"Gender of {user.id}: {gender}")
    context.user_data['gender'] = gender.lower()
    dest_lang = context.user_data['lang']
    age_mes = trans.translate_text(query_text="What is your age?", translator='google', to_language=dest_lang)
    await update.message.reply_text(age_mes)
    return AGE


async def age_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    age = update.message.text
    invalid_age_mes = trans.translate_text(query_text="Please enter a valid age.", translator='google',
                                           to_language=dest_lang)
    height_mes = trans.translate_text(query_text="What is your height in cm?", translator='google',
                                      to_language=dest_lang)
    try:
        age = int(age)  # Make sure age is a valid number
        if 0 < age < 120:  # Sanity check for age
            logger.info(f"Age of {user.id}: {age}")
            context.user_data['age'] = age
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
    dest_lang = context.user_data['lang']
    height = update.message.text
    invalid_height_mes = trans.translate_text(query_text="Please enter a valid weight.", translator='google',
                                              to_language=dest_lang)
    weight_mes = trans.translate_text(query_text='What is your weight in kg?', translator='google',
                                      to_language=dest_lang)
    try:
        height = int(height)
        if 120 < height < 230:
            logger.info(f"Height of {user.id}: {height}")
            context.user_data['height'] = height
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
    dest_lang = context.user_data['lang']
    weight = update.message.text
    invalid_weight_mes = trans.translate_text(query_text="Please enter a valid weight.", translator='google',
                                              to_language=dest_lang)
    steps_mes = trans.translate_text(query_text='On average, how many steps do you take per day?',
                                     translator='google', to_language=dest_lang)
    try:
        weight = float(weight)
        if 30 < weight < 200:
            logger.info(f"Weight of {user.id}: {weight}")
            context.user_data['weight'] = weight
            await update.message.reply_text(steps_mes)
            return STEPS  # Transition to STEPS state
        else:
            await update.message.reply_text(invalid_weight_mes)
            return WEIGHT
    except ValueError:
        await update.message.reply_text(invalid_weight_mes)
        return WEIGHT


async def steps_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    steps = update.message.text
    steps = int(steps)
    add_steps_record(user.id, steps)
    mes = trans.translate_text(query_text='Steps added successfully. Returning to the main menu.',
                               translator='google', to_language=dest_lang)
    await update.message.reply_text(mes)
    return await show_main_menu(update, context)
    # invalid_steps_mes = trans.translate_text(query_text="Please enter a valid number of steps.",
    #                                          to_language=dest_lang)
    # workout_mes = trans.translate_text(query_text='How many times do you workout per week?',
    #                                    to_language=dest_lang)
    # try:
    #     steps = int(steps)
    #     if 0 <= steps <= 100000:
    #         logger.info(f"Average steps per day of {user.id}: {steps}")
    #         context.user_data['steps'] = steps
    #         await update.message.reply_text(workout_mes)
    #         return WORKOUT_FREQUENCY
    #     else:
    #         await update.message.reply_text(invalid_steps_mes)
    #         return STEPS
    # except ValueError:
    #     await update.message.reply_text(invalid_steps_mes)
    #     return STEPS


async def workout_frequency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    workout_frequency = update.message.text
    main_menu_mes = trans.translate_text(query_text="Transitioning to the main menu.", translator='google',
                                         to_language=dest_lang)
    invalid_workout_mes = trans.translate_text(query_text="Please enter a valid number of workouts.",
                                               translator='google', to_language=dest_lang)
    type_workout_mes = trans.translate_text(
        query_text='What type of workouts do you usually do? (Cardio / Lifting / Both)',
        translator='google', to_language=dest_lang)
    try:
        if int(workout_frequency) <= 0:
            workout_frequency = max(0, int(workout_frequency))
            context.user_data['workout_frequency'] = workout_frequency
            logger.info(f"Workout frequency of {user.id}: {workout_frequency}")
            save_user_data(user.id, context.user_data)
            user_data = context.user_data
            await add_user_to_database(user.id, user_data['gender'], user_data['height'], user_data['weight'],
                                       user_data['steps'], user_data['workout_frequency'], user_data['bmr'],
                                       user_data['age'])
            await calculate_bmr(update, context)
            await update.message.reply_text(main_menu_mes)
            return await show_main_menu(update, context)
        else:
            workout_frequency = max(0, int(workout_frequency))
            context.user_data['workout_frequency'] = workout_frequency
            logger.info(f"Workout frequency of {user.id}: {workout_frequency}")
            save_user_data(user.id, context.user_data)
    except ValueError:
        await update.message.reply_text(invalid_workout_mes)
        return WORKOUT_FREQUENCY
    await update.message.reply_text(type_workout_mes)
    return WORKOUT_TYPE


async def workout_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    workout_type = update.message.text
    workout_type = trans.translate_text(query_text=workout_type, translator='google', to_language=dest_lang)
    logger.info(f"Workout type of {user.id}: {workout_type}")
    context.user_data['workout_type'] = workout_type.lower()
    save_user_data(user.id, context.user_data)  # Save all collected data to file
    await calculate_bmr(update, context)
    user_data = context.user_data
    await add_user_to_database(user.id, user_data['gender'], user_data['height'], user_data['weight'],
                               user_data['steps'],
                               user_data['workout_frequency'], user_data['bmr'], user_data['age'])
    transition_mes = trans.translate_text(query_text="Transitioning to the main menu.", translator='google',
                                          to_language=dest_lang)
    await update.message.reply_text(transition_mes)
    return await show_main_menu(update, context)


async def muscle_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    dest_lang = context.user_data['lang']
    query = update.callback_query
    muscle_group = query.data

    logger.info(f"User {user.id} selected muscle group: {muscle_group}")
    context.user_data['muscle_group'] = muscle_group

    low_int = trans.translate_text(query_text="Low intensity", translator='google', to_language=dest_lang)
    med_int = trans.translate_text(query_text="Medium intensity", translator='google', to_language=dest_lang)
    high_int = trans.translate_text(query_text="High intensity", translator='google', to_language=dest_lang)
    int_mes = trans.translate_text(query_text='Choose an intensity level:', translator='google',
                                   to_language=dest_lang)
    keyboard = [
        [InlineKeyboardButton(low_int, callback_data='low'),
         InlineKeyboardButton(med_int, callback_data='medium'),
         InlineKeyboardButton(high_int, callback_data='high')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(
        int_mes,
        reply_markup=reply_markup)
    return INTENSITY


async def workout_area_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    dest_lang = context.user_data['lang']
    query = update.callback_query
    workout_type = query.data
    logger.info(f"User {user.id} selected workout type: {workout_type}")

    chest = trans.translate_text(query_text="Chest", translator='google', to_language=dest_lang)
    back = trans.translate_text(query_text="Back", translator='google', to_language=dest_lang)
    legs = trans.translate_text(query_text="Legs", translator='google', to_language=dest_lang)
    arms = trans.translate_text(query_text="Arms", translator='google', to_language=dest_lang)
    butt = trans.translate_text(query_text="Butt", translator='google', to_language=dest_lang)
    abs_ = trans.translate_text(query_text="Abs", translator='google', to_language=dest_lang)
    muscle_mes = trans.translate_text(query_text='Choose a muscle group:', translator='google', to_language=dest_lang)
    full = trans.translate_text(query_text="Full Body", translator='google', to_language=dest_lang)
    lower = trans.translate_text(query_text="Lower Body", translator='google', to_language=dest_lang)
    upper = trans.translate_text(query_text="Upper Body", translator='google', to_language=dest_lang)
    workout_mes = trans.translate_text(query_text="Choose a workout:", translator='google', to_language=dest_lang)

    if workout_type == 'single_muscle_group':
        keyboard = [
            [InlineKeyboardButton(chest, callback_data='chest'),
             InlineKeyboardButton(back, callback_data='back')],
            [InlineKeyboardButton(legs, callback_data='legs'),
             InlineKeyboardButton(arms, callback_data='arms')],
            [InlineKeyboardButton(butt, callback_data='butt'),
             InlineKeyboardButton(abs_, callback_data='abs')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            muscle_mes,
            reply_markup=reply_markup)
        return MUSCLE_GROUP
    else:  # compound workouts
        keyboard = [
            [InlineKeyboardButton(full, callback_data='full_body'),
             InlineKeyboardButton(upper, callback_data='upper_body'),
             InlineKeyboardButton(lower, callback_data='lower_body')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.reply_text(
            workout_mes,
            reply_markup=reply_markup)
        return MUSCLE_GROUP


async def intensity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    dest_lang = context.user_data['lang']
    query = update.callback_query
    intensity = query.data
    logger.info(f"User {user.id} selected intensity: {intensity}")
    muscle_group = context.user_data['muscle_group']

    proc_mes = trans.translate_text(query_text='Processing your request. This may take a couple of minutes...',
                                    translator='google', to_language=dest_lang)
    feedback_mes = trans.translate_text(query_text='How did you like the workout plan?', translator='google',
                                        to_language=dest_lang)

    await context.bot.send_chat_action(chat_id=query.message.chat_id, action='typing')

    processing_message = await query.message.reply_text(proc_mes)

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
    workout_suggestion = trans.translate_text(query_text=workout_suggestion, translator='google',
                                              to_language=dest_lang)
    await processing_message.edit_text(workout_suggestion)

    feedback_keyboard = [
        [InlineKeyboardButton("Good", callback_data='good'),
         InlineKeyboardButton("Bad", callback_data='bad')]
    ]
    feedback_markup = InlineKeyboardMarkup(feedback_keyboard)
    await query.message.reply_text(feedback_mes, reply_markup=feedback_markup)
    return FEEDBACK


async def feedback_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    dest_lang = context.user_data['lang']
    query = update.callback_query
    feedback = query.data  # This will be 'good' or 'bad' based on the button pressed
    logger.info(f"User {user.id} gave feedback: {feedback}")
    await query.message.reply_text(
        trans.translate_text(query_text="Thank you for your feedback! Redirecting to the main menu.",
                             translator='google', to_language=dest_lang))
    return await show_main_menu(update, context, query.message)


async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, message: Optional[Message] = None) -> int:
    # user_data = context.user_data
    user_data = (await get_user(update.effective_user.id))[-1]
    dest_lang = context.user_data['lang']
    gender = trans.translate_text(query_text='Gender', translator='google', to_language=dest_lang)
    height = trans.translate_text(query_text='Height', translator='google', to_language=dest_lang)
    weight = trans.translate_text(query_text='Weight', translator='google', to_language=dest_lang)
    steps = trans.translate_text(query_text='Steps per day', translator='google', to_language=dest_lang)
    freq = trans.translate_text(query_text='Workout Frequency', translator='google', to_language=dest_lang)
    tpw = trans.translate_text(query_text='times per week', translator='google', to_language=dest_lang)
    wtype = trans.translate_text(query_text='Workout Type', translator='google', to_language=dest_lang)
    kcal = trans.translate_text(query_text='kcal/day', translator='google', to_language=dest_lang)
    return_butt = trans.translate_text(query_text='Return', translator='google', to_language=dest_lang)
    profile_info = (
        f"{gender}: {user_data['gender']}\n"
        f"{height}: {user_data['height']} cm\n"
        f"{weight}: {user_data['weight']} kg\n"
        f"{steps}: {user_data['steps']}\n"
        f"{freq}: {user_data['workout_frequency']} "
        f"{tpw}\n"
        # f"{wtype}: {user_data['workout_type']}\n"
        f"BMR: {user_data['bmr']} {kcal}"
    )
    keyboard = [
        [InlineKeyboardButton(return_butt,
                              callback_data='return')]]
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
    height = float(str(context.user_data.get('height')).replace(',', '.'))
    weight = float(str(context.user_data.get('weight')).replace(',', '.'))

    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:  # Assuming female for any other input
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    context.user_data['bmr'] = bmr
    save_user_data(update.effective_user.id, context.user_data)  # Save updated data to file


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    logger.info(f"User {user.id} canceled the conversation.")
    cancel_mes = trans.translate_text(query_text="Bye! I hope we can talk again some day.", translator='google',
                                      to_language=dest_lang)
    await update.message.reply_text(cancel_mes, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def create_database_and_table():
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            gender TEXT,
            height REAL,
            weight REAL,
            steps INTEGER,
            workout_frequency INTEGER,
            bmr REAL,
            age INTEGER
        )
    ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS weights (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                date DATE,
                weight REAL
            )
        ''')

    cursor.execute('''
                CREATE TABLE IF NOT EXISTS steps (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    date DATE,
                    steps INTEGER
                )
            ''')

    cursor.execute('''
                CREATE TABLE IF NOT EXISTS kcal (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    date DATE,
                    type TEXT,
                    kcal INTEGER
                )
            ''')

    connection.commit()
    connection.close()


async def add_user_to_database(user_id, gender, height, weight, steps, workout_frequency, bmr, age):
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()

    cursor.execute(
        '''INSERT INTO users (user_id, gender, height, weight, steps, workout_frequency, bmr, age) VALUES (?, ?, ?, 
        ?, ?, ?, ?, ?)''',
        (user_id, gender, height, weight, steps, workout_frequency, bmr, age))

    connection.commit()
    connection.close()


async def get_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchall()
    conn.close()

    res = list()
    if user_data is not None:
        for user in user_data:
            keys = (
                'user_id', 'gender', 'height', 'weight', 'steps', 'workout_frequency', 'bmr', 'age'
            )
            res.append(dict(zip(keys, user)))
        return res
    return None


def main() -> None:
    # application = Application.builder().token("6668637502:AAEp-lxUpp2f3XKghLzeDSClw7ALZ6Ll0xY").build() # нужный
    application = Application.builder().token("6520497677:AAH2QjNPwcqvYA558rJsSHOBW-RIDK6HX3Y").build()

    create_database_and_table()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [CallbackQueryHandler(main_menu_callback,
                                             pattern='^(tracking|workouts|user_profile)$')],
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
            FEEDBACK: [CallbackQueryHandler(feedback_callback, pattern='^(good|bad)$')],
            WORKOUT_AREA: [CallbackQueryHandler(workout_area_callback, pattern='^(single_muscle_group|compound)$')],
            USER_PROFILE: [CallbackQueryHandler(user_profile_callback, pattern='^return$')],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age_callback)],
            TRACKING: [
                CallbackQueryHandler(tracking_callback, pattern='^(kcal|steps|cardio|lifting|burnt_kcal|return)$')],
            KCAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, kcal_callback)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
