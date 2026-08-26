#!/usr/bin/env python3
"""
Валидация yaml синтаксиса ansible файлов проекта.
Проверяет что файлы читаются и не сломаны синтаксически.

Использование:
  python3 validate_yml.py                    # проверить все файлы
  python3 validate_yml.py files/users.yml    # проверить конкретный файл
"""
import yaml
import sys
import os


# Файлы которые проверяем по умолчанию
DEFAULT_FILES = [
    "create.yml",
    "files/users.yml",
    "files/users_lock.yml",
    "inventory/hosts.yml",
]


# Файлы, которым разрешено быть полностью пустыми.
# Пустой users_lock.yml означает, что заблокированных пользователей нет.
ALLOW_EMPTY_FILES = {
    "files/users_lock.yml",
}


def validate_yaml_file(path: str) -> str | None:
    if not os.path.exists(path):
        return f"файл не найден: {path}"

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Пустой файл допустим только для файлов,
        # явно перечисленных в ALLOW_EMPTY_FILES.
        if not content.strip():
            if path in ALLOW_EMPTY_FILES:
                return None

            return "файл пустой"

        yaml.safe_load(content)
        return None

    except yaml.YAMLError as e:
        # Пытаемся показать строку где ошибка
        if hasattr(e, "problem_mark"):
            mark = e.problem_mark
            return (
                f"синтаксическая ошибка в строке {mark.line + 1}, "
                f"колонка {mark.column + 1}: {e.problem}"
            )

        return f"синтаксическая ошибка: {e}"

    except UnicodeDecodeError:
        return "ошибка кодировки — файл должен быть в UTF-8"

    except OSError as e:
        return f"ошибка чтения файла: {e}"


def main():
    # Если переданы аргументы — проверяем только их
    files_to_check = (
        sys.argv[1:]
        if len(sys.argv) > 1
        else DEFAULT_FILES
    )

    print(
        f"Проверка yaml синтаксиса "
        f"({len(files_to_check)} файлов)..."
    )
    print()

    errors = {}

    for path in files_to_check:
        error = validate_yaml_file(path)

        if error:
            errors[path] = error
            print(f"  ✗ {path}: {error}")
        else:
            print(f"  ✓ {path}")

    print()

    if errors:
        print(
            f"❌ Ошибок: "
            f"{len(errors)} из {len(files_to_check)} файлов"
        )
        sys.exit(1)

    else:
        print(
            f"✓ OK — все "
            f"{len(files_to_check)} файлов корректны"
        )
        sys.exit(0)


if __name__ == "__main__":
    main()

