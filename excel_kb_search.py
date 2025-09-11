import pandas as pd
from pathlib import Path
from typing import List, Dict

EXCEL_PATH = Path("files") / "Скрипты для товаров.xlsx"

# Загрузка Excel-файла в память (один раз при старте)
def load_kb_excel() -> pd.DataFrame:
    df = pd.read_excel(EXCEL_PATH, dtype=str)
    df = df.fillna("")
    return df

# Поиск по вопросам (столбцы A и B), возвращает список ответов (C и D)
def search_kb_excel(df: pd.DataFrame, query: str, limit: int = 3) -> List[Dict]:
    # Приводим к нижнему регистру для простого поиска
    query_lower = query.lower()
    results = []
    for _, row in df.iterrows():
        question = f"{row.iloc[0]} {row.iloc[1]}".strip().lower()
        if query_lower in question:
            answer = f"{row.iloc[2]}\n{row.iloc[3]}".strip()
            results.append({
                "question": question,
                "answer": answer
            })
        if len(results) >= limit:
            break
    return results

# Пример использования
if __name__ == "__main__":
    df = load_kb_excel()
    q = input("Введите запрос: ")
    found = search_kb_excel(df, q)
    for res in found:
        print(f"Вопрос: {res['question']}")
        print(f"Ответ: {res['answer']}")
        print("---")
    if not found:
        print("Ничего не найдено!")
