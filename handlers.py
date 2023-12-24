from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup)
from telegram.ext import (
    ContextTypes,
)

import config
from config import *
import translators as trans

from menu_handler import show_main_menu
from user_data import save_user_data, load_user_data
from db import add_user_to_database, add_record, get_user, get_stats
from utils import calculate_bmr, get_dest_lang


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from main import logger
    user = update.message.from_user
    dest_lang = get_dest_lang(update)
    logger.info(f"User {user.id} started the conversation.")
    context.user_data.update(load_user_data(user.id))
    context.user_data['lang'] = dest_lang
    user_data = await get_user(user.id)
    if len(user_data) == 0:
        start_mes = trans.translate_text(
            query_text="Let\'s start by collecting some information.\nWhat is your gender?",
            translator='google', to_language=dest_lang)

        male = trans.translate_text(query_text='Male', translator='google', to_language=dest_lang)
        female = trans.translate_text(query_text='Female', translator='google', to_language=dest_lang)
        start_keyboard = [
            [InlineKeyboardButton(male, callback_data='male'), InlineKeyboardButton(female, callback_data='female')]
        ]
        start_markup = InlineKeyboardMarkup(start_keyboard)
        await update.message.reply_text(start_mes, reply_markup=start_markup)
        return config.GENDER  # Transition to GENDER state
    else:
        return await show_main_menu(update, context)


async def gender_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from main import logger
    query = update.callback_query
    choice = query.data
    user = query.from_user
    logger.info(f"Gender of {user.id}: {choice}")
    context.user_data['gender'] = choice
    dest_lang = context.user_data['lang']
    age_mes = trans.translate_text(query_text="What is your birth date in format dd.mm.yyyy?", translator='google',
                                   to_language=dest_lang)
    await query.message.reply_text(age_mes)
    return AGE


async def age_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from main import logger
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    age = update.message.text
    invalid_age_mes = trans.translate_text(query_text="Please enter a valid date in a required format",
                                           translator='google', to_language=dest_lang)
    height_mes = trans.translate_text(query_text="What is your height in cm?", translator='google',
                                      to_language=dest_lang)
    try:
        age = age.split('.')  # Make sure age is a valid number
        if 1920 < int(age[2]) < 2020:  # Sanity check for age
            logger.info(f"Birth date of {user.id}: {'.'.join(age)}")
            context.user_data['birth_dt'] = age[2] + '-' + age[1] + '-' + age[0]
            await update.message.reply_text(height_mes)
            return HEIGHT
        else:
            await update.message.reply_text(invalid_age_mes)
            return AGE  # Repeat the AGE state if the input is not valid
    except ValueError or IndexError:
        await update.message.reply_text(invalid_age_mes)
        return AGE


async def height_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from main import logger
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    height = update.message.text
    invalid_height_mes = trans.translate_text(query_text="Please enter a valid height.", translator='google',
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
    from main import logger
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    weight = update.message.text
    invalid_weight_mes = trans.translate_text(query_text="Please enter a valid weight.", translator='google',
                                              to_language=dest_lang)
    menu_mes = trans.translate_text(query_text='Redirecting to main menu', translator='google', to_language=dest_lang)
    try:
        weight = float(weight)
        if 30 < weight < 200:
            logger.info(f"Weight of {user.id}: {weight}")
            context.user_data['weight'] = weight
            save_user_data(user.id, context.user_data)
            user_data = context.user_data
            await add_user_to_database(user.id, user_data['gender'], user_data['birth_dt'], user_data['height'],
                                       user_data['weight'])
            await update.message.reply_text(menu_mes)
            return await show_main_menu(update, context)
        else:
            await update.message.reply_text(invalid_weight_mes)
            return WEIGHT
    except ValueError:
        await update.message.reply_text(invalid_weight_mes)
        return WEIGHT


async def workout_frequency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from main import logger
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
        return config.WORKOUT_FREQUENCY
    await update.message.reply_text(type_workout_mes)
    return config.WORKOUT_TYPE


async def workout_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from main import logger
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
