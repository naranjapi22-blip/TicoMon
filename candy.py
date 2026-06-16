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