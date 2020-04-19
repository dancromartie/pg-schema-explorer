"""
Functions for walking the user through an editor-driven documentation flow
and then making the updates.
"""

import datetime
import os
import subprocess

import util

UNEDITABLE_FIELDS = (
    "id", "table_schema", "table_name", "last_approval_at", "orphaned", "rows_count",
    "rows_count_as_of")
EDIT_FILE_PATH = os.path.join(util.THIS_DIR, "temp_files/table_edit_file.tmp")
UPDATE_FREQUENCIES = ("hourly", "sub-hourly", "daily", "weekly", "ad-hoc", "never-again")


def try_edit_update(row_id, file_path):
    """
    Start editor for inputting docs, validate, and possibly update in DB
    """
    subprocess.call([os.environ.get("EDITOR", "vim"), file_path])
    update_data = util.parse_editable_file(file_path)

    if str(update_data["docs_approved"]).lower() in ["true", "yes"]:
        update_data["last_approval_at"] = datetime.datetime.now()

    freq = update_data["intended_update_frequency"]
    if freq and freq not in UPDATE_FREQUENCIES:
        raise ValueError(
            "Bad update frequency %s. Expected one of: %s" % (freq, UPDATE_FREQUENCIES))
    util.update_db_from_dict(row_id, update_data, table="tables")


def doc_table(name):
    """
    Delegate to edit_loop
    """
    util.edit_loop(name, UNEDITABLE_FIELDS, try_edit_update, EDIT_FILE_PATH)
