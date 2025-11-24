# Инструкция по обновлению embeddings на сервере

## Проблема
На сервере embeddings в базе данных устарели (обновлялись 17 ноября с question+answer).
Текущий код использует question-only, что дает лучшие результаты.

## Решение

### 1. Подключиться к серверу
```bash
ssh root@147.78.65.141
# или
ssh root@vm3401705.firstbyte.club
```

### 2. Перейти в директорию проекта
```bash
cd ~/Maldina_AI
```

### 3. Активировать виртуальное окружение
```bash
source .venv312/bin/activate
```

### 4. Обновить код
```bash
git pull
```

### 5. Перегенерировать embeddings
```bash
python to_kb.py
```
Это обновит все embeddings в базе данных на question-only.

### 6. Перезапустить бота
```bash
sudo systemctl restart maldina_bot
```

### 7. Проверить статус
```bash
sudo systemctl status maldina_bot
```

## Ожидаемый результат

После обновления:
- "Когда придет заказ?" → ID=6 (про доставку) с distance ~2.92
- ID=13 (про деньги) с distance ~2.84
- Оба пройдут порог 3.1 и LLM выберет правильный ответ про доставку

## Команды для проверки (опционально)

Проверить distance после обновления:
```bash
python test_llm_response.py
```

Проверить даты обновления:
```bash
python check_kb_updates.py
```
