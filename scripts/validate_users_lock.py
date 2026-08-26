import yaml
import sys
import re


FILE_PATH = "files/users_lock.yml"

REQUIRED_FIELDS = [
    "login",
    "firstname",
    "lastname",
]

LOGIN_PATTERN = re.compile(r"^[a-z0-9.]+$")


def fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)


def ok(msg):
    print(f"✓ {msg}")


# ── 1. Читаем и парсим YAML ───────────────────────────────────────────────
try:
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

except FileNotFoundError:
    fail(f"Файл не найден: {FILE_PATH}")

except yaml.YAMLError as e:
    fail(f"Невалидный YAML: {e}")

except OSError as e:
    fail(f"Не удалось прочитать файл: {e}")


# ── 2. Полностью пустой файл разрешён ─────────────────────────────────────
#
# yaml.safe_load() для полностью пустого файла возвращает None.
#
# Пустой users_lock.yml означает:
# "заблокированных пользователей нет"
if data is None:
    ok("users_lock.yml пуст — заблокированных пользователей нет")
    sys.exit(0)


# ── 3. Проверяем структуру YAML ───────────────────────────────────────────
if not isinstance(data, dict):
    fail("Корневой элемент YAML должен быть словарём")

if "users" not in data:
    fail("Нет ключа 'users'")

if not isinstance(data["users"], list):
    fail("'users' должен быть списком")


users = data["users"]


# ── 4. Пустой список users тоже разрешён ──────────────────────────────────
if len(users) == 0:
    ok("users_lock.yml корректен — список users пуст")
    sys.exit(0)


# ── 5. Проверяем пользователей ────────────────────────────────────────────
seen_logins = {}


for i, user in enumerate(users, start=1):

    if not isinstance(user, dict):
        fail(f"Элемент #{i} должен быть словарём")

    # Проверяем обязательные поля
    for field in REQUIRED_FIELDS:

        if field not in user:
            fail(
                f"Элемент #{i}: "
                f"отсутствует поле '{field}'"
            )

        if user[field] is None:
            fail(
                f"Элемент #{i}: "
                f"поле '{field}' равно null"
            )

        if not str(user[field]).strip():
            fail(
                f"Элемент #{i}: "
                f"поле '{field}' пустое"
            )

    # ── Проверка login ────────────────────────────────────────────────────
    login = user["login"]

    if not isinstance(login, str):
        fail(
            f"Элемент #{i}: "
            f"поле 'login' должно быть строкой"
        )

    # Та же регулярка, что и в validate_users.py:
    # только строчные a-z, цифры 0-9 и точка
    if not LOGIN_PATTERN.fullmatch(login):
        fail(
            f"Элемент #{i}: "
            f"недопустимые символы в login '{login}' "
            f"— только строчные буквы a-z, цифры 0-9 и точка"
        )

    # ── Проверка уникальности login ──────────────────────────────────────
    if login in seen_logins:
        first_element = seen_logins[login]

        fail(
            f"Элемент #{i}: "
            f"дублирующийся login '{login}' "
            f"— такой login уже указан "
            f"в элементе #{first_element}"
        )

    seen_logins[login] = i


# ── 6. Всё хорошо ─────────────────────────────────────────────────────────
ok(
    f"users_lock.yml корректен — "
    f"{len(users)} пользователей, login уникальны"
)

