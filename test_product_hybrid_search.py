import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from product_search import search_products_hybrid
import logging
import os

# --- Настройка логирования ---
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "test_product_hybrid_search.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# --- Конфигурация базы данных ---
# ВНИМАНИЕ: Используйте переменные окружения для боевых систем!
DATABASE_URL = "postgresql+asyncpg://adminmaldina:maldina123!@147.78.65.141/maldinadb"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)

# --- Тестовые запросы для товаров ---
TEST_PRODUCT_QUERIES = [
    {"query": "1728614518", "description": "Точный SKU - должен быть priority=0"},
    {"query": "1471830723", "description": "Точный SKU - должен быть priority=0"},
    {"query": "1909110657", "description": "Точный SKU - должен быть priority=0"},
    {"query": "лампа коран", "description": "Семантический + название"},
    {"query": "Лампа-цилиндр с Кораном", "description": "Точное название + семантика"},
    {"query": "массажный матрас", "description": "Семантический поиск"},
    {"query": "умное кольцо", "description": "Семантический поиск"},
    {"query": "автомат орбизы", "description": "Семантический + название"},
]


async def run_test():
    async with AsyncSessionFactory() as session:
        logger.info("--- Запуск теста гибридного поиска товаров ---")

        for i, sample in enumerate(TEST_PRODUCT_QUERIES):
            query = sample["query"]
            description = sample.get("description", "")

            logger.info(f"\n--- Тест {i+1}/{len(TEST_PRODUCT_QUERIES)} ---")
            logger.info(f"Запрос: {query}")
            logger.info(f"Описание: {description}")

            logger.info("Выполнение гибридного поиска товаров...")
            results = await search_products_hybrid(session, query, limit=5)

            if results:
                logger.info(f"Найдено товаров: {len(results)}")
                for idx, res in enumerate(results, 1):
                    # Форматируем distance
                    dist_val = res.get('distance', 'N/A')
                    dist_str = f"{dist_val:.4f}" if isinstance(dist_val, (int, float)) else str(dist_val)
                    
                    log_line = (
                        f"  {idx}. ID: {res.get('id')}, "
                        f"Priority: {res.get('priority', 'N/A')}, "
                        f"Distance: {dist_str}, "
                        f"Name: {res.get('name', '')[:50]}, "
                        f"Search Type: {res.get('search_type', 'unknown')}"
                    )
                    logger.info(log_line)
                    
                    # Дополнительная информация для первого результата
                    if idx == 1:
                        sku_info = (
                            f"     SKU (internal): {res.get('internal_sku', '')}, "
                            f"WB: {res.get('wb_sku', '')}, "
                            f"Ozon: {res.get('ozon_sku', '')}"
                        )
                        logger.info(sku_info)
            else:
                logger.info("Товары не найдены.")

        logger.info("--- Тест гибридного поиска товаров завершен ---")


if __name__ == "__main__":
    asyncio.run(run_test())
