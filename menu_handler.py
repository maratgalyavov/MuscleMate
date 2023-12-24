from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import ContextTypes, CallbackQueryHandler
import translators as trans

import config
from profile_handler import user_profile


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, message: Optional[Message] = None) -> int:
    query = update.callback_query
    dest_lang = context.user_data['lang']
    calorie_button = trans.translate_text(query_text="Activity Tracking", translator='google', to_language=dest_lang)
    workout_button = trans.translate_text(query_text="Workouts", translator='google', to_language=dest_lang)
    user_button = trans.translate_text(query_text="User Profile", translator='google', to_language=dest_lang)
    stats_button = trans.translate_text(query_text="Stats", translator='google', to_language=dest_lang)
    nutrition_button = trans.translate_text(query_text="Nutrition", translator='google', to_language=dest_lang)
    main_menu = trans.translate_text(query_text="Main Menu:", translator='google', to_language=dest_lang)
    funding_button = trans.translate_text(query_text="Support the developers", translator='google', to_language=dest_lang)
    keyboard = [
        [InlineKeyboardButton(calorie_button, callback_data='tracking')],
        [InlineKeyboardButton(workout_button, callback_data='workouts')],
        [InlineKeyboardButton(user_button, callback_data='user_profile')],
        [InlineKeyboardButton(stats_button, callback_data='stats')],
        [InlineKeyboardButton(nutrition_button, callback_data='nutrition')],
        [InlineKeyboardButton(funding_button, url='https://www.tinkoff.ru/cf/3mvrQU4wHFX')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if message:
        mes = await message.reply_text(main_menu, reply_markup=reply_markup)
    elif query:
        mes = await query.message.reply_text(main_menu, reply_markup=reply_markup)
    else:
        mes = await update.message.reply_text(main_menu, reply_markup=reply_markup)

    return config.MAIN_MENU


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
        return config.TRACKING
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
        return config.WORKOUT_AREA
    elif choice == 'user_profile':
        return await user_profile(update, context, query.message)
    elif choice == 'stats':
        steps = trans.translate_text(query_text='Steps', translator='google', to_language=dest_lang)
        weight = trans.translate_text(query_text='Weight', translator='google', to_language=dest_lang)
        workouts = trans.translate_text(query_text='Workouts', translator='google', to_language=dest_lang)
        kcal = trans.translate_text(query_text='Calories', translator='google', to_language=dest_lang)
        mes = trans.translate_text(query_text='Statistics for which parameter you would like to see?',
                                   translator='google', to_language=dest_lang)
        stats_keyboard = [
            [InlineKeyboardButton(steps, callback_data='steps'),
             InlineKeyboardButton(weight, callback_data='weight')],
            [InlineKeyboardButton(workouts, callback_data='workouts'),
             InlineKeyboardButton(kcal, callback_data='kcal')]
        ]
        stats_markup = InlineKeyboardMarkup(stats_keyboard)
        await query.message.reply_text(mes, reply_markup=stats_markup)
        return config.STATS
    elif choice == 'nutrition':
        planning_button = trans.translate_text(query_text="Meal Planning", translator='google',
                                             to_language=dest_lang)
        counting_button = trans.translate_text(query_text="Calorie counting", translator='google',
                                               to_language=dest_lang)
        nutrition_mes = trans.translate_text(query_text="What are you looking for?", translator='google',
                                                to_language=dest_lang)
        nutrition_keyboard = [
            [InlineKeyboardButton(planning_button, callback_data='meal_planning'),
             InlineKeyboardButton(counting_button, callback_data='calorie_counting')]
        ]
        nutrition_markup = InlineKeyboardMarkup(nutrition_keyboard)
        await query.message.reply_text(nutrition_mes + ":", reply_markup=nutrition_markup)
        return config.NUTRITION
    return config.MAIN_MENU  # Remain in MAIN_MENU state for unrecognized choices
