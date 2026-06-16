import database

def add_candy(user_id, candy_type, amount=1):

    conn = database.get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO user_candies (
                user_id,
                candy_type,
                amount
            )
            VALUES (%s, %s, %s)

            ON CONFLICT (
                user_id,
                candy_type
            )

            DO UPDATE SET
                amount = user_candies.amount + EXCLUDED.amount
            """,
            (
                str(user_id),
                candy_type,
                amount
            )
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()
def add_candy_for_pokemon(user_id, pokemon_nombre, amount=1):

    conn = database.get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT tipos
            FROM pokemon_data
            WHERE nombre = %s
            """,
            (pokemon_nombre.lower(),)
        )

        row = cursor.fetchone()

        if not row:
            return

        tipo_primario = row[0].split(",")[0]

        add_candy(
            user_id,
            tipo_primario,
            amount
        )

    finally:
        cursor.close()
        conn.close()
def get_candies(user_id):

    conn = database.get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            SELECT candy_type, amount
            FROM user_candies
            WHERE user_id = %s
            """,
            (str(user_id),)
        )

        return {
            candy_type: amount
            for candy_type, amount in cursor.fetchall()
        }

    finally:
        cursor.close()
        conn.close()
def remove_candy(user_id, candy_type, amount):

    conn = database.get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            UPDATE user_candies
            SET amount = amount - %s
            WHERE user_id = %s
            AND candy_type = %s
            """,
            (
                amount,
                str(user_id),
                candy_type
            )
        )

        conn.commit()

    finally:
        cursor.close()
        conn.close()