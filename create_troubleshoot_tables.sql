-- SQL скрипт для создания таблиц troubleshooting функционала
-- PostgreSQL с расширениями pgvector

-- Убедитесь, что расширение pgvector установлено (если его нет - векторы будут NULL)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- Таблица инструкций по устранению неисправностей
-- =============================================================================
CREATE TABLE IF NOT EXISTS troubleshoot_instructions (
    id SERIAL PRIMARY KEY,
    internal_sku TEXT,
    wb_sku TEXT,
    ozon_sku TEXT,
    product_name TEXT NOT NULL,
    issue_description TEXT NOT NULL,
    steps JSONB NOT NULL,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_troubleshoot_product_name 
    ON troubleshoot_instructions USING gin(to_tsvector('russian', product_name));

CREATE INDEX IF NOT EXISTS idx_troubleshoot_issue 
    ON troubleshoot_instructions USING gin(to_tsvector('russian', issue_description));

CREATE INDEX IF NOT EXISTS idx_troubleshoot_content_hash 
    ON troubleshoot_instructions(content_hash);

-- Индекс для векторного поиска (cosine distance)
CREATE INDEX IF NOT EXISTS idx_troubleshoot_embedding 
    ON troubleshoot_instructions USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- GIN индекс для JSONB (если нужен поиск внутри шагов)
CREATE INDEX IF NOT EXISTS idx_troubleshoot_steps 
    ON troubleshoot_instructions USING gin(steps);

-- Комментарии к таблице и колонкам
COMMENT ON TABLE troubleshoot_instructions IS 'Инструкции по устранению неисправностей товаров';
COMMENT ON COLUMN troubleshoot_instructions.internal_sku IS 'Внутренние артикулы через запятую';
COMMENT ON COLUMN troubleshoot_instructions.wb_sku IS 'Артикулы Wildberries через запятую';
COMMENT ON COLUMN troubleshoot_instructions.ozon_sku IS 'Артикулы Ozon через запятую';
COMMENT ON COLUMN troubleshoot_instructions.steps IS 'JSON с пошаговыми инструкциями: {"1": "шаг 1", "2": "шаг 2"}';
COMMENT ON COLUMN troubleshoot_instructions.content_hash IS 'SHA256 хеш product_name + issue_description для дедупликации';
COMMENT ON COLUMN troubleshoot_instructions.embedding IS 'Vector(384) для семантического поиска';


-- =============================================================================
-- Таблица сессий troubleshooting (аналитика)
-- =============================================================================
CREATE TABLE IF NOT EXISTS troubleshoot_sessions (
    id SERIAL PRIMARY KEY,
    
    -- Telegram ID пользователя
    telegram_user_id BIGINT NOT NULL,
    
    -- Связь с инструкцией (если найдена)
    instruction_id INTEGER REFERENCES troubleshoot_instructions(id) ON DELETE SET NULL,
    
    -- Поисковый запрос пользователя
    search_query TEXT NOT NULL,
    
    -- Найдена ли инструкция
    instruction_found BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Количество пройденных шагов
    steps_completed INTEGER NOT NULL DEFAULT 0,
    
    -- Решена ли проблема (NULL если пользователь не указал)
    issue_resolved BOOLEAN,
    
    -- Временные метки
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Индексы для аналитики
CREATE INDEX IF NOT EXISTS idx_troubleshoot_sessions_user 
    ON troubleshoot_sessions(telegram_user_id);

CREATE INDEX IF NOT EXISTS idx_troubleshoot_sessions_instruction 
    ON troubleshoot_sessions(instruction_id);

CREATE INDEX IF NOT EXISTS idx_troubleshoot_sessions_created 
    ON troubleshoot_sessions(created_at);

CREATE INDEX IF NOT EXISTS idx_troubleshoot_sessions_resolved 
    ON troubleshoot_sessions(issue_resolved) WHERE issue_resolved IS NOT NULL;

-- Комментарии
COMMENT ON TABLE troubleshoot_sessions IS 'Аналитика сессий troubleshooting (статистика использования инструкций)';
COMMENT ON COLUMN troubleshoot_sessions.steps_completed IS 'Сколько шагов прошел пользователь';
COMMENT ON COLUMN troubleshoot_sessions.issue_resolved IS 'TRUE - помогло, FALSE - не помогло, NULL - не указано';


-- =============================================================================
-- Триггер для автоматического обновления updated_at
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_troubleshoot_instructions_updated_at 
    BEFORE UPDATE ON troubleshoot_instructions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- Вспомогательные функции для поиска
-- =============================================================================

-- Функция для поиска по артикулу
CREATE OR REPLACE FUNCTION find_instruction_by_sku(search_sku TEXT)
RETURNS TABLE (
    id INTEGER,
    product_name TEXT,
    issue_description TEXT,
    steps JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ti.id,
        ti.product_name,
        ti.issue_description,
        ti.steps
    FROM troubleshoot_instructions ti
    WHERE 
        search_sku = ANY(string_to_array(REPLACE(ti.internal_sku, ' ', ''), ','))
        OR search_sku = ANY(string_to_array(REPLACE(ti.wb_sku, ' ', ''), ','))
        OR search_sku = ANY(string_to_array(REPLACE(ti.ozon_sku, ' ', ''), ','));
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_instruction_by_sku IS 'Поиск инструкций по любому артикулу (internal_sku, wb_sku, ozon_sku)';


-- =============================================================================
-- Конец скрипта
-- =============================================================================

-- Проверка созданных таблиц
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_name IN ('troubleshoot_instructions', 'troubleshoot_sessions')
ORDER BY table_name;
