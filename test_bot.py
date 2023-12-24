import pytest
from telegram import Update
from unittest.mock import MagicMock

from main import load_user_data, save_user_data, get_dest_lang, show_main_menu, main_menu_callback, tracking_callback, \
    kcal_callback, cardio_callback, lifting_callback, start, gender_callback, age_callback, height_callback, \
    weight_callback, steps_callback, workout_frequency_callback, workout_type_callback, muscle_group_callback, \
    workout_area_callback, intensity_callback, feedback_callback, user_profile, user_profile_callback, calculate_bmr, \
    cancel, create_database_and_table, add_user_to_database, get_user, get_workouts


@pytest.fixture
def update_mock():
    return MagicMock()


@pytest.fixture
def context_mock():
    return MagicMock()


@pytest.fixture
def user_data_fixture():
    return {'lang': 'en', 'gender': 'male', 'birth_dt': '1990-01-01', 'height': 180, 'weight': 70}


def test_start(update_mock, context_mock, user_data_fixture):
    with pytest.raises(Exception):
        result = start(update_mock, context_mock)
        assert result == 10 or result == 4
