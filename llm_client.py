import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat-v3.1:free"
REFERER = "https://maldina.ru"  # Можно заменить на свой сайт
TITLE = "MaldinaBot"


def ask_llm(user_question: str, kb_answers: list[str]) -> str:
    """
    Отправляет запрос к OpenRouter LLM, используя найденные ответы из базы знаний как контекст.
    Возвращает сгенерированный ответ.
    """
    context = "\n\n".join([f"{i+1}. {a}" for i, a in enumerate(kb_answers)])
    prompt = (
        "Ответь пользователю на основании базы знаний магазина MalDina. "
        "Используй только приведённые ниже ответы, не придумывай ничего от себя. "
        "Если информации недостаточно, честно скажи, что ответа нет и предложи обратиться в поддержку.\n"
        f"Вопрос пользователя: {user_question}\n"
        f"Ответы из базы знаний:\n{context}"
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
