import sqlalchemy
from sqlalchemy import Column, Integer, Text

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = sqlalchemy.MetaData(naming_convention=naming_convention)

nosacze = sqlalchemy.Table(
    "nosacze",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("url", Text, nullable=False, unique=True),
)

feels = sqlalchemy.Table(
    "feels",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("url", Text, nullable=False, unique=True),
)

fortunki = sqlalchemy.Table(
    "fortunki",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("text", Text, nullable=False, unique=True),
)
