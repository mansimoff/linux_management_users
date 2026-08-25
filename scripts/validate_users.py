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

REQUIRED_FIELDS = [
    "login",
    "firstname",
    "lastname",
    "email",
    "groups",
]

EMAIL_PATTERN = re.compile(r"^[\w.\-]+@company\.net$")
LOGIN_PATTERN = re.compile(r"^[a-z0-9.]+$")


def validate_users(path: str) -> list[str]:
    errors = []

    # ── 1. Читаем и парсим YAML ──────────────────────────────────────────
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

    # Храним уже встреченные login.
    # Формат:
    # {
    #     "ivanov": 1,
    #     "petrov": 2,
    # }
    #
    # Значение — номер пользователя, у которого login встретился впервые.
    seen_logins = {}

    # ── 3. Проверяем каждого пользователя ─────────────────────────────────
    for i, user in enumerate(data["users"], start=1):

        # Сначала проверяем тип записи.
        # Это важно, потому что user может оказаться строкой,
        # числом, списком и т.д.
        if not isinstance(user, dict):
            label = f"пользователь #{i}"
            errors.append(f"{label}: запись должна быть словарём")
            continue

        # Для понятных сообщений об ошибках берём login, если он есть.
        login_for_label = user.get("login", "не указан")
        label = f"пользователь #{i} (login: {login_for_label})"

        # ── 3.1 Проверка обязательных полей ───────────────────────────────
        for field in REQUIRED_FIELDS:
            if field not in user:
                errors.append(
                    f"{label}: отсутствует поле '{field}'"
                )

            elif user[field] is None:
                errors.append(
                    f"{label}: поле '{field}' равно null"
                )

            elif isinstance(user[field], str) and not user[field].strip():
                errors.append(
                    f"{label}: поле '{field}' пустое"
                )

        # ── 3.2 Проверка login ────────────────────────────────────────────
        login = user.get("login")

        # Проверяем тип login отдельно.
        if login is not None and not isinstance(login, str):
            errors.append(
                f"{label}: поле 'login' должно быть строкой"
            )

        # Проверяем login только если это строка и она не пустая.
        if isinstance(login, str) and login.strip():

            # Недопустимые символы.
            if not LOGIN_PATTERN.fullmatch(login):
                errors.append(
                    f"{label}: недопустимые символы в login '{login}' "
                    f"— только строчные буквы a-z, цифры 0-9 и точка"
                )

            # ── 3.3 Проверка уникальности login ──────────────────────────
            #
            # Проверяем именно исходное значение login.
            # Например:
            #
            #   ivanov
            #   ivanov
            #
            # будет обнаружено как дубликат.
            if login in seen_logins:
                first_user_number = seen_logins[login]

                errors.append(
                    f"{label}: дублирующийся login '{login}' "
                    f"— такой login уже используется "
                    f"у пользователя #{first_user_number}"
                )
            else:
                # Запоминаем первый экземпляр login.
                seen_logins[login] = i

        # ── 3.4 Проверка email ────────────────────────────────────────────
        email = user.get("email")

        if isinstance(email, str) and email.strip():
            if not EMAIL_PATTERN.fullmatch(email):
                errors.append(
                    f"{label}: некорректный email '{email}' "
                    f"— ожидается формат name@company.net"
                )

        # ── 3.5 Проверка groups ───────────────────────────────────────────
        groups = user.get("groups")

        if groups is not None:

            # groups может быть списком.
            if isinstance(groups, list):

                if len(groups) == 0:
                    errors.append(
                        f"{label}: поле 'groups' — пустой список"
                    )

                else:
                    for g in groups:
                        if not str(g).strip():
                            errors.append(
                                f"{label}: в поле 'groups' "
                                f"есть пустое значение"
                            )

            # Или groups может быть строкой.
            elif isinstance(groups, str):

                if not groups.strip():
                    errors.append(
                        f"{label}: поле 'groups' пустая строка"
                    )

            # Все остальные типы запрещены.
            else:
                errors.append(
                    f"{label}: поле 'groups' должно быть "
                    f"строкой или списком"
                )

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
        # Для отчёта считаем количество пользователей.
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        count = len(data["users"])

        print(
            f"✓ OK — {count} пользователей, "
            f"все поля корректны, login уникальны"
        )

        sys.exit(0)


if __name__ == "__main__":
    main()
