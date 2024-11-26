
## Запуск

1. Получить [токен](https://vkhost.github.io)
2. Получить [id пользователя](https://regvk.com/id/)
3. Установить виртуальное окружение:
```bash
python -m venv venv
```
4. Запустить окружение:
```bash
venv/scripts/activate
```
5. Установить зависимости:
```bash
pip install -r requirements.txt
```
6. Запустить скрипт, передав необходимые параметры:
```bash
python main.py --token <TOKEN> --user_id <ID> --query <TYPE> --depth <INT> --neo4j_uri <URI> --neo4j_login <LOGIN> --neo4j_pass <PASSWORD> --clear
```

**Параметры:**
--token — access token VK.
--user_id — ID пользователя VK.
--query — (необязательный) Тип запроса для выполнения в базе данных. Возможные значения: users_count, groups_count, top_users, top_groups, mutual_followers.
--depth — (необязательный) Глубина извлечения информации о пользователе (по умолчанию 2).
--neo4j_uri — (необязательный) URI для подключения к базе данных Neo4j (по умолчанию neo4j://localhost:7687).
--neo4j_login — (необязательный) Логин для подключения к базе данных Neo4j (по умолчанию neo4j).
--neo4j_pass — (необязательный) Пароль для подключения к базе данных Neo4j (по умолчанию 11111111).
--clear — (необязательный) Флаг для очистки базы данных перед запуском.

### Примеры:
```bash
python main.py --token vk1.a.abc --user_id 1 --query users_count
```
выведет количество пользователей в бд
```bash
python main.py --token vk1.a.abc --user_id 1 --clear --depth 3
```
очистит бд, сгенерирует значения с глубиной 3 и запишет их в бд
