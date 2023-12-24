from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

import config
from db import add_user_to_database, get_user
import translators as trans


async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, message: Optional[Message] = None) -> int:
    # user_data = context.user_data
    user_data = (await get_user(update.effective_user.id))[-1]
    dest_lang = context.user_data['lang']
    gender = trans.translate_text(query_text='Gender', translator='google', to_language=dest_lang)
    height = trans.translate_text(query_text='Height', translator='google', to_language=dest_lang)
    weight = trans.translate_text(query_text='Weight', translator='google', to_language=dest_lang)
    birth_dt = trans.translate_text(query_text='Date of birth', translator='google', to_language=dest_lang)
    return_butt = trans.translate_text(query_text='Return', translator='google', to_language=dest_lang)
    profile_info = (
        f"{gender}: {user_data['gender']}\n"
        f"{height}: {user_data['height']} cm\n"
        f"{weight}: {user_data['weight']} kg\n"
        f"{birth_dt}: {user_data['birth_dt']}\n"
        # f"{freq}: {user_data['workout_frequency']} "
        # f"{tpw}\n"
        # f"{wtype}: {user_data['workout_type']}\n"
        # f"BMR: {user_data['bmr']} {kcal}"
    )
    keyboard = [
        [InlineKeyboardButton(return_butt,
                              callback_data='return')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if message:
        await message.reply_text(profile_info, reply_markup=reply_markup)
    else:
        await update.message.reply_text(profile_info, reply_markup=reply_markup)
    return config.USER_PROFILE


async def user_profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    from menu_handler import show_main_menu
    query = update.callback_query
    choice = query.data
    if choice == 'return':
        return await show_main_menu(update, context, query.message)
    return config.USER_PROFILE
