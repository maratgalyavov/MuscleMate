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
    if dest_lang != 'en':
        calorie_button = trans.translate_text(query_text="Calorie Tracking", from_language='en', to_language=dest_lang)
        workout_button = trans.translate_text(query_text="Workouts", from_language='en', to_language=dest_lang)
        user_button = trans.translate_text(query_text="User Profile", from_language='en', to_language=dest_lang)
        more_button = trans.translate_text(query_text="More Features", from_language='en', to_language=dest_lang)
        main_menu = trans.translate_text(query_text="Main Menu:", from_language='en', to_language=dest_lang)
    else:
        calorie_button = "Calorie Tracking"
        workout_button = "Workouts"
        user_button = "User Profile"
        more_button = "More Features"
        main_menu = "Main Menu"
    keyboard = [
        [InlineKeyboardButton(calorie_button, callback_data='calorie_tracking')],
        [InlineKeyboardButton(workout_button, callback_data='workouts')],
        [InlineKeyboardButton(user_button, callback_data='user_profile')],
        [InlineKeyboardButton(more_button, callback_data='more_features')]
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
    if choice == 'calorie_tracking':
        if dest_lang != 'en':
            mes = trans.translate_text(query_text='In progress', from_language='en', to_language=dest_lang)
        else:
            mes = 'In progress'
        await query.message.reply_text(mes)
        return await show_main_menu(update, context, query.message)
    elif choice == 'workouts':
        if dest_lang != 'en':
            single_button = trans.translate_text(query_text="Single Muscle Group", from_language='en',
                                                 to_language=dest_lang)
            compound_button = trans.translate_text(query_text="Compound Workouts", from_language='en',
                                                   to_language=dest_lang)
            workout_type_mes = trans.translate_text(query_text="Choose a workout type:", from_language='en',
                                                    to_language=dest_lang)
        else:
            single_button = "Single Muscle Group"
            compound_button = "Compound Workouts"
            workout_type_mes = "Choose a workout type"
        workout_keyboard = [
            [InlineKeyboardButton(single_button, callback_data='single_muscle_group'),
             InlineKeyboardButton(compound_button, callback_data='compound')]
        ]
        workout_markup = InlineKeyboardMarkup(workout_keyboard)
        await query.message.reply_text(workout_type_mes + ":", reply_markup=workout_markup)
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
    context.user_data['lang'] = dest_lang
    if dest_lang != 'en':
        start_mes = trans.translate_text(
            query_text="Let\'s start by collecting some information.\nWhat is your gender? (Male / Female / Other)",
            from_language='en',
            to_language=dest_lang)
    else:
        start_mes = "Let\'s start by collecting some information.\nWhat is your gender? (Male / Female / Other)"
    await update.message.reply_text(start_mes)
    return GENDER  # Transition to GENDER state


async def gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    gender = update.message.text
    logger.info(f"Gender of {user.id}: {gender}")
    context.user_data['gender'] = gender.lower()
    dest_lang = context.user_data['lang']
    if dest_lang != 'en':
        age_mes = trans.translate_text(query_text="What is your age?", from_language='en', to_language=dest_lang)
    else:
        age_mes = "What is your age?"
    await update.message.reply_text(age_mes)
    return AGE


async def age_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    age = update.message.text
    if dest_lang != 'en':
        invalid_age_mes = trans.translate_text(query_text="Please enter a valid age.", from_language='en',
                                               to_language=dest_lang)
        height_mes = trans.translate_text(query_text="What is your height in cm?", from_language='en',
                                          to_language=dest_lang)
    else:
        invalid_age_mes = "Please enter a valid age."
        height_mes = "What is your height in cm?"
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
    if dest_lang != 'en':
        invalid_height_mes = trans.translate_text(query_text="Please enter a valid weight.", from_language='en',
                                                  to_language=dest_lang)
        weight_mes = trans.translate_text(query_text='What is your weight in kg?', from_language='en',
                                          to_language=dest_lang)
    else:
        invalid_height_mes = "Please enter a valid weight."
        weight_mes = 'What is your weight in kg?'
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
    if dest_lang != 'en':
        invalid_weight_mes = trans.translate_text(query_text="Please enter a valid weight.", from_language='en',
                                                  to_language=dest_lang)
        steps_mes = trans.translate_text(query_text='On average, how many steps do you take per day?',
                                         from_language='en',
                                         to_language=dest_lang)
    else:
        invalid_weight_mes = "Please enter a valid weight."
        steps_mes = 'On average, how many steps do you take per day?'
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
    if dest_lang != 'en':
        invalid_steps_mes = trans.translate_text(query_text="Please enter a valid number of steps.", from_language='en',
                                                 to_language=dest_lang)
        workout_mes = trans.translate_text(query_text='How many times do you workout per week?', from_language='en',
                                           to_language=dest_lang)
    else:
        invalid_steps_mes = "Please enter a valid number of steps."
        workout_mes = 'How many times do you workout per week?'
    try:
        steps = int(steps)
        if 0 <= steps <= 100000:
            logger.info(f"Average steps per day of {user.id}: {steps}")
            context.user_data['steps'] = steps
            await update.message.reply_text(workout_mes)
            return WORKOUT_FREQUENCY
        else:
            await update.message.reply_text(invalid_steps_mes)
            return STEPS
    except ValueError:
        await update.message.reply_text(invalid_steps_mes)
        return STEPS


async def workout_frequency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    workout_frequency = update.message.text
    if dest_lang != 'en':
        main_menu_mes = trans.translate_text(query_text="Transitioning to the main menu.", from_language='en',
                                             to_language=dest_lang)
        invalid_workout_mes = trans.translate_text(query_text="Please enter a valid number of workouts.",
                                                   from_language='en',
                                                   to_language=dest_lang)
        type_workout_mes = trans.translate_text(
            query_text='What type of workouts do you usually do? (Cardio / Lifting / Both)',
            from_language='en',
            to_language=dest_lang)
    else:
        main_menu_mes = "Transitioning to the main menu."
        invalid_workout_mes = "Please enter a valid number of workouts."
        type_workout_mes = 'What type of workouts do you usually do? (Cardio / Lifting / Both)'
    try:
        if int(workout_frequency) <= 0:
            workout_frequency = max(0, int(workout_frequency))
            context.user_data['workout_frequency'] = workout_frequency
            logger.info(f"Workout frequency of {user.id}: {workout_frequency}")
            save_user_data(user.id, context.user_data)
            user_data = context.user_data
            add_user_to_database(user.id, user_data['gender'], user_data['height'], user_data['weight'],
                                 user_data['steps'], user_data['workout_frequency'], user_data['bmr'], user_data['age'])
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
    workout_type = trans.translate_text(query_text=workout_type, to_language='en')
    logger.info(f"Workout type of {user.id}: {workout_type}")
    context.user_data['workout_type'] = workout_type.lower()
    save_user_data(user.id, context.user_data)  # Save all collected data to file
    await calculate_bmr(update, context)
    user_data = context.user_data
    add_user_to_database(user.id, user_data['gender'], user_data['height'], user_data['weight'], user_data['steps'],
                         user_data['workout_frequency'], user_data['bmr'], user_data['age'])
    if dest_lang != 'en':
        transition_mes = trans.translate_text(query_text="Transitioning to the main menu.", from_language='en',
                                              to_language=dest_lang)
    else:
        transition_mes = "Transitioning to the main menu."
    await update.message.reply_text(transition_mes)
    return await show_main_menu(update, context)


async def muscle_group_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    dest_lang = context.user_data['lang']
    query = update.callback_query
    muscle_group = query.data

    logger.info(f"User {user.id} selected muscle group: {muscle_group}")
    context.user_data['muscle_group'] = muscle_group

    if dest_lang != 'en':
        low_int = trans.translate_text(query_text="Low intensity", from_language='en', to_language=dest_lang)
        med_int = trans.translate_text(query_text="Medium intensity", from_language='en', to_language=dest_lang)
        high_int = trans.translate_text(query_text="High intensity", from_language='en', to_language=dest_lang)
        int_mes = trans.translate_text(query_text='Choose an intensity level:', from_language='en',
                                       to_language=dest_lang)
    else:
        low_int = "Low intensity"
        med_int = "Medium intensity"
        high_int = "High intensity"
        int_mes = 'Choose an intensity level:'
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

    if dest_lang != 'en':
        chest = trans.translate_text(query_text="Chest", from_language='en', to_language=dest_lang)
        back = trans.translate_text(query_text="Back", from_language='en', to_language=dest_lang)
        legs = trans.translate_text(query_text="Legs", from_language='en', to_language=dest_lang)
        arms = trans.translate_text(query_text="Arms", from_language='en', to_language=dest_lang)
        butt = trans.translate_text(query_text="Butt", from_language='en', to_language=dest_lang)
        abs_ = trans.translate_text(query_text="Abs", from_language='en', to_language=dest_lang)
        muscle_mes = trans.translate_text(query_text='Choose a muscle group:', from_language='en',
                                          to_language=dest_lang)
        full = trans.translate_text(query_text="Full Body", from_language='en', to_language=dest_lang)
        lower = trans.translate_text(query_text="Lower Body", from_language='en', to_language=dest_lang)
        upper = trans.translate_text(query_text="Upper Body", from_language='en', to_language=dest_lang)
        workout_mes = trans.translate_text(query_text="Choose a workout:", from_language='en', to_language=dest_lang)
    else:
        chest = "Chest"
        back = "Back"
        legs = "Legs"
        arms = "Arms"
        butt = "Butt"
        abs_ = "Abs"
        muscle_mes = 'Choose a muscle group:'
        full = 'Full Body'
        lower = "Lower Body"
        upper = "Upper Body"
        workout_mes = "Choose a workout:"

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

    if dest_lang != 'en':
        proc_mes = trans.translate_text(query_text='Processing your request. This may take a couple of minutes...',
                                        from_language='en', to_language=dest_lang)
        feedback_mes = trans.translate_text(query_text='How did you like the workout plan?', from_language='en',
                                            to_language=dest_lang)
    else:
        proc_mes = 'Processing your request. This may take a couple of minutes...'
        feedback_mes = 'How was the workout plan?'

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
    # if dest_lang != 'en':
    #     workout_suggestion = trans.translate_text(query_text=workout_suggestion, from_language='en',
    #                                               to_language=dest_lang)
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
                             from_language='en',
                             to_language=dest_lang) if dest_lang != 'en' else "Thank you for your feedback! "
                                                                              "Redirecting to the main menu.")
    return await show_main_menu(update, context, query.message)


async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, message: Optional[Message] = None) -> int:
    # user_data = context.user_data
    user_data = get_user(update.effective_user.id)[-1]
    dest_lang = context.user_data['lang']
    if dest_lang != 'en':
        gender = trans.translate_text(query_text='Gender', from_language='en', to_language=dest_lang)
        height = trans.translate_text(query_text='Height', from_language='en', to_language=dest_lang)
        weight = trans.translate_text(query_text='Weight', from_language='en', to_language=dest_lang)
        steps = trans.translate_text(query_text='Steps per day', from_language='en', to_language=dest_lang)
        freq = trans.translate_text(query_text='Workout Frequency', from_language='en', to_language=dest_lang)
        tpw = trans.translate_text(query_text='times per week', from_language='en', to_language=dest_lang)
        wtype = trans.translate_text(query_text='Workout Type', from_language='en', to_language=dest_lang)
        kcal = trans.translate_text(query_text='kcal/day', from_language='en', to_language=dest_lang)
        return_butt = trans.translate_text(query_text='Return', from_language='en', to_language=dest_lang)
    else:
        gender = 'Gender'
        height = 'Height'
        weight = "Weight"
        steps = 'Steps per day'
        freq = 'Workout Frequency'
        tpw = 'times per week'
        wtype = 'Workout Type'
        kcal = 'kcal/day'
        return_butt = "Return"
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
    if dest_lang != 'en':
        cancel_mes = trans.translate_text(query_text="Bye! I hope we can talk again some day.", from_language='en',
                                          to_language=dest_lang)
    else:
        cancel_mes = "Bye! I hope we can talk again some day."
    await update.message.reply_text(cancel_mes, reply_markup=ReplyKeyboardRemove()
                                    )

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


def add_user_to_database(user_id, gender, height, weight, steps, workout_frequency, bmr, age):
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()

    cursor.execute(
        '''INSERT INTO users (user_id, gender, height, weight, steps, workout_frequency, bmr, age) VALUES (?, ?, ?, 
        ?, ?, ?, ?, ?)''',
        (user_id, gender, height, weight, steps, workout_frequency, bmr, age))

    connection.commit()
    connection.close()


def get_user(user_id):
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
    application = Application.builder().token("6668637502:AAEp-lxUpp2f3XKghLzeDSClw7ALZ6Ll0xY").build()

    create_database_and_table()

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
