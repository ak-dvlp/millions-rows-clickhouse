# millions-rows-clickhouse

#### Инженерный проект по построению высокопроизводительного аналитического конвейера данных на базе ClickHouse и Apache Superset.

Основная цель — обеспечить эффективную загрузку, хранение и визуализацию больших объёмов данных (более 16 млн строк).

#### 🗺️ Конвейер данных:

Parquet-файлы ➡️ ClickHouse (OLAP) ➡️ Apache Superset (Визуализация данных).


#### Запуск ETL-скрипта в изолированном окружении Docker

```bash
docker compose exec superset /app/.venv/bin/python /app/etl_to_clickhouse.py
```
