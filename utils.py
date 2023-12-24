from config import dest_lang, supported_languages
from telegram import (
    Update)
from telegram.ext import (
    ContextTypes,
)
from user_data import save_user_data


def get_dest_lang(update: Update) -> str:
    """
    Determines the user's language preference based on their Telegram settings or defaults to English.
    """
    if update.message is None:
        return dest_lang
    dl = update.message.from_user.language_code
    if dl == '' or dl is None or dl not in supported_languages:
        dl = 'en'
    return dl


async def calculate_bmr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Calculates and saves the user's Basal Metabolic Rate (BMR) based on stored personal data.
    """
    # Assuming age is already collected and saved in user_data
    age = context.user_data.get('birth_dt')
    age = 2023 - int(age[0:4])
    gender = context.user_data.get('gender')
    height = float(str(context.user_data.get('height')).replace(',', '.'))
    weight = float(str(context.user_data.get('weight')).replace(',', '.'))

    if gender.lower() == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:  # Assuming female for any other input
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    context.user_data['bmr'] = int(bmr)
    save_user_data(update.effective_user.id, context.user_data)  # Save updated data to file
