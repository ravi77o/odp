from enum import Enum

import click
from pydantic import BaseModel


class QueryRow(BaseModel):
    QUERY_TEXT: str
    DATABASE_NAME: str | None
    SCHEMA_NAME: str | None


class SchemaRow(BaseModel):
    TABLE_CATALOG: str
    TABLE_SCHEMA: str
    TABLE_NAME: str
    COLUMN_NAME: str


class Dialect(Enum):
    snowflake = "snowflake"
    bigquery = "bigquery"
    redshift = "redshift"

def validate_dialect(ctx, param, value):
    try:
        return Dialect(value)
    except ValueError:
        raise click.BadParameter(
            f'Invalid dialect value: {value}. Valid values are: {", ".join(d.value for d in Dialect)}')


class Grain(Enum):
    schema = "schema"
    table = "table"
    column = "column"

def validate_grain(ctx, param, value):
    try:
        return Grain(value)
    except ValueError:
        raise click.BadParameter(
            f'Invalid grain value: {value}. Valid values are: {", ".join(g.value for g in Grain)}')