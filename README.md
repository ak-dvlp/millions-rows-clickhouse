# millions-rows-clickhouse

#### Инженерный проект по построению высокопроизводительного аналитического конвейера данных на базе ClickHouse и Apache Superset.

Основная цель — обеспечить эффективную загрузку, хранение и визуализацию больших объёмов данных (более 13 млн строк).

#### 🗺️ Конвейер данных:

Parquet-файлы ➡️ ClickHouse (OLAP) ➡️ Apache Superset (Визуализация данных).

## Развёртывание и настройка

#### Клонирование репозитория

Клонируйте репозиторий и перейдите в директорию проекта. Папка `data/parquet` занимает объём порядка `230 МиБ`, так что клонирование займёт большее количество времени чем обычно.

#### Создание виртуального окружения для работы скриптов папки `scripts`

Для успешного выполнения дальнейших шагов в вашей системе должен быть установлен `Poetry`. После установки `Poetry`, выполните установку пакетов командой:

```bash
poetry install
```

Если вы работаете в `VS Code`, нажмите комбинацию клавиш `Ctrl + Shift + P`, наберите в поисковом поле `Python: Select Interpreter` и выберите пункт, содержащий имя виртуального окружения вашего проекта.

Примерный вид корректного пункта:

```bash
Python 3.x.x ('.venv': Poetry) ./.venv/bin/python
```

Если нужного интерпретатора нет, добавьте его вручную или попробуйте выполнить команды:

```bash
poetry config virtualenvs.in-project true
poetry env remove --all
poetry install

```

#### Запуск службы Docker и настройка прав группы

Перед запуском контейнеров убедитесь, что сама служба `Docker` запущена в вашей системе. Без этого команды управления контейнерами будут выдавать ошибку подключения к сокету.

Проверка статуса службы:

```bash
sudo systemctl status docker
```

В строке `Active:` должно быть указано `active (running)` зелёным цветом.

Запуск службы (если она остановлена):

```bash
sudo systemctl start docker
```

Если вы как пользователь не являетесь членом группы `docker`, то будете вынуждены использовать `sudo` в большинстве команд. Для того чтобы упростить себе работу, выполните команды в раскрывающемся списке ниже.

<details>
<summary>Пошаговая настройка прав (без перезагрузки)</summary>

Создание группы:

```bash
sudo groupadd docker
```

Добавление себя в группу:

```bash
sudo usermod -aG docker $USER
```

Обновление конфигурации групп текущей сессии (необходимо, если не хотите перезагружать компьютер)

```bash
newgrp docker
```

Проверка вашего членства в группе `docker`:

```bash
id $USER
```

Примерный вывод (где вместо `aleks` будет ваше имя пользователя):

```text
uid=1001(aleks) gid=1001(aleks) groups=1001(aleks),10(wheel),999(docker)
```

</details>

#### Развёртывание и запуск контейнеров

```bash
docker compose up -d
```

Дождитесь окончания создания изолированных хранилищ данных, создания виртуальной сети и запуска всех контейнеров:

---

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
