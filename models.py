# models.py
# SQLAlchemy 2.x (async) — пример модели User для PostgreSQL
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    async_sessionmaker,
    create_async_engine,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func
from datetime import datetime


class Base(AsyncAttrs, DeclarativeBase):
    pass


from sqlalchemy import DateTime, func


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# Пример создания движка и сессии:
# from dotenv import load_dotenv
# import os
# load_dotenv()
# DATABASE_URL = os.getenv("DATABASE_URL")
# engine = create_async_engine(DATABASE_URL, echo=True)
# async_session = async_sessionmaker(engine, expire_on_commit=False)

# Для миграций используйте Alembic или создайте таблицы вручную:
# async with engine.begin() as conn:
#     await conn.run_sync(Base.metadata.create_all)
