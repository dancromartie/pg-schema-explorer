"""
Functions for fixing orphaned tables,
i.e. tables that no longer exist upstream as we last knew them.
"""

import sys

import util


def autoselect_table():
    """
    Find a random orphaned table
    """
    util.cursor.execute("""
        SELECT * FROM tables
        WHERE orphaned ORDER BY RANDOM()
        LIMIT 1
    """)
    row = util.cursor.fetchone()
    return row


def handle_orphaned_table():
    """
    Select an orphaned table, and walk the user through options for fixing.
    """
    orphaned_row = autoselect_table()
    if not orphaned_row:
        print("No orphaned tables found")
        sys.exit(0)

    print("Orphaned table: %s" % orphaned_row)
    print("What would you like to do?")
    while True:
        user_response = input("(r=rename, d=delete, t=transfer)")
        if user_response in "rdt":
            break

    if user_response == "r":
        new_table_name = input("What's the new table name? ")
        # Update record for table
        util.cursor.execute("""
            UPDATE tables SET table_name = %s
            WHERE table_name = %s AND table_schema = %s
        """, (new_table_name, orphaned_row["table_name"], orphaned_row["table_schema"]))
        # Update records for columns
        util.cursor.execute("""
            UPDATE columns SET table_name = %s
            WHERE table_name = %s AND table_schema = %s
        """, (new_table_name, orphaned_row["table_name"], orphaned_row["table_schema"]))
        util.db_conn.commit()


        util.db_conn.commit()
    elif user_response == "d":
        # Delete record for table
        util.cursor.execute("""
            DELETE FROM tables
            WHERE table_name = %s AND table_schema = %s
        """, (orphaned_row["table_name"], orphaned_row["table_schema"]))
        # Delete records for columns
        util.cursor.execute("""
            DELETE FROM columns
            WHERE table_name = %s AND table_schema = %s
        """, (orphaned_row["table_name"], orphaned_row["table_schema"]))

        util.db_conn.commit()
