"""
Syncs documentation tables with upstream data tables.
"""

import util


def update_table_list():
    """
    Look for new tables upstream that don't exist in documentation tables, and add them.
    """
    query_params = []
    query_params += list(util.USER_CONFIG["table_ignore_patterns"])
    query_params.append(tuple(util.USER_CONFIG["schemas_to_ignore"]))

    query = f"""
        INSERT INTO tables (table_schema, table_name) (
            SELECT table_schema, table_name
            FROM information_schema.columns
            WHERE 1 = 1
            { util.TABLE_IGNORE_STRING } 
            AND table_schema NOT IN %s
        )
        ON CONFLICT DO NOTHING;
    """
    util.cursor.execute(query, tuple(query_params))
    num_inserted_rows = util.cursor.rowcount
    print("%i rows inserted" % num_inserted_rows)
    util.db_conn.commit()


def update_column_list():
    """
    Insert rows for columns that exist in data tables but not in documentation tables
    """
    query_params = []
    query_params += list(util.USER_CONFIG["table_ignore_patterns"])
    query_params.append(tuple(util.USER_CONFIG["schemas_to_ignore"]))

    query = f"""
        INSERT INTO columns (table_schema, table_name, column_name, data_type) (
            SELECT table_schema, table_name, column_name, data_type
            FROM information_schema.columns
            WHERE 1 = 1
            { util.TABLE_IGNORE_STRING }
            AND table_schema NOT IN %s
            AND table_name IN (SELECT table_name FROM tables)
        )
        ON CONFLICT DO NOTHING;

    """
    util.cursor.execute(query, tuple(query_params))
    num_inserted_rows = util.cursor.rowcount
    print("%i rows inserted" % num_inserted_rows)
    util.db_conn.commit()


def update_orphans():
    """
    Marks tables/columns as orphaned, if their corresponding upstream entry has disappeared.
    """
    table_query = f"""
        WITH isc AS (
            SELECT DISTINCT table_schema, table_name
            FROM information_schema.columns
        )

        UPDATE tables t
        SET orphaned = True
        WHERE (orphaned IS NOT True) AND NOT EXISTS (
            SELECT * FROM isc
            WHERE table_name = t.table_name
            AND table_schema = t.table_schema);
    """
    util.cursor.execute(table_query)
    num_updated_rows = util.cursor.rowcount
    print("%i tables marked as orphaned" % num_updated_rows)
    util.db_conn.commit()
    
    column_query = """
        WITH isc AS (
            SELECT DISTINCT table_schema, table_name, column_name
            FROM information_schema.columns
        )

        UPDATE columns t
        SET orphaned = True
        WHERE (orphaned IS NOT True) AND NOT EXISTS (
            SELECT * FROM isc
            WHERE table_name = t.table_name
            AND table_schema = t.table_schema
            AND column_name = t.column_name
        );
    """
    util.cursor.execute(column_query)
    num_updated_rows = util.cursor.rowcount
    print("%i columns marked as orphaned" % num_updated_rows)
    util.db_conn.commit()
