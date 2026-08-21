import yaml
import sys


FILE_PATH = "files/users_lock.yml"


def fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)


def ok(msg):
    print(f"✓ {msg}")


try:
    with open(FILE_PATH, "r") as f:
        data = yaml.safe_load(f)
except Exception as e:
    fail(f"YAML не читается: {e}")


# 1. проверка root key
if "users" not in data:
    fail("Нет ключа 'users'")

if not isinstance(data["users"], list):
    fail("'users' должен быть списком")


users = data["users"]

if len(users) == 0:
    fail("Список users пуст")


# 2. проверка каждого пользователя
for i, user in enumerate(users, start=1):

    if not isinstance(user, dict):
        fail(f"Элемент #{i} должен быть dict")

    required_fields = ["login", "firstname", "lastname"]

    for field in required_fields:
        if field not in user:
            fail(f"Элемент #{i}: отсутствует поле '{field}'")

        if not str(user[field]).strip():
            fail(f"Элемент #{i}: поле '{field}' пустое")

    # логин без пробелов
    if " " in user["login"]:
        fail(f"Элемент #{i}: login не должен содержать пробелы")


ok("users_lock.yml корректен")
