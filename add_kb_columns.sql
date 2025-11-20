ALTER TABLE kb_entries ADD COLUMN embedding VECTOR(384);
ALTER TABLE kb_entries ADD COLUMN tsv TSVECTOR;

-- После выполнения этих SQL-запросов вам следует повторно запустить to_kb.py, чтобы заполнить эти новые столбцы данными.
