import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

from db import create_database_and_table, add_user_to_database, add_record, get_user, get_workouts, get_stats
from handlers import gender_callback, age_callback, height_callback, weight_callback, start, workout_frequency_callback, \
    workout_type_callback
from activity import tracking_callback, kcal_callback, cardio_callback, lifting_callback, steps_callback, stats_callback
import config
from menu_handler import main_menu_callback, show_main_menu
from nutrition import nutrition_callback, plan_callback, counting_callback
from profile_handler import user_profile_callback
from workouts import muscle_group_callback, feedback_callback, intensity_callback, workout_area_callback, cancel

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

handler = logging.FileHandler(filename='MuscleMate.log', mode='a')
logger = logging.getLogger(__name__)
logger.addHandler(handler)


def main() -> None:
    application = Application.builder().token(config.telegram_key).build()  # нужный
    # application = Application.builder().token("6520497677:AAH2QjNPwcqvYA558rJsSHOBW-RIDK6HX3Y").build()

    create_database_and_table()
    # print(get_stats(626846493, 'workouts'))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            config.MAIN_MENU: [
                CallbackQueryHandler(main_menu_callback, pattern='^(tracking|workouts|user_profile|stats|nutrition)$')],
            config.GENDER: [CallbackQueryHandler(gender_callback, pattern='^(male|female)$')],
            config.HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, height_callback)],
            config.WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, weight_callback)],
            config.STEPS: [MessageHandler(filters.TEXT & ~filters.COMMAND, steps_callback)],
            config.WORKOUT_FREQUENCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, workout_frequency_callback)],
            config.WORKOUT_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, workout_type_callback)],
            config.MUSCLE_GROUP: [CallbackQueryHandler(muscle_group_callback,
                                                       pattern='^(chest|back|legs|arms|butt|abs|full_body|upper_body'
                                                               '|lower_body)$')],
            config.INTENSITY: [CallbackQueryHandler(intensity_callback, pattern='^(low|medium|high)$')],
            config.FEEDBACK: [CallbackQueryHandler(feedback_callback, pattern='^(good|bad)$')],
            config.WORKOUT_AREA: [
                CallbackQueryHandler(workout_area_callback, pattern='^(single_muscle_group|compound)$')],
            config.USER_PROFILE: [CallbackQueryHandler(user_profile_callback, pattern='^return$')],
            config.AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age_callback)],
            config.TRACKING: [
                CallbackQueryHandler(tracking_callback, pattern='^(kcal|steps|cardio|lifting|burnt_kcal|return)$')],
            config.KCAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, kcal_callback)],
            config.CARDIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, cardio_callback)],
            config.LIFTING: [MessageHandler(filters.TEXT & ~filters.COMMAND, lifting_callback)],
            config.STATS: [CallbackQueryHandler(stats_callback, pattern='^(steps|weight|workouts|kcal)$')],
            config.NUTRITION: [CallbackQueryHandler(nutrition_callback, pattern='^(meal_planning|calorie_counting)$')],
            config.PLAN: [CallbackQueryHandler(plan_callback, pattern='^(1|3|5|7)$')],
            config.COOKING: [MessageHandler(filters.TEXT & ~filters.COMMAND, counting_callback)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
