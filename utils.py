from config import dest_lang, supported_languages
from telegram import (
    Update)
from telegram.ext import (
    ContextTypes,
)
from user_data import save_user_data


def get_dest_lang(update: Update) -> str:
    if update.message is None:
        return dest_lang
    dl = update.message.from_user.language_code
    if dl == '' or dl is None or dl not in supported_languages:
        dl = 'en'
    return dl


async def calculate_bmr(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
