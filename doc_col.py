"""
Functions for walking the user through an editor-driven documentation flow
and then making the updates.
"""

import os
import subprocess

import util

UNEDITABLE_FIELDS = ("id", "table_schema", "table_name", "column_name", "data_type", "orphaned")
EDIT_FILE_PATH = os.path.join(util.THIS_DIR, "temp_files/col_edit_file.tmp")


def try_edit_update(row_id, file_path):
    """
    Start editor for inputting docs, validate, and possibly update in DB
    """
    subprocess.call([os.environ.get("EDITOR", "vim"), file_path])
    update_data = util.parse_editable_file(file_path)
    util.update_db_from_dict(row_id, update_data, table="columns")


def doc_col(name):
    """
    Delegate to edit_loop
    """
    util.edit_loop(name, UNEDITABLE_FIELDS, try_edit_update, EDIT_FILE_PATH)
