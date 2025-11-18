import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-2.5-flash"
REFERER = "https://maldina.ru"  # Можно заменить на свой сайт
TITLE = "MaldinaBot"


def ask_llm(user_question: str, kb_answers: list[str]) -> str:
    """
    Отправляет запрос к OpenRouter LLM, используя найденные ответы из базы
    знаний как контекст. Возвращает сгенерированный ответ.
    """
    if not kb_answers:
        # Если контекста нет — честно признаём
        prompt = (
            f"Вопрос пользователя: {user_question}\n\n"
            "В базе знаний магазина MalDina нет ответа на этот вопрос. "
            "Вежливо сообщи пользователю, что ответа нет, и предложи "
            "обратиться в службу поддержки магазина."
        )
    else:
        context = "\n\n".join(
            [f"{i+1}. {a}" for i, a in enumerate(kb_answers)]
        )
        prompt = (
            "Ты — помощник службы поддержки магазина MalDina.\n"
            "Твоя задача: ответить пользователю кратко, точно и по делу, "
            "используя ТОЛЬКО информацию из базы знаний ниже.\n\n"
            "Правила:\n"
            "- Отвечай на русском языке, вежливо и профессионально\n"
            "- Если ответ из базы полностью отвечает на вопрос — "
            "используй его\n"
            "- Если ответ частично подходит — адаптируй под вопрос, "
            "не добавляя лишнего\n"
            "- Если ответ НЕ подходит к вопросу — честно скажи, что "
            "информации нет, и предложи обратиться в поддержку\n"
            "- НЕ придумывай информацию, которой нет в базе знаний\n"
            "- Будь лаконичен, не повторяй очевидное\n\n"
            f"Вопрос пользователя: {user_question}\n\n"
            f"Информация из базы знаний:\n{context}\n\n"
            "Твой ответ:"
        )
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": REFERER,
        "X-Title": TITLE,
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    try:
        resp = requests.post(
            OPENROUTER_URL, headers=headers, data=json.dumps(data), timeout=30
        )
        resp.raise_for_status()
        result = resp.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[Ошибка LLM: {e}]"
