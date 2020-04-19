WITH latest_counts AS (
    SELECT DISTINCT ON (table_schema, table_name) *
    FROM table_rows_count
    ORDER BY table_schema, table_name, created_at DESC
)

UPDATE schemadoc.tables t
SET rows_count = c.rows_count, rows_count_as_of = c.created_at
FROM latest_counts c
WHERE t.table_schema = c.table_schema
AND t.table_name = c.table_name;
