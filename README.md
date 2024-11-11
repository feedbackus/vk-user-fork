
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
python vk_user_info.py <TOKEN> <ID> --output <FILENAME>
```

**Параметры:**

- `<TOKEN>` — VK API токен.
- `<ID>` — ID пользователя VK.
- `--output` — необязательный параметр. Имя файла для сохранения результата (по умолчанию `output.json`).

### Пример:
```bash
python main.py vk1.a.abc 1 --output user_data.json
```

Этот пример извлечет данные о пользователе с ID `1` и сохранит их в файл `user_data.json`.
