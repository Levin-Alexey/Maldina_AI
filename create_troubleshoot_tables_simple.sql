-- SQL скрипт для создания таблиц troubleshooting функционала
-- PostgreSQL с pgvector

-- Таблица инструкций по устранению неисправностей
CREATE TABLE IF NOT EXISTS troubleshoot_instructions (
    id SERIAL PRIMARY KEY,
    internal_sku TEXT,
    wb_sku TEXT,
    ozon_sku TEXT,
    product_name TEXT NOT NULL,
    issue_description TEXT NOT NULL,
    steps JSONB NOT NULL,
    content_hash VARCHAR(64) UNIQUE NOT NULL,
    embedding VECTOR(384),
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

CREATE INDEX IF NOT EXISTS idx_troubleshoot_steps 
    ON troubleshoot_instructions USING gin(steps);

-- Таблица сессий troubleshooting (аналитика)
CREATE TABLE IF NOT EXISTS troubleshoot_sessions (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL,
    instruction_id INTEGER REFERENCES troubleshoot_instructions(id) ON DELETE SET NULL,
    search_query TEXT NOT NULL,
    instruction_found BOOLEAN NOT NULL DEFAULT FALSE,
    steps_completed INTEGER NOT NULL DEFAULT 0,
    issue_resolved BOOLEAN,
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

-- Триггер для автоматического обновления updated_at
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

-- Проверка
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public' 
  AND table_name IN ('troubleshoot_instructions', 'troubleshoot_sessions')
ORDER BY table_name;
