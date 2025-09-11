import pandas as pd
from sentence_transformers import SentenceTransformer
import psycopg2

# Загрузка Excel
df = pd.read_excel("files/Скрипты для товаров.xlsx", dtype=str).fillna("")

# Модель эмбеддингов
model = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2"
)  # 384-мерный вектор

# Подключение к БД
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
    emb = model.encode(question).tolist()
    cur.execute(
        "INSERT INTO kb_entries (question, answer, embedding) VALUES (%s, %s, %s)",
        (question, answer, emb),
    )

conn.commit()
cur.close()
conn.close()
Резюме:

#Один столбец — вопрос, второй — ответ.
#Чем чище и короче формулировки, тем лучше будет поиск.
#После импорта можно реализовать поиск по смыслу и интеграцию с ботом.
#Если нужна помощь с обработкой Excel или скриптом — дай знать!