# models.py
# SQLAlchemy 2.x (async) — пример модели User для PostgreSQL
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    async_sessionmaker,
    create_async_engine,
    AsyncSession,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy import String, Integer, DateTime, func, BigInteger, Text, ARRAY
from datetime import datetime
from pgvector.sqlalchemy import Vector


class Base(AsyncAttrs, DeclarativeBase):
    pass


# Модель базы знаний (knowledge base)
class KbEntry(Base):
    __tablename__ = "kb_entries"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_primary: Mapped[str] = mapped_column(Text, nullable=False)
    answer_followup: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating_context: Mapped[list[str] | None] = mapped_column(
        ARRAY(Text), nullable=True
    )
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    source_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    embedding = mapped_column(Vector(384), nullable=True)
    tsv = mapped_column(Text, nullable=True) # Representing TSVECTOR as Text in ORM, actual type handled by DB
    # tsv не нужен в ORM, он для индексации/поиска


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    internal_sku: Mapped[str | None] = mapped_column(Text, nullable=True)
    wb_sku: Mapped[str | None] = mapped_column(Text, nullable=True)
    ozon_sku: Mapped[str | None] = mapped_column(Text, nullable=True)

    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)

    rag_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # эмбеддинг товара (VECTOR(384))
    embedding = mapped_column(Vector(384), nullable=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# Модель аналитики запросов
class QueryAnalytics(Base):
    __tablename__ = "query_analytics"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Запрос пользователя
    query_original: Mapped[str] = mapped_column(Text, nullable=False)
    query_normalized: Mapped[str] = mapped_column(Text, nullable=False)

    # Путь поиска и результат
    search_path: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # "sku_success", "sku_failed->name_success", etc.
    final_result_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # "product", "kb", "failed"

    # Детали результата
    result_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # product.id или kb_entry.id
    confidence_score: Mapped[float | None] = mapped_column(
        nullable=True
    )  # distance для KB
    threshold_used: Mapped[float | None] = mapped_column(
        nullable=True
    )  # порог на момент запроса

    # Мета-данные
    created_at: Mapped[datetime] = mapped_column(
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
