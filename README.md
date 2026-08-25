# millions-rows-clickhouse

#### Инженерный проект по построению высокопроизводительного аналитического конвейера данных на базе ClickHouse и Apache Superset.

Основная цель — обеспечить эффективную загрузку, хранение и визуализацию больших объёмов данных. Итоговым источником для `Apache Superset` выступает денормализованная таблица в `ClickHouse` объёмом 13 миллионов строк, оптимизированная для быстрых агрегаций и построения сводных отчётов.

#### 🗺️ Конвейер данных:

Parquet-файлы ➡️ ClickHouse (OLAP) ➡️ Apache Superset (Визуализация данных).

## Развёртывание и настройка

#### Клонирование репозитория

Клонируйте репозиторий и перейдите в директорию проекта. Папка `data/parquet` занимает объём порядка `230 МиБ`, так что клонирование займёт большее количество времени чем обычно.

#### Создание виртуального окружения для работы скрипта папки `scripts`

Для успешного выполнения дальнейших шагов в вашей системе должен быть установлен `Poetry`. После установки `Poetry`, выполните установку пакета `clickhouse-connect` командой:

```bash
poetry install
```

Если вы работаете в `VS Code`, нажмите комбинацию клавиш `Ctrl + Shift + P`, наберите в поисковом поле `Python: Select Interpreter` и выберите пункт, содержащий имя виртуального окружения вашего проекта.

Примерный вид корректного пункта:

```bash
Python 3.x.x ('.venv': Poetry) ./.venv/bin/python
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

```text
 ✔ Network millions-rows-clickhouse_default               Created                                                                                                                                     0.0s
 ✔ Volume millions-rows-clickhouse_superset_home_millions Created                                                                                                                                     0.0s
 ✔ Volume millions-rows-clickhouse_chdata_millions        Created                                                                                                                                     0.0s
 ✔ Container superset_millions_rows                       Started                                                                                                                                     0.3s
 ✔ Container ecommerce_clickhouse_millions                Started
```

Выполните команду для вывода сообщений журнала в реальном времени:

```bash
docker compose logs superset -f
```

Дождитесь следующих сообщений журнала:

```text
superset_millions_rows  | ⏳ Запуск Superset...
superset_millions_rows  | [2026-08-25 21:29:05 +0000] [114] [INFO] Starting gunicorn 23.0.0
superset_millions_rows  | [2026-08-25 21:29:05 +0000] [114] [INFO] Listening at: http://0.0.0.0:8088 (114)
superset_millions_rows  | [2026-08-25 21:29:05 +0000] [114] [INFO] Using worker: gthread
superset_millions_rows  | [2026-08-25 21:29:05 +0000] [115] [INFO] Booting worker with pid: 115
```

Выйдите из режима вывода сообщений журнала при помощи комбинации горячих клавиш `Ctrl + C`.

#### Загрузка данных из Parquet-файлов в ClickHouse

Выполните команду запуска ETL-скрипта для `ClickHouse`:

```bash
poetry run python scripts/etl_to_clickhouse.py
```

Дождитесь окончания выполнения скрипта:

```text
⏳ Подключение к ClickHouse...
⏳ Создание плоской таблицы superset_flat_analytics...
✅ Таблица superset_flat_analytics успешно создана.
⏳ Создание быстрых временных таблиц в памяти...
✅ Временные таблицы успешно созданы.
⏳ Запуск денормализации и импорта строк из Parquet...
✅ Импорт завершён. Время выполнения: 20.15 сек.
⏳ Удаление временных таблиц...
✅ Временные таблицы удалены.
⏳ Проверка загруженных данных...
Общее количество строк таблицы: 13,000,000
```

На ПК со следующими характеристиками:

```text
ОЗУ: 16 ГиБ
Процессор: Intel Core i7‑8700, 3.20 ГГц
```

этап формирования денормализованной таблицы и загрузки данных из Parquet-файлов объёмом `230 МиБ` в `ClickHouse` занимает порядка 20 секунд.

---

#### Настройка Apache Superset в веб клиенте

Перейдите по адресу: [http://localhost:8088](http://localhost:8088)
Введите имя пользователя `admin` и пароль `admin`

<img width="622" height="500" alt="image" src="https://github.com/user-attachments/assets/c1ef2f81-0759-4d4d-bc0c-656807f45cf6" />

Откройте выпадающее меню нажав в правой части навигационного меню на иконку `+`. Затем нажмите: `Data` => `Connect Database`.

<img width="622" height="500" alt="image" src="https://github.com/user-attachments/assets/805cf2cf-941c-48cf-b778-a2800d0d7cc1" />

Шаг 1. В выпадающем меню поля выбора `Supported databases` выберите `ClickHouse`. Отсутствие данного пункта может означает неудачную установку драйверов базы данных.

<img width="622" height="500" alt="image" src="https://github.com/user-attachments/assets/1d31f07c-c877-4f62-9f8e-971b494b47e4" />

Шаг 2. В нижней части модального окна нажмите на метку `Connect this database with a SQLAlchemy URI string instead`:

<img width="492" height="500" alt="image" src="https://github.com/user-attachments/assets/fd221265-4e2c-4b48-9938-c5a38f6a0d7c" />

введите в поле `SQLAlchemy URI*` строку ниже и нажмите на кнопку `Test connection`:

```text
clickhouse+connect://bi_user:bi_password@127.0.0.1:8124/ecommerce_olap
```

<img width="461" height="500" alt="image" src="https://github.com/user-attachments/assets/aa0e64bb-f89f-40e2-b383-544bdffe5db7" />

Нажмите на кнопку `Connect`.

#### Проверка наличия денормализованной таблицы

В левой части навигационного меню нажмите на `SQL`. В выпадающем меню выберите пункт `SQL Lab`.

<img width="461" height="500" alt="image" src="https://github.com/user-attachments/assets/3e603af9-fff1-4f22-befe-a8820098f8d9" />

Нажмите на вкладку `Add a new tab`

<img width="461" height="500" alt="image" src="https://github.com/user-attachments/assets/d48d7b4c-c017-4688-ac65-b0a4a7b18663" />

Выполните запрос:

```sql
SELECT * FROM ecommerce_olap.superset_flat_analytics
LIMIT 100;
```

Нажмите на кнопку `Run`

<img width="910" height="500" alt="image" src="https://github.com/user-attachments/assets/ce9a5ddf-2e70-4d7e-88b2-01e1bfbfd6f9" />  
<img width="910" height="500" alt="image" src="https://github.com/user-attachments/assets/38e86fe8-0df3-434c-92a3-94459e40eba6" />  
<img width="910" height="500" alt="image" src="https://github.com/user-attachments/assets/045e8ea7-1a24-4d0b-8abe-76c41965a016" />

#### Работа с данными через ClickHouse

Перейдите по адресу: [http://localhost:8123/play](http://localhost:8124/play)

<img width="910" height="500" alt="image" src="https://github.com/user-attachments/assets/a4a69ec9-b2f0-493a-8b01-a105e7f55622" />

Заполните поля `user` и `password` значениями `bi_user` и `bi_password` соответственно (если поля скрыты, нажмите на иконку ключ).

Выполните какой-либо запрос, например:

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

Нажмите на кнопку `Run`.

<img width="910" height="500" alt="image" src="https://github.com/user-attachments/assets/803e22ad-2460-478e-9593-cd11212a396d" />

## Заключение

Инфраструктура готова к созданию графиков и витрин интерактивной аналитики в `Apache Superset`.
