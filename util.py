"""
import sys
Utils, database connection stuff
"""

import json
import os
import re
import subprocess

import psycopg2
import psycopg2.extras


class NoSuchTableOrColError(Exception):
    """
    Exception for when an unknown table/column is requested
    """
    pass # pylint: disable=unnecessary-pass


def get_record_from_name(name):
    """
    Get record from tables table or columns table, depending on where we find matches.
    """
    results = []
    object_type = None

    if name.count(".") == 0:
        # Must be a table
        object_type = "table"
        cursor.execute("SELECT * FROM tables WHERE table_name = %s", (name,))
        results = list(cursor.fetchall())
    elif name.count(".") == 2:
        # Must be a column
        object_type = "column"
        left, middle, right = name.split(".")
        cursor.execute("""
            SELECT * FROM columns
            WHERE table_schema = %s
            AND table_name = %s
            AND column_name = %s
        """, (left, middle, right))
        results = list(cursor.fetchall())
    elif name.count(".") == 1:
        # Could be a table or column
        left, right = name.split(".")
        # Check for tables
        cursor.execute(
            "SELECT * FROM tables WHERE table_schema = %s and table_name = %s", (left, right))
        results = list(cursor.fetchall())
        if results:
            object_type = "table"
        else:
            # Check for columns
            object_type = "column"
            cursor.execute(
                "SELECT * FROM columns WHERE table_name = %s and column_name = %s", (left, right))
            results = list(cursor.fetchall())

    if not results:
        raise NoSuchTableOrColError("Couldn't find any object using name %s" % name)

    to_return = results[0]
    assert object_type in ("table", "column")
    return to_return, object_type


def get_cols_for_table(table_schema, table_name):
    """
    Get all records from schemadoc.columns for a given table
    """
    cursor.execute("""
        SELECT * FROM columns
        WHERE table_schema = %s AND table_name = %s
    """, (table_schema, table_name))
    return list(cursor.fetchall())


def prep_editable_file(row, uneditable_fields, file_path):
    """
    Prepare a file with the current values, so it can be edited using editor of choice.
    The new values will be used in an update.
    """
    text_to_edit = ""
    commented_text = "# You can't edit these commented fields:\n"

    for field, value in row.items():
        if field in uneditable_fields:
            commented_text += "# ___%s: %s\n" % (field, row[field])
        else:
            value = "" if value is None else value
            text_to_edit += "___%s: %s\n" % (field, value)

    with open(file_path, "w") as edit_f:
        edit_f.write(commented_text + "\n")
        edit_f.write(text_to_edit)


def parse_editable_file(file_path):
    """
    Take the "key: value" pairs from the text file and get them into a dict.
    Ignores comments, and allowed multiline values.
    """
    lines = open(file_path).read().splitlines()
    lines = [x for x in lines if not x.startswith("#")]
    remaining_text = "\n".join(lines)
    splitup = [x.strip() for x in remaining_text.split("___") if x.strip()]
    update_data = {}

    for piece in splitup:
        matches = re.match(r"(\w+):(.*)", piece, flags=re.DOTALL)
        key = matches.group(1).strip()
        val = matches.group(2).strip()
        update_data[key] = val

    return update_data


def update_db_from_dict(row_id, update_data, table):
    """
    Update a table given a dictionary of fields and values.
    Used today for taking values from text editor and overwriting in DB.
    """
    print("Update data is:", json.dumps(update_data, indent=4, default=str))

    for field, value in update_data.items():
        if isinstance(value, str):
            value = None if not value.strip() else value
        update_query = "UPDATE " + table + " SET " + field + " = %s WHERE id = %s"
        update_params = (value, row_id)
        cursor.execute(update_query, update_params)

    db_conn.commit()


def call_less(text):
    """
    Render a string in `less`
    """
    process = subprocess.Popen(["less", "-r"], stdin=subprocess.PIPE)
    process.stdin.write(text.encode("utf-8"))
    process.communicate()


def edit_loop(obj_name, uneditable_fields, update_func, file_path):
    """Call update_func with row_id as an arg, retrying if errors hit, or if user cancels"""
    row, _ = get_record_from_name(obj_name)
    row_id = row["id"]
    assert isinstance(row_id, int)

    prep_editable_file(row, uneditable_fields, file_path)
    while True:
        try:
            update_func(row_id, file_path)
        except Exception as e: # pylint: disable=broad-except
            print("oops, hit a problem:")
            db_conn.rollback()
            print(str(e))
            user_response = input("Try again? (y/n)")
            if user_response == "n":
                break
        break


def parse_options_file():
    """
    Read the se_options file into a dict
    """
    options = {}
    if not os.path.exists("se_options"):
        return {}

    with open("se_options") as config_fin:
        for line in config_fin:
            line = line.strip()
            option_name = line.split("=")[0]
            option_value = line.split("=")[1]
            options[option_name] = option_value

    return options


def get_user_config():
    """
    Set certain variables from environment variables or config files.
    """

    options_from_file = parse_options_file()

    table_ignore_patterns = {"^pg"}
    schemas_to_ignore = {"information_schema", "schemadoc"}
    schema = "schemadoc"

    table_ignore_patterns_string = os.environ.get("SE_TABLE_IGNORE_PATTERNS")
    if not table_ignore_patterns_string:
        table_ignore_patterns_string = options_from_file.get("TABLE_IGNORE_PATTERNS")

    if table_ignore_patterns_string:
        table_ignore_patterns.update(table_ignore_patterns_string.split(","))

    schemas_to_ignore_string = os.environ.get("SE_SCHEMAS_TO_IGNORE")
    if not schemas_to_ignore_string:
        schemas_to_ignore_string = options_from_file.get("SCHEMAS_TO_IGNORE")

    if schemas_to_ignore_string:
        schemas_to_ignore.update(schemas_to_ignore_string.split(","))

    if os.environ.get("SE_SCHEMA"):
        schema = os.environ["SE_SCHEMA"]
    elif options_from_file.get("SCHEMA"):
        schema = options_from_file["SCHEMA"]

    return {
        "schemas_to_ignore": schemas_to_ignore,
        "table_ignore_patterns": table_ignore_patterns,
        "schema": schema,
    }


def get_table_ignore_sql_string():
    """
    Get SQL string used in many places for excluding tables which we don't want to document
    """
    user_config = get_user_config()
    table_ignore_string = ""
    for _ in user_config["table_ignore_patterns"]:
        table_ignore_string += " AND table_name !~ %s"
    return table_ignore_string


def print_table_stats():
    psql_command = "psql -q << EOF\n"
    psql_command += f"SET SEARCH_PATH = { USER_CONFIG['schema'] },public;\n"
    psql_command += """
        \C 'Table Stats'
        SELECT
        table_schema,
        count(1) AS num_tables,
        round(avg(description IS NOT NULL :: int), 2) AS prop_with_desc,
        round(avg(last_approval_at IS NOT NULL :: int), 2) AS prop_with_approval,
        sum(orphaned::int) AS num_orphaned
        FROM schemadoc.tables
        GROUP BY table_schema;

        \C 'Column Stats'
        SELECT
        table_schema,
        count(1) AS num_columns,
        round(avg(description IS NOT NULL :: int), 2) AS prop_with_desc,
        round(avg(example_vals IS NOT NULL :: int), 2) AS prop_with_example_vals,
        sum(orphaned::int) AS num_orphaned
        FROM schemadoc.columns
        GROUP BY table_schema;
    """
    psql_command += "\nEOF"
    subprocess.call(psql_command, shell=True)


USER_CONFIG = get_user_config()
TABLE_IGNORE_STRING = get_table_ignore_sql_string()

db_conn = psycopg2.connect(
    "postgresql://%s@%s:5432/%s" % \
        (os.environ["PGUSER"], os.environ["PGHOST"], os.environ["PGDATABASE"]))
cursor = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cursor.execute(f"SET SEARCH_PATH = { USER_CONFIG['schema'] },public")
db_conn.commit()

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(THIS_DIR, "temp_files")
if not os.path.isdir(TEMP_DIR):
    os.mkdir("temp_files")
