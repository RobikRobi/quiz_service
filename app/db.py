import ssl
from uuid import uuid4

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import config

database_url = config.env_data.QUIZ_DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

connect_args = {
    "statement_cache_size": 0,
    "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
}

url = make_url(database_url)
query = dict(url.query)
sslmode = query.pop("sslmode", None)
sslrootcert = query.pop("sslrootcert", None)
query.pop("channel_binding", None)
query.setdefault("prepared_statement_cache_size", "0")

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

database_url = url.set(query=query)

engine = create_async_engine(
    database_url,
    echo=False,
    connect_args=connect_args,
    poolclass=NullPool,
)

async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_session():
    async with async_session() as session:
        yield session
        await session.commit()


class Base(AsyncAttrs, DeclarativeBase):
    pass
