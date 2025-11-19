-- Создание таблицы query_analytics для логирования запросов пользователей
-- Выполнить на сервере PostgreSQL: psql -U adminmaldina -d maldinadb -f create_query_analytics_table.sql

CREATE TABLE IF NOT EXISTS query_analytics (
    id SERIAL PRIMARY KEY,
    telegram_user_id BIGINT NOT NULL,
    
    -- Запрос пользователя
    query_original TEXT NOT NULL,
    query_normalized TEXT NOT NULL,
    
    -- Путь поиска и результат
    search_path VARCHAR(100) NOT NULL,  -- "sku_success", "sku_failed->name_success", etc.
    final_result_type VARCHAR(20) NOT NULL,  -- "product", "kb", "failed"
    
    -- Детали результата
    result_id INTEGER,  -- product.id или kb_entry.id (NULL если failed)
    confidence_score DOUBLE PRECISION,  -- distance для KB (NULL для товаров)
    threshold_used DOUBLE PRECISION,  -- порог на момент запроса (NULL если не применялся)
    
    -- Временная метка
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для оптимизации запросов
CREATE INDEX IF NOT EXISTS idx_query_analytics_normalized 
    ON query_analytics(query_normalized);

CREATE INDEX IF NOT EXISTS idx_query_analytics_result_type_time 
    ON query_analytics(final_result_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_query_analytics_user_time 
    ON query_analytics(telegram_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_query_analytics_created_at 
    ON query_analytics(created_at DESC);

-- Комментарии к таблице и колонкам
COMMENT ON TABLE query_analytics IS 'Логирование всех запросов пользователей к боту';
COMMENT ON COLUMN query_analytics.query_original IS 'Оригинальный запрос как написал пользователь';
COMMENT ON COLUMN query_analytics.query_normalized IS 'Нормализованный запрос (lowercase, stripped)';
COMMENT ON COLUMN query_analytics.search_path IS 'Путь поиска: sku_success, sku_failed->name_success, etc.';
COMMENT ON COLUMN query_analytics.final_result_type IS 'Тип итогового результата: product, kb, failed';
COMMENT ON COLUMN query_analytics.result_id IS 'ID найденного товара или KB записи (NULL если failed)';
COMMENT ON COLUMN query_analytics.confidence_score IS 'Distance для RAG KB поиска (меньше = лучше)';
COMMENT ON COLUMN query_analytics.threshold_used IS 'Порог distance который использовался при поиске в KB';
