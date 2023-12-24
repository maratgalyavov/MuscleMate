import pytest
# from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, User
from unittest.mock import MagicMock, AsyncMock, patch, ANY
import json
# from sqlalchemy import create_engine
import sqlite3
import os
from telegram.ext import ConversationHandler

# import config
# import matplotlib.pyplot as plt
# import seaborn as sns

from user_data import load_user_data, save_user_data
from utils import get_dest_lang, calculate_bmr
from profile_handler import user_profile, user_profile_callback
from menu_handler import show_main_menu, main_menu_callback
from handlers import age_callback, gender_callback, start, height_callback, weight_callback, workout_frequency_callback, workout_type_callback
from activity import tracking_callback, kcal_callback, cardio_callback, lifting_callback, steps_callback, stats_callback
from nutrition import nutrition_callback, cancel
from workouts import muscle_group_callback, feedback_callback, intensity_callback, workout_area_callback
from db import create_database_and_table, add_user_to_database, get_user, get_workouts, get_stats, add_record


USER_DATA_FILE = "user_data_test.json"
MUSCLE_GROUP, INTENSITY, FEEDBACK, ASK_AGAIN = range(4)
GENDER, HEIGHT, WEIGHT, STEPS = range(4, 8)
WORKOUT_FREQUENCY, WORKOUT_TYPE = range(8, 10)
MAIN_MENU = 10
WORKOUT_AREA = 11
USER_PROFILE, BMR = range(12, 14)
AGE = 14
TRACKING = 15
KCAL, CARDIO, LIFTING = range(16, 19)
STATS = 19

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


def test_load_user_data(update_mock, context_mock, user_data_fixture):
    with open(USER_DATA_FILE, "w") as f:
        json.dump({"1": user_data_fixture}, f)
    update_mock.message.from_user.id = 1
    context_mock.user_data = {"user_id": 1}
    result = load_user_data(1)
    assert result == user_data_fixture


def test_save_user_data(update_mock, context_mock, user_data_fixture):
    update_mock.message.from_user.id = 1
    context_mock.user_data = {"user_id": 1}
    save_user_data(1, user_data_fixture)
    loaded_data = load_user_data(1)
    assert loaded_data == user_data_fixture


def test_get_dest_lang(update_mock):
    result = get_dest_lang(update_mock)
    assert result == 'en'
    update_mock.message.from_user.language_code = 'unavailable_lang'
    result = get_dest_lang(update_mock)
    assert result == 'en'
    update_mock.message.from_user.language_code = None
    result = get_dest_lang(update_mock)
    assert result == 'en'


class FakeTranslator:
    @staticmethod
    async def translate_text(query_text, translator, to_language):
        return f"Translated: {query_text}"


@pytest.mark.asyncio
async def test_main_menu_callback_tracking_choice(update_mock, context_mock):
    update_mock.callback_query.data = 'tracking'
    context_mock.user_data = {'lang': 'en'}

    async def mock_reply_text(mes, reply_markup):
        return None

    update_mock.callback_query.message.reply_text = AsyncMock(side_effect=mock_reply_text)
    context_mock.bot.send_message = AsyncMock(side_effect=mock_reply_text)

    result = await main_menu_callback(update_mock, context_mock)
    update_mock.callback_query.message.reply_text.assert_called_once()

    assert result == TRACKING

@pytest.mark.asyncio
async def test_main_menu_callback_workouts_choice(update_mock, context_mock):
    update_mock.callback_query.data = 'workouts'
    context_mock.user_data = {'lang': 'en'}

    async def mock_reply_text(mes, reply_markup):
        return None

    update_mock.callback_query.message.reply_text = AsyncMock(side_effect=mock_reply_text)

    result = await main_menu_callback(update_mock, context_mock)
    update_mock.callback_query.message.reply_text.assert_called_once()

    assert result == WORKOUT_AREA


@pytest.fixture
def test_db_path():
    return 'users.db'


def test_create_database_and_table(test_db_path):
    create_database_and_table()

    assert os.path.exists(test_db_path)

    connection = sqlite3.connect(test_db_path)
    cursor = connection.cursor()
    cursor.execute("PRAGMA table_info(users);")
    columns_users = cursor.fetchall()

    assert len(columns_users) == 6
    assert columns_users[0][1] == 'user_id'
    assert columns_users[1][1] == 'gender'
    assert columns_users[2][1] == 'birth_dt'
    assert columns_users[3][1] == 'height'
    assert columns_users[4][1] == 'weight'

    cursor.execute("PRAGMA table_info(tracking);")
    columns_tracking = cursor.fetchall()

    assert len(columns_tracking) == 4
    assert columns_tracking[0][1] == 'user_id'
    assert columns_tracking[1][1] == 'date'
    assert columns_tracking[2][1] == 'type'
    assert columns_tracking[3][1] == 'value'

    connection.close()


@pytest.mark.asyncio
async def test_user_profile_callback_other(update_mock, context_mock):
    update_mock.callback_query.data = 'some_choice'
    result = await user_profile_callback(update_mock, context_mock)
    assert result == USER_PROFILE


@pytest.fixture
def connection_mock():
    return MagicMock()

@pytest.mark.asyncio
async def test_add_user_to_database(connection_mock):
    user_id = 123
    gender = 'male'
    birth_dt = '1990-01-01'
    height = 180
    weight = 70
    bmr = 0

    with patch('sqlite3.connect', new_callable=MagicMock) as mock_connect:
        mock_cursor = MagicMock()
        mock_execute = MagicMock()
        mock_cursor.execute.side_effect = mock_execute
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor

        await add_user_to_database(user_id, gender, birth_dt, height, weight, bmr)

    mock_connect.assert_called_once_with('users.db')


@pytest.fixture
def connection_mock():
    return MagicMock()

@pytest.mark.asyncio
async def test_add_record(connection_mock):
    user_id = 123
    record_type = 'some_type'
    value = 42

    with patch('sqlite3.connect', new_callable=MagicMock) as mock_connect:
        mock_cursor = MagicMock()
        mock_execute = MagicMock()
        mock_cursor.execute.side_effect = mock_execute
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor

        await add_record(user_id, record_type, value)

    mock_connect.assert_called_once_with('users.db')

    mock_cursor.execute(
        '''INSERT INTO tracking (user_id, date, type, value) VALUES (?, date('now'), ?, ?)''',
        (user_id, record_type, value)
    )


@pytest.fixture
def connection_mock():
    return MagicMock()

@pytest.mark.asyncio
async def test_get_user(connection_mock):
    user_id = 123

    with patch('sqlite3.connect', new_callable=MagicMock) as mock_connect:
        mock_cursor = MagicMock()
        mock_execute = MagicMock()
        mock_cursor.execute.side_effect = mock_execute
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor

        result = await get_user(user_id)

    mock_connect.assert_called_once_with('users.db')
    mock_cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))



@pytest.fixture
def connection_mock():
    return MagicMock()

@pytest.mark.asyncio
async def test_get_workouts(connection_mock):
    user_id = 123

    with patch('sqlite3.connect', new_callable=MagicMock) as mock_connect:
        mock_cursor = MagicMock()
        mock_execute = MagicMock()
        mock_cursor.execute.side_effect = mock_execute
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor

        result = await get_workouts(user_id)

    mock_connect.assert_called_once_with('users.db')

    mock_cursor.execute(
        "SELECT sum(value) FROM tracking WHERE user_id=? and type='cardio' and date=date('now')", (user_id,)
    )

    mock_cursor.execute(
        "SELECT sum(value) FROM tracking WHERE user_id=? and type='lifting' and date=date('now')", (user_id,)
    )


@pytest.fixture
def connection_mock():
    return MagicMock()


@pytest.mark.asyncio
async def test_get_stats(connection_mock):
    user_id = 123
    choice = 'some_choice'

    with patch('sqlite3.connect', new_callable=MagicMock) as mock_connect:
        mock_cursor = MagicMock()
        mock_execute = MagicMock()
        mock_cursor.execute.side_effect = mock_execute
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor

        result = await get_stats(user_id, choice)
    mock_connect.assert_called_once_with('users.db')

    mock_cursor.execute(
        "SELECT date, sum(value) FROM tracking WHERE user_id=? and type=? GROUP BY date", (user_id, choice)
    )


@pytest.mark.asyncio
async def test_calculate_bmr(context_mock, update_mock):
    context_mock.user_data = {
        'birth_dt': '1990-01-01',
        'gender': 'male',
        'height': 180,
        'weight': 70
    }

    with patch('user_data.save_user_data') as mock_save_user_data:
        await calculate_bmr(update_mock, context_mock)

    mock_save_user_data(update_mock.effective_user.id, context_mock.user_data)

    assert 'bmr' in context_mock.user_data
    assert isinstance(context_mock.user_data['bmr'], int)


@pytest.mark.asyncio
async def test_cancel():
    context_mock = AsyncMock()
    update_mock = AsyncMock()
    message_mock = AsyncMock()

    user_id = 123
    dest_lang = 'en'
    context_mock.user_data = {'lang': dest_lang}
    update_mock.message.from_user.id = user_id

    with patch('main.logger') as mock_logger:
        with patch('telegram.Message.reply_text') as mock_reply_text:
            result = await cancel(update_mock, context_mock)

    mock_logger.info.assert_called_once_with(f"User {user_id} canceled the conversation.")

    assert result == ConversationHandler.END
