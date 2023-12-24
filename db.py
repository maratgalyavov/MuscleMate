import sqlite3


def create_database_and_table():
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            gender TEXT,
            birth_dt DATE,
            height INTEGER,
            weight INTEGER
        )
    ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracking (
                user_id INTEGER,
                date DATE,
                type TEXT,
                value REAL
            )
        ''')

    connection.commit()
    connection.close()


async def add_user_to_database(user_id, gender, birth_dt, height, weight):
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()

    cursor.execute(
        '''INSERT INTO users (user_id, gender, birth_dt, height, weight) VALUES (?, ?, ?, ?, ?)''',
        (user_id, gender, birth_dt, height, weight))

    connection.commit()
    connection.close()


async def add_record(user_id, type, value):
    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()

    cursor.execute(
        '''INSERT INTO tracking (user_id, date, type, value) VALUES (?, date('now'), ?, ?)''',
        (user_id, type, value))

    connection.commit()
    connection.close()


async def get_user(user_id) -> list or None:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_data = cursor.fetchall()
    conn.close()

    res = list()
    if user_data is not None:
        for user in user_data:
            keys = (
                'user_id', 'gender', 'birth_dt', 'height', 'weight'
            )
            res.append(dict(zip(keys, user)))
        return res
    return None


async def get_workouts(user_id) -> list:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT sum(value) FROM tracking WHERE user_id=? and type='cardio' and date=date('now')", (user_id,))
    cardio = cursor.fetchone()
    cursor.execute("SELECT sum(value) FROM tracking WHERE user_id=? and type='lifting' and date=date('now')",
                   (user_id,))
    lifting = cursor.fetchone()
    conn.close()
    if cardio is None:
        cardio = [0]
    if lifting is None:
        lifting = [0]
    return [cardio[0], lifting[0]]


async def get_stats(user_id, choice):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    if choice == 'workouts':
        cursor.execute(
            "SELECT date, sum(value) FROM tracking WHERE user_id=? and (type='cardio' or type='lifting') GROUP BY date",
            (user_id,))
    else:
        cursor.execute("SELECT date, sum(value) FROM tracking WHERE user_id=? and type=? GROUP BY date",
                       (user_id, choice))
    tuples = cursor.fetchall()
    dates = list()
    values = list()
    for d, v in tuples:
        dates.append(d)
        values.append(v)
    return [dates, values]
