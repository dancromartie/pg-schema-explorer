"""
Functions for fixing orphaned columns,
i.e. columns that no longer exist upstream as we last knew them
"""

import sys

import util


def autoselect_column():
    """
    Automatically selects an orphaned column for fixing
    """
    util.cursor.execute("""
        SELECT * FROM columns
        WHERE orphaned ORDER BY RANDOM()
        LIMIT 1
    """)
    row = util.cursor.fetchone()
    return row


def handle_orphaned_column():
    """
    Selects a column for fixing and walks the user through options
    """
    orphaned_row = autoselect_column()
    if not orphaned_row:
        print("No orphaned columns found")
        sys.exit(0)

    print("Orphaned column: %s" % orphaned_row)
    print("What would you like to do?")
    while True:
        user_response = input("(r=rename, d=delete, t=transfer)")
        if user_response in "rdt":
            break

    if user_response == "r":
        new_column_name = input("What's the new column name? ")
        # Update record for column
        util.cursor.execute("""
            UPDATE columns SET column_name = %s
            WHERE table_name = %s AND table_schema = %s
        """, (new_column_name, orphaned_row["table_name"], orphaned_row["table_schema"]))
        util.db_conn.commit()


        util.db_conn.commit()
    elif user_response == "d":
        # Delete record for table
        delete_query = """
            DELETE FROM columns
            WHERE table_name = %s AND table_schema = %s AND column_name = %s
        """
        util.cursor.execute(
            delete_query, (
                orphaned_row["table_name"],
                orphaned_row["table_schema"],
                orphaned_row["column_name"]))

        util.db_conn.commit()
