#!/usr/bin/env python3
"""
Валидация files/users.yml
Проверяет:
  - корректность yaml синтаксиса
  - наличие и непустоту обязательных полей
  - формат email (@company.net)
  - допустимые символы в login
"""

import yaml
import sys
import re

USERS_FILE = "files/users.yml"
REQUIRED_FIELDS = ["login", "firstname", "lastname", "email", "groups"]
EMAIL_PATTERN = re.compile(r'^[\w.\-]+@company\.net$')
LOGIN_PATTERN = re.compile(r'^[a-z0-9.]+$')


def validate_users(path: str) -> list[str]:
    errors = []

    # ── 1. Читаем и парсим yaml ───────────────────────────────────────────
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        return [f"Файл не найден: {path}"]
    except yaml.YAMLError as e:
        return [f"Невалидный yaml синтаксис: {e}"]

    # ── 2. Проверяем структуру файла ──────────────────────────────────────
    if not isinstance(data, dict):
        return ["Файл должен содержать словарь верхнего уровня"]

    if "users" not in data:
        return ["Отсутствует обязательная секция 'users:'"]

    if not data["users"]:
        return ["Секция 'users:' пустая — нет ни одного пользователя"]

    if not isinstance(data["users"], list):
        return ["Секция 'users:' должна быть списком"]

    # ── 3. Проверяем каждого пользователя ────────────────────────────────
    for i, user in enumerate(data["users"], start=1):
        # Для понятных сообщений об ошибках берём login если есть
        label = f"пользователь #{i} (login: {user.get('login', 'не указан')})"

        if not isinstance(user, dict):
            errors.append(f"{label}: запись должна быть словарём")
            continue

        # Проверка обязательных полей
        for field in REQUIRED_FIELDS:
            if field not in user:
                errors.append(f"{label}: отсутствует поле '{field}'")
            elif user[field] is None:
                errors.append(f"{label}: поле '{field}' равно null")
            elif isinstance(user[field], str) and not user[field].strip():
                errors.append(f"{label}: поле '{field}' пустое")

        # Проверка login — только строчные латинские буквы, цифры, точка
        login = user.get("login", "")
        if login and not LOGIN_PATTERN.match(str(login)):
            errors.append(
                f"{label}: недопустимые символы в login '{login}' "
                f"— только строчные буквы a-z, цифры 0-9 и точка"
            )

        # Проверка email
        email = user.get("email", "")
        if email and not EMAIL_PATTERN.match(str(email)):
            errors.append(
                f"{label}: некорректный email '{email}' "
                f"— ожидается формат name@company.net"
            )

        # Проверка groups — должно быть строкой или списком, не пустым
        groups = user.get("groups")
        if groups is not None:
            if isinstance(groups, list):
                if len(groups) == 0:
                    errors.append(f"{label}: поле 'groups' — пустой список")
                else:
                    for g in groups:
                        if not str(g).strip():
                            errors.append(f"{label}: в поле 'groups' есть пустое значение")
            elif isinstance(groups, str):
                if not groups.strip():
                    errors.append(f"{label}: поле 'groups' пустая строка")
            else:
                errors.append(f"{label}: поле 'groups' должно быть строкой или списком")

    return errors


def main():
    print(f"Проверка {USERS_FILE}...")
    errors = validate_users(USERS_FILE)

    if errors:
        print(f"\n❌ Найдено ошибок: {len(errors)}")
        for err in errors:
            print(f"   ✗ {err}")
        sys.exit(1)
    else:
        # Для отчёта считаем количество пользователей
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        count = len(data["users"])
        print(f"✓ OK — {count} пользователей, все поля корректны")
        sys.exit(0)


if __name__ == "__main__":
    main()
