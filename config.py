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

openai.api_key = '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'
telegram_key = "6668637502:AAEp-lxUpp2f3XKghLzeDSClw7ALZ6Ll0xY"
USER_DATA_FILE = "user_data.json"
