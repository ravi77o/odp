import os

import snowflake.connector
from pydantic import BaseModel

from odp.core.types import SchemaRow, QueryRow


class SnowflakeCredentials(BaseModel):
    snowflake_account: str
    snowflake_user: str
    snowflake_password: str
    snowflake_database: str
    snowflake_warehouse: str | None = None
    snowflake_role: str | None = None


def load_snowflake_credentials() -> SnowflakeCredentials:
    """
    Load snowflake credentials from the .env-formatted file object
    """
    return SnowflakeCredentials(
        snowflake_account=os.environ["ODP_SNOWFLAKE_ACCOUNT"],
        snowflake_user=os.environ["ODP_SNOWFLAKE_USERNAME"],
        snowflake_password=os.environ["ODP_SNOWFLAKE_PASSWORD"],
        snowflake_database=os.environ["ODP_SNOWFLAKE_DATABASE"],
        snowflake_warehouse=os.environ.get("ODP_SNOWFLAKE_WAREHOUSE"),
        snowflake_role=os.environ.get("ODP_SNOWFLAKE_ROLE"),
    )

def get_snowflake_queries(credentials: SnowflakeCredentials) -> list[QueryRow]:
    conn = snowflake.connector.connect(
        user=credentials.snowflake_user,
        password=credentials.snowflake_password,
        account=credentials.snowflake_account,
        database=credentials.snowflake_database,
        role=credentials.snowflake_role,
        warehouse=credentials.snowflake_warehouse,
    )

    # Create a cursor object.
    cur = conn.cursor()

    # Execute a statement that will generate a result set.
    sql = """
SELECT QUERY_TEXT, DATABASE_NAME, SCHEMA_NAME
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE QUERY_TEXT ILIKE 'select%'
ORDER BY START_TIME DESC
LIMIT 10000; -- or start_time > $SOME_DATE to get columns unused in the last N days
        """
    cur.execute(sql)

    return [
        QueryRow(
            QUERY_TEXT=row[0],
            DATABASE_NAME=row[1],
            SCHEMA_NAME=row[2]
        ) for row in cur.fetchall()
    ]


def get_snowflake_schema(credentials: SnowflakeCredentials) -> list[SchemaRow]:
    conn = snowflake.connector.connect(
        user=credentials.snowflake_user,
        password=credentials.snowflake_password,
        account=credentials.snowflake_account,
        warehouse=credentials.snowflake_warehouse,
        database=credentials.snowflake_database,
        role=credentials.snowflake_role,
    )

    # Create a cursor object.
    cur = conn.cursor()

    # Execute a statement that will generate a result set.
    sql = f"""
SELECT
TABLE_CATALOG,
TABLE_SCHEMA,
TABLE_NAME,
COLUMN_NAME
FROM {credentials.snowflake_database}.information_schema.columns
WHERE TABLE_SCHEMA != 'INFORMATION_SCHEMA';
    """
    cur.execute(sql)

    return [
        SchemaRow(
            TABLE_CATALOG=row[0],
            TABLE_SCHEMA=row[1],
            TABLE_NAME=row[2],
            COLUMN_NAME=row[3],
        ) for row in cur.fetchall()
    ]