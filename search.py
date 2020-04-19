"""
Functions for finding and displaying tables and columns.
Mostly leverages the psql client.
"""

import subprocess

import util


def search(
        patterns, expanded_display=False, tuples_only=False, most_recent=False, wrap=False,
        null_desc_only=False):
    """
    Find tables or columns matching passed regular expressions.
    Print according to given formatting options.
    """
    if len(patterns) not in (1, 2):
        raise ValueError("Too many patterns provided to search function")

    psql_command = "psql -q << EOF\n"
    psql_command += f"SET SEARCH_PATH = { util.USER_CONFIG['schema'] },public;\n"

    if expanded_display:
        psql_command += "\\x\n"
    if tuples_only:
        psql_command += "\\t\n"
    if wrap:
        psql_command += \
            "\pset format wrapped\n\pset columns 150" \
            # pylint: disable=anomalous-backslash-in-string

    null_desc_clause = ""
    if null_desc_only:
        null_desc_clause = "AND description IS NULL"

    table_pattern = patterns[0]
    if len(patterns) == 1:
        order_clause = "ORDER BY table_schema, table_name"
        if most_recent:
            order_clause = "ORDER BY inserted_at DESC"
        psql_command += f"""
            SELECT
            table_schema, table_name, description, docs_approved AS aprvd
            FROM tables
            WHERE table_name ~ '{table_pattern}'
            {null_desc_clause}
            {order_clause}
            ;
        """
    elif len(patterns) == 2:
        column_pattern = patterns[1]
        order_clause = "ORDER BY table_name, column_name"
        if most_recent:
            order_clause = "ORDER BY inserted_at DESC"
        psql_command += f"""
            SELECT table_schema, table_name, column_name, description
            FROM columns
            WHERE table_name ~ '{table_pattern}'
            AND column_name ~ '{column_pattern}'
            {null_desc_clause}
            {order_clause}
            ;
        """
    psql_command += "\nEOF"
    subprocess.call(psql_command, shell=True)
