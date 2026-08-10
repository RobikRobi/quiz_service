import asyncio
import ssl
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection, make_url
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from app.config import config as app_config
from app.db import Base
from app.models import AnswerOption, AttemptAnswer, Question, Quiz, QuizAttempt

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url_and_connect_args() -> tuple[str, dict]:
    database_url = app_config.env_data.QUIZ_DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    url = make_url(database_url)
    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    sslrootcert = query.pop("sslrootcert", None)
    query.pop("channel_binding", None)
    query.setdefault("prepared_statement_cache_size", "0")

    connect_args = {}
    if sslmode and sslmode != "disable":
        if sslmode == "require":
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
        elif sslmode == "verify-ca":
            ssl_context = ssl.create_default_context(cafile=sslrootcert)
            ssl_context.check_hostname = False
        else:
            ssl_context = ssl.create_default_context(cafile=sslrootcert)
        connect_args["ssl"] = ssl_context

    return str(url.set(query=query)), connect_args


def get_database_url() -> str:
    database_url, _connect_args = get_database_url_and_connect_args()
    return database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    database_url, connect_args = get_database_url_and_connect_args()
    connectable = create_async_engine(
        database_url,
        connect_args=connect_args,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
