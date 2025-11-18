import pandas as pd
from sentence_transformers import SentenceTransformer
import psycopg2
from pathlib import Path

# === 1. Ищем Excel-файл с товарами ===
# Пути-п候дпи (как в to_kb.py): ./files/products.xlsx или ./products.xlsx
base_dir = Path(__file__).resolve().parent
candidates = [base_dir / "files" / "products.xlsx", base_dir / "products.xlsx"]
for path in candidates:
    if path.exists():
        xlsx_path = path
        break
else:
    raise FileNotFoundError(
        "Не найден Excel-файл products.xlsx. "
        "Проверь, что он есть по одному из путей: "
        + ", ".join(str(p) for p in candidates)
    )

print(f"Используется файл: {xlsx_path}")

# === 2. Читаем Excel ===
df = pd.read_excel(xlsx_path, dtype=str).fillna("")

# Проверяем, что нужные колонки есть
required_cols = ["internal_sku", "wb_sku", "ozon_sku", "product_name", "category", "rag_text"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"В файле {xlsx_path} нет обязательных колонок: {missing}")

# === 3. Модель эмбеддингов (та же, что для kb) ===
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")  # 384-мерный вектор

# === 4. Подключение к БД ===
conn = psycopg2.connect(
    dbname="maldinadb",
    user="adminmaldina",
    password="maldina123!",
    host="147.78.65.141",
)
cur = conn.cursor()

# (опционально) очищаем таблицу перед заливкой, чтобы не плодить дубли
# Если боишься потерять данные — закомментируй следующую строку:
cur.execute("TRUNCATE TABLE products;")

# === 5. Проходим по строкам Excel и заливаем в products ===
for idx, row in df.iterrows():
    internal_sku = row["internal_sku"].strip()
    wb_sku = row["wb_sku"].strip()
    ozon_sku = row["ozon_sku"].strip()
    name = row["product_name"].strip()
    category = row["category"].strip()
    rag_text = row["rag_text"].strip()

    if not rag_text and not name:
        # Строка пустая, пропускаем
        continue

    # Текст для эмбеддинга — используем rag_text, а если он пустой — хотя бы name
    emb_source_text = rag_text if rag_text else name
    emb = model.encode(emb_source_text).tolist()

    cur.execute(
        """
        INSERT INTO products (
            internal_sku,
            wb_sku,
            ozon_sku,
            name,
            category,
            rag_text,
            embedding
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (internal_sku, wb_sku, ozon_sku, name, category, rag_text, emb),
    )

conn.commit()
cur.close()
conn.close()
print("Импорт products.xlsx в таблицу products завершён.")
