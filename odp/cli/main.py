import click
from dotenv import load_dotenv

from odp.core.detect_unused import detect_unused_columns, build_info_schema, read_queries, \
    read_info_schema_from_file
from odp.core.snowflake import load_snowflake_credentials, get_snowflake_schema, get_snowflake_queries
from odp.core.types import Dialect, validate_dialect, validate_grain, Grain

load_dotenv()

@click.group(name="odp")
def cli():
    pass


@cli.command('detect-unused', help="""
Detect unused columns in SQL queries. 
Requires two files: a query file and an information schema file. 
Run `show-queries` to see the SQL queries to run against your 
Snowflake instance to generate the two files.""")
@click.option('--queries_file', help='The SQL query file to analyze.')
@click.option('--info_schema_file',
              help='The file containing the information schema for the database.')
@click.option('--dialect',
              type=click.Choice([d.value for d in Dialect]),
              callback=validate_dialect,
              default='snowflake',
              help='The type of warehouse to connect to. Currently only snowflake is supported.')
@click.option('--grain',
              type=click.Choice([g.value for g in Grain]),
              callback=validate_grain,
              default='column',
              help='the grain to search for, e.g. use --grain=table to search for unused tables. Default is column.')
def cli_detect_unused_columns(
    queries_file: str | None,
    info_schema_file: str | None,
    dialect: Dialect,
    grain: Grain,
):

    if queries_file and info_schema_file:
        queries = read_queries(queries_file)
        print(f"Read {len(queries)} queries from {queries_file}")

        info_schema, info_schema_flat = read_info_schema_from_file(info_schema_file)
        print(f"Read {len(info_schema_flat)} information schema rows from {info_schema_file}")
        if grain == Grain.column:
            detect_unused_columns(queries, info_schema, info_schema_flat, dialect)
        elif grain == Grain.table:
            raise NotImplementedError("Table grain is not yet supported")
        elif grain == Grain.schema:
            raise NotImplementedError("Schema grain is not yet supported")

        return


    if dialect == Dialect.snowflake:
        try:
            credentials = load_snowflake_credentials()
        except KeyError as e:
            raise ValueError(f"""
Missing or invalid parameters: {e}. Please provide either 
            
   1. both of --info_schema_file and --queries_file (use "odp show-queries" to generate these
   2. valid crendentials via env, e.g. ODP_SNOWFLAKE_ACCOUNT, ODP_SNOWFLAKE_USER, etc
            """)

        schema = get_snowflake_schema(credentials)
        queries = get_snowflake_queries(credentials)

        info_schema, info_schema_flat = build_info_schema(schema)
        if grain == Grain.column:
            detect_unused_columns(queries, info_schema, info_schema_flat, dialect)
        elif grain == Grain.table:
            raise NotImplementedError("Table grain is not yet supported")
        elif grain == Grain.schema:
            raise NotImplementedError("Schema grain is not yet supported")
    elif dialect == Dialect.bigquery:
        raise NotImplementedError("Loading BigQuery data via credentials is not yet supported")
    elif dialect == Dialect.redshift:
        raise NotImplementedError("Loading Redshift data via credentials is not yet supported")


@cli.command("show-queries")
def show_snowflake_queries():
    print("Run the below against your snowflake instance to generate a dataset you can"
          "export to CSV for analysis")
    print("""
-- query_file

SELECT *
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TEXT ILIKE 'select%'
ORDER BY START_TIME DESC
LIMIT 10000; -- or start_time > $SOME_DATE to get columns unused in the last N days


-- info_schema_file

use database MY_DATABASE; -- change me

SELECT
TABLE_CATALOG,
TABLE_SCHEMA,
TABLE_NAME,
COLUMN_NAME
FROM information_schema.columns
WHERE TABLE_SCHEMA != 'INFORMATION_SCHEMA';
        
        """
    )

if __name__ == "__main__":
    cli()