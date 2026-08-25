# millions-rows-clickhouse

#### Инженерный проект по построению высокопроизводительного аналитического конвейера данных на базе ClickHouse и Apache Superset.

Основная цель — обеспечить эффективную загрузку, хранение и визуализацию больших объёмов данных (более 13 млн строк).

#### 🗺️ Конвейер данных:

Parquet-файлы ➡️ ClickHouse (OLAP) ➡️ Apache Superset (Визуализация данных).

#### Запуск ETL-скрипта в изолированном окружении Docker

```bash
docker compose exec superset /app/.venv/bin/python /app/etl_to_clickhouse.py
```

#### Запуск ETL-скрипта локально

```bash
poetry run python scripts/etl_to_clickhouse.py
```

#### Подключение ClickHouse к Apache Superset

```bash
clickhouse+connect://bi_user:bi_password@127.0.0.1:8124/ecommerce_olap
```

```sql
SELECT
    order_id,
    order_date,
    order_total_amount,
    orderline_id,
    quantity,
    unit_price,
    subtotal,
    product_name
FROM ecommerce_olap.superset_flat_analytics
WHERE order_id IN (
    SELECT order_id
    FROM ecommerce_olap.superset_flat_analytics
    GROUP BY order_id
    HAVING count() > 2
    LIMIT 10
)
ORDER BY order_id ASC, orderline_id ASC
LIMIT 100;

```
