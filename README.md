# Custom Single-Sign-On based on JsonWebToken
## With Oauth providers: Yandex & VK

Кастомный сервис авторизации поддерживает различные функции:

* регистрация
* взаимодействие с сервисом отправки сообщений в телеграм чат
* вход через внешних провайдеров
* валидацию и обновление токенов


### Подробнее

* GET http://localhost:8080/docs - swagger документация

* GET http://localhost:8000/auth/login/{provider} , provider = [yandex, vk] - эндпоинт для редиректа на провайдера авторизации
* POST http://localhost:8000/auth/register - эндпоинт для регистрации и получения пары токенов
* POST http://localhost:8000/auth/refresh - эндпоинт для обновления access токена
* GET http://localhost:8000/auth/validate - эндпоинт для валидации токена
* GET http://localhost:8000/auth/callback/{provider} - эндпоинты для обратного вызова которые будут обрабатывать ответы от серверов авторизации


### Сервисы:

**[1]** app - основной сервис, отвечающий за бизнес логику авторизации \
**[2]** notifier - сервис, в фоновом режиме слушающий кафку \
**[3]** postgres - база данных для персистентного хранения информации о юзерах \
**[4]** kafka (+ zookeper) - сконфигурированный брокер для обеспечения малой связности

Для запуска достаточно из корневой директории выполнить:
```angular2html
docker-compose up --build
```

Образы будут собраны автоматически на основе докерфайлоd из папки /docker

Чтобы сервисы работали корректно - необходимо добавить .env файлы в директорию каждого сервиса.
Пример .env для tg_notifier:
```angular2html
# kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
# топик который будет слушаться
NOTIFY_TOPIC=user_notifications

# tg Bot
# токен для получения доступа к тг-апи
TELEGRAM_BOT_TOKEN=
# айди чата куда нужно слать приветствия, обязательно чтоб бот был в чате админом
TELEGRAM_CHAT_ID=
```

Пример .env для app (auth-service):
```angular2html
# настройки jwt приватных ключей
JWT_SECRET=FIXME
JWT_ACCESS_SECRET=FIXME
JWT_REFRESH_SECRET=FIXME
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# OAuth для Yandex и VK
YANDEX_CLIENT_ID=FIXME
YANDEX_CLIENT_SECRET=FIXME

VK_CLIENT_ID=FIXME
VK_CLIENT_SECRET=FIXME
VK_AUTHORIZE_URL=https://oauth.vk.com/authorize
VK_TOKEN_ENDPOINT=https://oauth.vk.com/access_token
VK_API_BASE_URL=https://api.vk.com/method/
VK_API_VERSION=5.199
VK_SCOPE=email

# конфиг для коннекта к бд, значения взяты из docker-compose и для безопасности можно изменить
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
DB_HOST=db
DB_PORT=5432
POSTGRES_DB=mydatabase

# конфигурация кафки и топика, куда будут слаться приветсьвия
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
NOTIFY_TOPIC=user_notifications
```