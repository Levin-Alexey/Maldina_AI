import asyncio
import hashlib
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

CSV_PATH = Path("files") / "Скрипты для товаров - Скрипты для ВСЕХ товаров.csv"

DDL_STATEMENTS = [
    """
        CREATE TABLE IF NOT EXISTS kb_entries (
                id BIGSERIAL PRIMARY KEY,
                category TEXT,
                user_question TEXT,
                answer_primary TEXT NOT NULL,
                answer_followup TEXT,
                rating_context TEXT[],
                tags TEXT[],
                source_hash TEXT UNIQUE,
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now(),
                tsv tsvector
        )
        """,
    "CREATE INDEX IF NOT EXISTS idx_kb_entries_hash ON kb_entries(source_hash)",
    "CREATE INDEX IF NOT EXISTS idx_kb_entries_category ON kb_entries(category)",
    # Function (kept standalone)
    """
        CREATE OR REPLACE FUNCTION kb_entries_tsv_trigger() RETURNS trigger AS $$
        BEGIN
            NEW.tsv := to_tsvector('russian', coalesce(NEW.user_question,'') || ' ' || NEW.answer_primary || ' ' || coalesce(NEW.answer_followup,''));
            RETURN NEW;
        END
        $$ LANGUAGE plpgsql
        """,
    "DROP TRIGGER IF EXISTS trg_kb_entries_tsv ON kb_entries",
    "CREATE TRIGGER trg_kb_entries_tsv BEFORE INSERT OR UPDATE ON kb_entries FOR EACH ROW EXECUTE FUNCTION kb_entries_tsv_trigger()",
    "CREATE INDEX IF NOT EXISTS idx_kb_entries_tsv ON kb_entries USING GIN(tsv)",
]

KEYWORD_TAGS = {
    "возврат": "return",
    "брак": "defect",
    "доставка": "delivery",
    "ламп": "lamp",
    "инструкц": "manual",
    "адрес": "address",
    "whatsapp": "whatsapp",
}

# Columns guess: ['', 'проблема', 'ответ-скрипт', 'какие дальше дествия', '', '']


def normalize_text(x: Optional[str]) -> Optional[str]:
    if x is None:
        return None
    x = str(x).strip()
    if not x:
        return None
    # Collapse spaces
    while "  " in x:
        x = x.replace("  ", " ")
    return x


def extract_tags(*parts: str) -> List[str]:
    text_join = " ".join([p.lower() for p in parts if p])
    tags = set()
    for kw, tag in KEYWORD_TAGS.items():
        if kw in text_join:
            tags.add(tag)
    return sorted(tags)


def extract_rating_context(row_tail: List[str]) -> List[str]:
    ctx = []
    for cell in row_tail:
        if not cell:
            continue
        low = cell.lower()
        if "1" in low and "звезд" in low:
            ctx.append("stars_1_2_3")
        elif "4" in low and "звезд" in low:
            ctx.append("stars_4")
        elif "5" in low and "звезд" in low:
            ctx.append("stars_5")
    return sorted(set(ctx))


def build_source_hash(*parts: str) -> str:
    h = hashlib.sha1()
    for p in parts:
        if p:
            h.update(p.encode("utf-8"))
            h.update(b"\x1f")
    return h.hexdigest()


async def ensure_schema(engine: AsyncEngine):
    async with engine.begin() as conn:
        for stmt in DDL_STATEMENTS:
            await conn.execute(text(stmt))


async def import_csv(engine: AsyncEngine):
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH, dtype=str, keep_default_na=False)
    inserted = 0
    skipped = 0

    # Heuristic column positions
    # 0: blank, 1: problem, 2: answer, 3: followup, others tail

    async with engine.begin() as conn:
        for _, row in df.iterrows():
            raw_problem = normalize_text(row.iloc[1]) if len(row) > 1 else None
            raw_answer = normalize_text(row.iloc[2]) if len(row) > 2 else None
            raw_follow = normalize_text(row.iloc[3]) if len(row) > 3 else None

            # Skip empty
            if not raw_answer and not raw_problem:
                continue
            # Ignore delimiter rows
            if raw_problem and all(ch == "," for ch in raw_problem):
                continue

            # Category vs question heuristic
            category = None
            user_question = None
            if raw_problem and len(raw_problem) < 80 and raw_problem.endswith("?"):
                user_question = raw_problem
            elif raw_problem:
                # treat as category if short single token or has no spaces
                if len(raw_problem.split()) <= 4 and not raw_problem.endswith("."):
                    category = raw_problem
                else:
                    user_question = raw_problem

            rating_context = extract_rating_context(
                [normalize_text(c) for c in row.iloc[4:].tolist()]
            )
            tags = extract_tags(raw_problem or "", raw_answer or "", raw_follow or "")

            answer_primary = raw_answer or (raw_follow if raw_follow else None)
            if not answer_primary:
                continue

            source_hash = build_source_hash(
                raw_problem or "", answer_primary, raw_follow or ""
            )

            # Upsert (skip if exists)
            exists = await conn.execute(
                text("SELECT 1 FROM kb_entries WHERE source_hash=:h"),
                {"h": source_hash},
            )
            if exists.scalar() is not None:
                skipped += 1
                continue

            await conn.execute(
                text(
                    """
                    INSERT INTO kb_entries (category, user_question, answer_primary, answer_followup, rating_context, tags, source_hash)
                    VALUES (:category, :user_question, :answer_primary, :answer_followup, :rating_context, :tags, :source_hash)
                    """
                ),
                {
                    "category": category,
                    "user_question": user_question,
                    "answer_primary": answer_primary,
                    "answer_followup": raw_follow,
                    "rating_context": rating_context if rating_context else None,
                    "tags": tags if tags else None,
                    "source_hash": source_hash,
                },
            )
            inserted += 1

    print(f"Inserted: {inserted}, skipped (duplicates): {skipped}")


async def main():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    engine = create_async_engine(db_url, echo=False)
    await ensure_schema(engine)
    await import_csv(engine)


if __name__ == "__main__":
    asyncio.run(main())
