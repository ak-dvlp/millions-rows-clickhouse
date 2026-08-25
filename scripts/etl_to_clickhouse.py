import time
import clickhouse_connect  # type: ignore

# Настройки подключения
CH_HOST = '127.0.0.1'
CH_PORT = 8124  # Используем внешний HTTP-порт для clickhouse-connect
CH_USER = 'bi_user'
CH_PASSWORD = 'bi_password'
CH_DATABASE = 'ecommerce_olap'


def run_etl():
    print("⏳ Подключение к ClickHouse...")
    client = clickhouse_connect.get_client(
        host=CH_HOST, port=CH_PORT, username=CH_USER, password=CH_PASSWORD
    )

    # Создание базы данных, если её нет
    client.command(f"CREATE DATABASE IF NOT EXISTS {CH_DATABASE}")

    # Удаляем старую аналитическую таблицу, если она осталась от прошлых попыток
    client.command(f"DROP TABLE IF EXISTS {CH_DATABASE}.superset_flat_analytics")

    # SQL для создания плоской таблицы
    create_table_ddl = f"""
    CREATE TABLE IF NOT EXISTS {CH_DATABASE}.superset_flat_analytics
    (
        order_id UInt32,
        order_date Date,
        order_status LowCardinality(String),
        payment_method LowCardinality(String),
        shipping_method LowCardinality(String),
        order_total_amount Decimal(18, 2),
        order_notes Nullable(String),
        orderline_id UInt16,
        quantity UInt8,
        unit_price Decimal(18, 2),
        subtotal Decimal(18, 2),
        line_status LowCardinality(String),
        line_notes Nullable(String),
        product_id UInt32,
        sku String,
        product_name String,
        product_description String,
        category LowCardinality(String),
        subcategory LowCardinality(String),
        brand LowCardinality(String),
        product_price Decimal(18, 2),
        product_cost Decimal(18, 2),
        stock_quantity UInt32,
        weight_kg Decimal(8, 3),
        product_status LowCardinality(String),
        rating_average Decimal(3, 2),
        review_count UInt32,
        customer_id UInt32,
        firstname String,
        lastname String,
        age UInt8,
        postalcode String,
        city LowCardinality(String)
    )
    ENGINE = MergeTree()
    ORDER BY (order_date, category, brand, city);
    """

    print("⏳ Создание плоской таблицы superset_flat_analytics...")
    client.command(create_table_ddl)
    print("✅ Таблица superset_flat_analytics успешно создана.")

    print("⏳ Создание быстрых временных таблиц в памяти...")
    client.command(
        f"DROP TABLE IF EXISTS {CH_DATABASE}.tmp_products"
    )  # Защита от дублей
    client.command(
        f"DROP TABLE IF EXISTS {CH_DATABASE}.tmp_customers"
    )  # Защита от дублей
    client.command(
        f"DROP TABLE IF EXISTS {CH_DATABASE}.tmp_orders"
    )  # Защита от дублей

    client.command(
        f"CREATE TABLE {CH_DATABASE}.tmp_products ENGINE = Memory AS SELECT * FROM file('parquet/product_part1.parquet', Parquet)"
    )
    client.command(
        f"CREATE TABLE {CH_DATABASE}.tmp_customers ENGINE = Memory AS SELECT * FROM file('parquet/customer_part1.parquet', Parquet)"
    )
    client.command(
        f"CREATE TABLE {CH_DATABASE}.tmp_orders ENGINE = Memory AS SELECT * FROM file('parquet/order_part*.parquet', Parquet)"
    )
    print("✅ Временные таблицы успешно созданы.")

    # SQL для вставки данных
    insert_dml = f"""
    INSERT INTO {CH_DATABASE}.superset_flat_analytics
    SELECT
        o.order_id, o.order_date, o.status AS order_status, o.payment_method, o.shipping_method,
        o.total_amount AS order_total_amount, o.notes AS order_notes,
        ol.orderline_id, ol.quantity, ol.unit_price, ol.subtotal, ol.status AS line_status, ol.notes AS line_notes,
        p.product_id, p.sku, p.name AS product_name, p.description AS product_description,
        p.category, p.subcategory, p.brand, p.price AS product_price, p.cost AS product_cost,
        p.stock_quantity, p.weight_kg, p.status AS product_status, p.rating_average, p.review_count,
        c.customer_id, c.firstname, c.lastname, c.age, c.postalcode, c.city
    FROM (
        SELECT * FROM file('parquet/orderline_part*.parquet', Parquet)
    ) AS ol
    INNER JOIN {CH_DATABASE}.tmp_orders AS o ON ol.order_id = o.order_id
    INNER JOIN {CH_DATABASE}.tmp_products AS p ON ol.product_id = p.product_id
    INNER JOIN {CH_DATABASE}.tmp_customers AS c ON o.customer_id = c.customer_id
    SETTINGS max_memory_usage = 10000000000;
    """

    print("⏳ Запуск денормализации и импорта строк из Parquet...")
    start_time = time.time()

    client.command(insert_dml)

    end_time = time.time()
    duration = end_time - start_time
    print(f"✅ Импорт завершён. Время выполнения: {duration:.2f} сек.")

    # Очистка ресурсов оперативной памяти ClickHouse
    print("⏳ Удаление временных таблиц...")
    client.command(f"DROP TABLE IF EXISTS {CH_DATABASE}.tmp_products")
    client.command(f"DROP TABLE IF EXISTS {CH_DATABASE}.tmp_customers")
    client.command(f"DROP TABLE IF EXISTS {CH_DATABASE}.tmp_orders")
    print("✅ Временные таблицы удалены.")

    # Проверка результата
    print("⏳ Проверка загруженных данных...")
    count_res = client.command(
        f"SELECT count() FROM {CH_DATABASE}.superset_flat_analytics"
    )
    print(f"Общее количество строк таблицы: {count_res:,}")

    client.close()


if __name__ == '__main__':
    run_etl()
