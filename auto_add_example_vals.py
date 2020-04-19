"""
Adds examples values to columns table by sampling, ranking, and selecting a range
from ranked values.
"""

import argparse
import time

import util


def autoselect_column():
    """Find a record from columns table without example values"""
    util.cursor.execute("""
        SELECT * FROM columns
        WHERE table_name != 'tables'
        AND example_vals IS NULL
        ORDER BY table_name, column_name
        LIMIT 1
    """)
    row = util.cursor.fetchone()
    return row


def get_examples(schema, table, column):
    """Sample, rank, keep a few spaced-out items from ranked list"""
    util.cursor.execute(f"""
        WITH first_sample AS (
            SELECT coalesce({column}::text, 'NULL') AS val
            FROM {schema}.{table} TABLESAMPLE SYSTEM (10)
            LIMIT 10000
        ),
        ranked AS (
            SELECT val, count(1), row_number() OVER (ORDER BY count(1) DESC) AS rnk
            FROM first_sample
            GROUP BY val
        )
        SELECT * FROM ranked ORDER BY rnk
    """)
    sampled_vals = []
    for row in util.cursor.fetchall():
        raw_val = str(row['val'])
        final_val = raw_val
        if len(raw_val) > 80:
            final_val = raw_val[0:80] + '...[truncated]'
        sampled_vals.append(final_val)

    if len(sampled_vals) <= 5:
        return sampled_vals
    if len(sampled_vals) < 10:
        return sampled_vals[0:4] + [sampled_vals[-1]]

    return [
        sampled_vals[0], sampled_vals[2], sampled_vals[4], sampled_vals[6], sampled_vals[8]]


def set_examples(schema, table, column, vals):
    """Update the example_vals column"""
    column_string = " ; ".join(vals)
    util.cursor.execute(f"""
        UPDATE columns SET example_vals = %s
        WHERE table_schema = %s AND table_name = %s AND column_name = %s
    """, (column_string, schema, table, column))
    util.db_conn.commit()


def main():
    """main"""
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--no-confirmation", action="store_true")
    cli_args = argument_parser.parse_args()

    while True:
        col_row = autoselect_column()
        if not col_row:
            break
        print("*" * 40)
        print("Getting sample vals for %s.%s" % (col_row["table_name"], col_row["column_name"]))
        sampled_vals = get_examples(
            col_row["table_schema"], col_row["table_name"], col_row["column_name"])
        print("Sampled vals are:", sampled_vals)
        user_response = None
        if not cli_args.no_confirmation:
            user_response = input("Use sample values? (y/n)")
        if user_response == "y" or cli_args.no_confirmation:
            print("Updating DB...")
            set_examples(
                col_row["table_schema"],
                col_row["table_name"],
                col_row["column_name"],
                sampled_vals)
        else:
            print("skipping this column at user's request.")
            print(
                "to avoid being asked about this column again, " +
                "fill it manually with the example values of your choice")

        time.sleep(.1)


if __name__ == "__main__":
    main()
