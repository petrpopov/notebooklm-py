# notebooklm-py (fork)

> **Это форк** оригинального проекта <https://github.com/teng-lin/notebooklm-py>.
>
> Основная цель форка — обойти проблему с `notebooklm login`, который запускает браузер в изолированном окружении Playwright, где не работают кнопки входа Google SSO.
>
> **Решение:** импортируйте cookies напрямую из вашего основного профиля Chrome без открытия браузера.
>
> Также добавлена поддержка **SOCKS5 proxy** — на macOS автоматически определяется системный proxy (через `scutil --proxy`), ручная настройка env vars не требуется.

---

## Установка из этого репозитория

```bash
# Клонируйте форк
git clone https://github.com/petrpopov/notebooklm-py.git
cd notebooklm-py

# Установите пакет в editable-режиме с зависимостями для Chrome cookies
pip install -e '.[chrome]'
```

> **Примечание:** флаг `-e` (editable) нужен, чтобы изменения в исходниках подхватывались без переустановки.

---

## Вход через импорт cookies из Chrome (macOS)

Вместо `notebooklm login` с браузером Playwright:

```bash
# Импортировать cookies из профиля Chrome по умолчанию
notebooklm auth import-chrome

# Или указать другой профиль (например, "Profile 1")
notebooklm auth import-chrome --profile "Profile 1"

# Проверить аутентификацию
notebooklm auth check --test
```

После импорта cookies все команды работают как обычно:

```bash
notebooklm list
notebooklm use <notebook_id>
notebooklm ask "What are the key themes?"
notebooklm generate audio "make it engaging" --wait
```

---

## Работа через proxy (SOCKS5/HTTP)

На macOS системный proxy определяется **автоматически** из настроек сети (`scutil --proxy`). Если у вас настроен SOCKS5 или HTTP proxy (например, через Xray, V2Ray), `notebooklm` подхватит его без дополнительной конфигурации:

```bash
# Просто работает — proxy определяется из системных настроек macOS
notebooklm list
```

При необходимости можно задать proxy явно через переменные окружения (они имеют приоритет над системными настройками):

```bash
export ALL_PROXY=socks5://127.0.0.1:10808
notebooklm list
```

Зависимость `httpx[socks]` (пакет `socksio`) уже включена — SOCKS5 proxy работает из коробки.

---

## Документация

Вся документация находится в оригинальном репозитории:

- **[CLI Reference](https://github.com/teng-lin/notebooklm-py/blob/main/docs/cli-reference.md)**
- **[Python API](https://github.com/teng-lin/notebooklm-py/blob/main/docs/python-api.md)**
- **[Configuration](https://github.com/teng-lin/notebooklm-py/blob/main/docs/configuration.md)**
- **[Troubleshooting](https://github.com/teng-lin/notebooklm-py/blob/main/docs/troubleshooting.md)**

---

## Оригинал

Исходный проект: <https://github.com/teng-lin/notebooklm-py>
