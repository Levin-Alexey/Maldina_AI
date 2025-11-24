import pandas as pd
from sentence_transformers import SentenceTransformer
import psycopg2
import hashlib
from pathlib import Path

# 1. Читаем Excel: 1-я колонка - вопрос, 2-я - ответ
# Ищем файл сначала в ./files/kb.xlsx, затем в ./kb.xlsx
base_dir = Path(__file__).resolve().parent
candidates = [base_dir / "files" / "kb.xlsx", base_dir / "kb.xlsx"]
for path in candidates:
    if path.exists():
        xlsx_path = path
        break
else:
    raise FileNotFoundError(
        (
            "Не найден Excel-файл kb.xlsx. Проверьте, что он существует по "
            "одному из путей: "
        )
        + ", ".join(str(p) for p in candidates)
    )

df = pd.read_excel(xlsx_path, dtype=str).fillna("")

# 2. Модель эмбеддингов (384-мерный вектор)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

# 3. Подключение к БД
conn = psycopg2.connect(
    dbname="maldinadb",
    user="adminmaldina",
    password="maldina123!",
    host="147.78.65.141",
)
cur = conn.cursor()

for _, row in df.iterrows():
    question = row.iloc[0].strip()
    answer = row.iloc[1].strip()

    if not question and not answer:
        continue

    # Текст для эмбеддинга: только вопрос
    # (короткие вопросы лучше матчатся без примеси длинного ответа)
    emb_text = question
    emb = model.encode(emb_text).tolist()

    # Уникальный хэш строки (чтобы не было дублей)
    source_hash = hashlib.sha256(
        (question + "\n" + answer).encode("utf-8")
    ).hexdigest()

    # INSERT в таблицу kb_entries
    # Upsert: при конфликте по source_hash обновляем
    # вопрос, ответ, embedding и tsv
    cur.execute(
        """
        INSERT INTO kb_entries (
            category,
            user_question,
            answer_primary,
            answer_followup,
            rating_context,
            tags,
            source_hash,
            embedding,
            tsv
        )
        VALUES (
            NULL,
            %s,
            %s,
            NULL,
            NULL,
            NULL,
            %s,
            %s,
            to_tsvector('russian', %s)
        )
        ON CONFLICT (source_hash) DO UPDATE SET
            user_question = EXCLUDED.user_question,
            answer_primary = EXCLUDED.answer_primary,
            embedding = EXCLUDED.embedding,
            tsv = EXCLUDED.tsv,
            updated_at = CURRENT_TIMESTAMP
        """,
        (question, answer, source_hash, emb, question + " " + answer),
    )

conn.commit()
cur.close()
conn.close()
print("Импорт kb.xlsx завершён.")
