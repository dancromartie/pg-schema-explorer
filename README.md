# Schema Explorer

## 4 examples

```
se search table_pattern column_pattern
se describe schema.table
se document schema.table
se document schema.table.column
```

## Setup

1. clone the repo
2. install the `psql` postgres client
3. make sure you have Python's `psycopg2` in some virtual environment
4. Put the repo on your path, e.g. add `export PATH="$PATH:~/dev/pg-schema-explorer"` to `~/.bash_profile`

## Commands for finding things

```

# List all tables
se search .

# list all columns. pattern 1 is a table regex, pattern 2 is a column regex
se search . .

# Use "expanded display" mode (key-value mode), like psql's -x option
se search -x . .

# Turn wrapping on
se search -w crm

# List all tables containing "order"
se search order

# List all columns containing "account"
se search . account

# List all columns containing "account" within tables containing "order"
se search order account

# List all tables ending with "staging"
se search "staging$"

# List most recently discovered tables with -r
se search . -r -w | less

# List only tables with null descriptions
se search . -n

# Disable headers and psql borders/formatting, e.g. for easier use with AWK, cut, Python, etc
se search -t crm

# "list" is an alias
se list .

```

These commands print textual output like:

```
 table_schema |      table_name       |               description       | aprvd
--------------+-----------------------+---------------------------------+-------
 public       |      my_table_name    | some table description here     | t
 public       |      my_table_name_2  | some other description here     | t
```

## Commands for describing/summaries

```
# Show a full printout out table public.foo, opening pager
se describe foo

# Show a full printout out table someschema.foo
se describe someschema.foo
```

## Commands for adding/editing content

```
# Start editor and edit info about a table
se document someschema.foo

# Start editor and edit info about a column
se document someschema.foo.bar

# Start editor and edit info about all columns in table foo
se document somechea.foo --columns

# Changing your editor
EDITOR=nano se document foo
EDITOR=vim se document foo
EDITOR=emacs se document foo
# etc. I can't get Sublime to work because it opens in the background and
# doesn't tell Python when done.
```

## Seeing stats about your docs

```
se stats
```

This prints something like:

```
     table_schema      | num_tables | prop_with_desc | prop_with_approval | num_orphaned
-----------------------+------------+----------------+--------------------+--------------
 ui                    |          1 |           1.00 |               1.00 |            0
 public                |        714 |           0.37 |               0.34 |            0
 bi                    |        138 |           0.47 |               0.39 |            0

                                         Column Stats
     table_schema      | num_columns | prop_with_desc | prop_with_example_vals | num_orphaned
-----------------------+-------------+----------------+------------------------+--------------
 ui                    |           3 |           1.00 |                   1.00 |            0
 public                |       24114 |           0.04 |                   1.00 |            0
 bi                    |        1038 |           0.04 |                   1.00 |            0
```

## Syncing with upstream data tables

As tables/columns are added/named/removed, you'll want your docs tables to stay in sync.

```
# Refresh table list
se refresh --table-list
se refresh --column-list
se refresh --orphans
```

## Resolving orphans

"Orphan" refers to a table/column that is documented but doesn't exist upstream in the actual database.
When these are detected, there are a few things you could do:

1. The table/column no longer exists upstream, so delete it from the docs tables.
2. The table/column has been renamed, so rename it in the docs tables.
3. The table has moved to another schema, so note the move.

The commands below would present you with the above options.

```
# Auto-selects an orphaned table to fix
se resolve-orphans --table
# Auto-selects an orphaned column to fix
se resolve-orphans --column
```

## Adding example values to columns

```
python auto_add_example_vals.py --no-confirmation
```

This will use PG's `TABLESAMPLE` feature to get fast samples and summarize/rank some of the top
values ~5 values.

## What's going on behind the scenes?

All data is stored in 2 tables. 1) `schemadoc.tables`, 2) `schemadoc.columns`

Everything is about manipulating either editing those tables, or adding/removing rows, based off
of what is found in `information_schema.columns` (Postgres's internal table/column lists)

## Environment/config

You can use these environment variables to tweak SE's behavior.

Connection-related:

```
# SE uses the standard PGHOST, PGDATABASE, and PGUSER vars that libpq uses
# See the PG docs for more.
export PGHOST=my.rds.instance.amazonaws.com
export PGDATABASE=my_test_dw
```

Ignoring tables/schemas using environment variables:

```
# Ignores tables starting with "staging___" or "geography_"
# It's a comma separated list
export SE_TABLE_IGNORE_PATTERNS='^staging___,^geography_'
# Ignores these 3 schemas
export SE_SCHEMAS_TO_IGNORE='personal,deprecated,boringschema'
```

If these variables are not set, then file "se_options" will be checked.
The format of this file is similar to using enviroment variables, except quoting is ignored,
and the "SE_" prefix is dropped.

```
TABLE_IGNORE_PATTERNS=^staging___,^geography_
SCHEMAS_TO_IGNORE=personal,deprecated,boringschema
```

If no environment or config is found, then a default will be used.

By default, tables for documentation go into schema "schemadoc", but you can change this with
environment variable `SE_SCHEMA` (or `SCHEMA` if using `se_options`)

## Creating tables, running custom queries

Run the scripts in custom_queries/, with the modifications you want. The Python
code does not do this setup for you. This is your opportunity to create the tables in
a different schema than the default, to grant perms to your users, etc.

You may also need to connect to your own tables in order to update certain columns.
For example, there is a file `custom_queries/update_row_counts.sh`. This assumes certain
helper tables for storing row counts, which may not exist in your project/organization.

## Editing without using command-line tools

What if you don't/won't know Vim/Emacs and find `nano` to be clunky? GUI tools
like PGAdmin, DataGrip, TablePlus, etc allow editing in-app. As long as the PG
permissions allow it, people can edit rows in the tables mentioned above using
their favored GUI.

I've tried this in PGAdmin and it works fine.
