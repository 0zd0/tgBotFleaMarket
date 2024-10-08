# Tg Bot Барахолка

Ссылка на скачивание - https://codeload.github.com/0zd0/tgBotFleaMarket/zip/refs/heads/master

### Запуск локально(конечно же с работающим postgres & redis)
```sh
python -m bot --mode=dev
```

Запуск в двух режимах(mode):
- `dev`
- `prod`

(в деплое с Docker работает в `prod` режиме)

### Config
Конфиг в зависимости от режима создается из примера `config.sample.toml` в `config.{mode}.toml`

![Screenshot_148](https://github.com/0zd0/tgBotFleaMarket/assets/67220210/4ebc1541-b027-40dd-9386-81b1c0fff7af)

#### Параметры
Секция telegram:

- `bot_token` - токена тг бота
- `db_name` - название базы данных в postgres (flea)
- `start_notify` - отправлять ли, что бот запустился
- `start_notify_ids` - массив id, кому отправлять о запуске
- `channel_id` - id канала, куда отправлять объявления
- `support_username` - юзернейм(без @), кто будет указан в контактах
- `bot_username` - юзернейм(без @) бота
- `channel_username` - юзернейм(без @) канала куда постится
- `max_ads_per_day` - максимальное кол-во объявлений в день (2)
- `advertising` - текст рекламы в двойных кавычках, разделение на строки с помощью символа "\n"
- `advertising_every_ad` - вставлять рекламу в каждое n объявление (4)
- `reminder_if_no_activity_seconds` - время в секундах, через сколько неактивности напоминать юзеру

Секция redis:

- `host` - хост (redis)
- `port` - порт (6379)

Секция postgres:

- `host` - хост (postgres)
- `host` - порт (5432)
- `login` - логин (postgres)
- `password` - пароль

установить так же логин и пароль в docker-compose.yml у postgres

Секция curse_words:

- `file_path` - путь до .txt файла с исключающими словами при создании объявления


### Остальные папки
- `bot` - исполняемый модуль с ботом
- `postgres` - папка для запуска postgres в docker
- `redis` - папка для запуска redis в docker
- `alembic` - миграции бд postgres


### ID в TG
Для того, чтобы узнать id у канала или человека:
заходим в https://web.telegram.org/, переходим на нужный канал/человека(если нужно узнать свой id, то переходим в Saved Messages/Избранное) и в ссылке будет id.
Пример https://web.telegram.org/a/#-1001988715526: ID тут -1001988715526


## Пример деплоя на сервер Ubuntu
### Файлы
создать на сервере папку `flea`, закинуть туда все файлы с гитхаба из архива. Через консоль перейти в нужную папку `cd ПУТЬ`(`cd flea`)
### Установка Docker
запустить файл `docker.sh` через консоль `sh docker.sh` или `sh ./docker.sh` или `./docker.sh` или `bash docker.sh`, на каждом сервере встречалось по разному. Со всем соглашаться и жать `Enter`
### Установка Docker-compose
запустить файл `compose.sh`, в конце он должен показать версию
### Создание docker сети для бота
Ввести команду `docker network create bot`
### Поднятие бд
Две папки, `postgres` и `redis` перенести в нужные места(или оставить в `flea`) и перейти в каждую из них по очереди через консоль и ввести команду `docker-compose up -d --build`

Теперь через `docker ps` будут показываться статусы контейнеров у бд

### Запуск бота
в самой папке `flea` запустить команду `docker-compose up -d --build`

остановить можно командой `docker-compose down`, аналогично и контейнеры бд(перейдя в нужную папку) 
