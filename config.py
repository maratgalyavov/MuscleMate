import translators as trans
import openai

dest_lang = 'en'
supported_languages = trans.get_languages()

(
    MUSCLE_GROUP,
    INTENSITY,
    FEEDBACK,
    ASK_AGAIN,
    GENDER,
    HEIGHT,
    WEIGHT,
    STEPS,
    WORKOUT_FREQUENCY,
    WORKOUT_TYPE,
    MAIN_MENU,
    WORKOUT_AREA,
    USER_PROFILE,
    BMR,
    AGE,
    TRACKING,
    KCAL,
    CARDIO,
    LIFTING,
    STATS,
    COOKING,
    NUTRITION,
    PLAN
) = range(23)

openai.api_key = 'your_key'
telegram_key = "your_telegram_token"

USER_DATA_FILE = "user_data.json"
