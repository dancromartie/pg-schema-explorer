"""
Pretty-prints a summary of a table and its columns, e.g. for reading in a pager.
"""

import textwrap

import util


def wrap_and_indent(text):
    """
    Wraps text to a reasonable width, and indents
    """
    if text is None:
        return "None"
    text = textwrap.fill(text, 100)
    # Indent the text
    text = text.replace("\n", "\n    ")
    return "    " + text


def format_table_summary(convenient_name):
    """
    Assembles a formatted string with an in-depth summary of table and columns
    """
    table_record, object_type = util.get_record_from_name(convenient_name)
    assert object_type == "table"
    table_schema, table_name = table_record["table_schema"], table_record["table_name"]

    output = []
    output.append("\n")

    output.append("-" * 100)
    output.append(("    TABLE %s.%s    " % (table_schema, table_name)).center(100))
    output.append("-" * 100)
    output.append("")
    output.append("Description:")
    output.append(wrap_and_indent(table_record["description"]))
    output.append("")
    output.append("Common joins: %s" % table_record["common_joins"])
    pretty_rows_count = "{:,}".format(
        table_record["rows_count"]) if table_record["rows_count"] else "unknown"
    output.append(
        "Latest num rows: {} as of {}".format(pretty_rows_count, table_record["rows_count_as_of"]))
    output.append("Update frequency: %s" % table_record["intended_update_frequency"])
    output.append("Deprecated: %s" % table_record["deprecated"])
    output.append("Docs Approved: %s" % table_record["docs_approved"])
    output.append("Last docs approval at: %s" % table_record["last_approval_at"])
    output.append("")
    output.append("-" * 100)
    output.append("   COLUMN DETAILS    ".center(100))
    output.append("-" * 100)
    output.append("")

    util.cursor.execute("""
        SELECT *
        FROM columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY column_name
    """, (table_schema, table_name))
    for row in util.cursor.fetchall():
        col_desc = row["description"]
        example_vals = row["example_vals"]
        also_goes_by = row["also_goes_by"]
        output.append("\033[1;4m%s\033[0m" % row["column_name"])
        if col_desc:
            output.append(wrap_and_indent(col_desc))
        if example_vals:
            output.append("\n    Example values:")
            output.append(wrap_and_indent(example_vals))
        if also_goes_by:
            output.append("\n    Also goes by:")
            output.append(wrap_and_indent(also_goes_by))
        output.append("")
        output.append("-" * 100)

    return "\n".join(output)
