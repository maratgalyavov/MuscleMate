from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from config import TRACKING, KCAL, CARDIO, LIFTING, STATS, STEPS
from utils import get_dest_lang
from db import add_record, get_workouts, get_stats
import translators as trans
from menu_handler import show_main_menu
from random import randint
import seaborn as sns
import matplotlib.pyplot as plt
import os


async def tracking_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user = query.from_user
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
    elif choice == 'cardio':
        mes = trans.translate_text(query_text='How long was your workout in minutes?', translator='google',
                                   to_language=dest_lang)
        await query.message.reply_text(mes)
        return CARDIO
    elif choice == 'lifting':
        mes = trans.translate_text(query_text='How long was your workout in minutes?', translator='google',
                                   to_language=dest_lang)
        await query.message.reply_text(mes)
        return LIFTING
    elif choice == 'burnt_kcal':
        cardio, lifting = await get_workouts(user.id)
        kcal = cardio * 500 / 60 + lifting * 5 + randint(-25, 26)
        mes = trans.translate_text(query_text=f'Today you burnt {kcal} kcal', translator='google',
                                   to_language=dest_lang)
        await query.message.reply_text(mes)
        return await show_main_menu(update, context)


async def kcal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    kcal = update.message.text
    kcal = int(kcal)
    await add_record(user.id, 'kcal', kcal)
    mes = trans.translate_text(query_text='Calories added successfully. Returning to main menu.',
                               translator='google', to_language=dest_lang)
    await update.message.reply_text(mes)
    return await show_main_menu(update, context)


async def cardio_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    minutes = update.message.text
    minutes = int(minutes)
    await add_record(user.id, 'cardio', minutes)
    mes = trans.translate_text(query_text='Workout added successfully. Returning to main menu.',
                               translator='google', to_language=dest_lang)
    await update.message.reply_text(mes)
    return await show_main_menu(update, context)


async def lifting_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    minutes = update.message.text
    minutes = int(minutes)
    await add_record(user.id, 'lifting', minutes)
    mes = trans.translate_text(query_text='Workout added successfully. Returning to main menu.',
                               translator='google', to_language=dest_lang)
    await update.message.reply_text(mes)
    return await show_main_menu(update, context)


async def steps_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    dest_lang = context.user_data['lang']
    steps = update.message.text
    steps = int(steps)
    await add_record(user.id, 'steps', steps)
    mes = trans.translate_text(query_text='Steps added successfully. Returning to the main menu.',
                               translator='google', to_language=dest_lang)
    await update.message.reply_text(mes)
    return await show_main_menu(update, context)


async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user = query.from_user
    dest_lang = context.user_data['lang']
    choice = query.data
    dates, values = await get_stats(user.id, choice)
    if not os.path.exists("images"):
        os.mkdir("images")
    sns.set_theme()
    fig = sns.lineplot(x=dates, y=values)
    plt.xlabel("Dates")
    plt.ylabel("Values")
    plt.title(f"Dynamics of {choice}")
    plt.xticks(rotation=45)
    plt.savefig(f"images/fig_{user.id}.png")
    plt.figure().clear()
    await context.bot.sendPhoto(user.id, f"images/fig_{user.id}.png")
    return await show_main_menu(update, context)
