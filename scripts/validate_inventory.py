#!/usr/bin/env python3
"""
Валидация inventory/hosts.yml
Проверяет:
  - корректность yaml синтаксиса
  - структуру inventory (all -> children -> devs -> hosts)
  - наличие и непустоту обязательных полей для каждого хоста
  - корректность IP адреса
  - допустимый диапазон порта
"""

import yaml
import sys
import re

HOSTS_FILE = "inventory/hosts.yml"
REQUIRED_HOST_FIELDS = ["ansible_host", "ansible_user", "ansible_connection", "ansible_port"]
IP_PATTERN = re.compile(
    r'^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$'
)


def validate_hosts(path: str) -> list[str]:
    errors = []

    # ── 1. Читаем и парсим yaml ───────────────────────────────────────────
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        return [f"Файл не найден: {path}"]
    except yaml.YAMLError as e:
        return [f"Невалидный yaml синтаксис: {e}"]

    # ── 2. Проверяем структуру верхнего уровня ────────────────────────────
    if not isinstance(data, dict):
        return ["Файл должен содержать словарь верхнего уровня"]

    if "all" not in data:
        return ["Отсутствует обязательная секция 'all:'"]

    all_section = data["all"]

    if not isinstance(all_section, dict):
        errors.append("Секция 'all:' должна быть словарём")
        return errors

    if "children" not in all_section:
        errors.append("Отсутствует секция 'all.children:'")
        return errors

    children = all_section["children"]

    if not isinstance(children, dict):
        errors.append("Секция 'children:' должна быть словарём")
        return errors

    if not children:
        errors.append("Секция 'children:' пустая — нет ни одной группы хостов")
        return errors

    # ── 3. Проверяем каждую группу и хосты в ней ─────────────────────────
    total_hosts = 0

    for group_name, group_data in children.items():
        if not isinstance(group_data, dict):
            errors.append(f"Группа '{group_name}': должна быть словарём")
            continue

        if "hosts" not in group_data:
            errors.append(f"Группа '{group_name}': отсутствует секция 'hosts:'")
            continue

        hosts = group_data["hosts"]

        if not hosts:
            errors.append(f"Группа '{group_name}': секция 'hosts:' пустая")
            continue

        if not isinstance(hosts, dict):
            errors.append(f"Группа '{group_name}': 'hosts:' должен быть словарём")
            continue

        # Проверяем каждый хост
        for host_name, host_vars in hosts.items():
            total_hosts += 1
            label = f"хост '{host_name}' (группа: {group_name})"

            if not isinstance(host_vars, dict):
                errors.append(f"{label}: параметры хоста должны быть словарём")
                continue

            # Проверка обязательных полей
            for field in REQUIRED_HOST_FIELDS:
                if field not in host_vars:
                    errors.append(f"{label}: отсутствует поле '{field}'")
                elif host_vars[field] is None:
                    errors.append(f"{label}: поле '{field}' равно null")
                elif isinstance(host_vars[field], str) and not host_vars[field].strip():
                    errors.append(f"{label}: поле '{field}' пустое")

            # Проверка корректности IP адреса
            ip = str(host_vars.get("ansible_host", ""))
            if ip and not IP_PATTERN.match(ip):
                errors.append(
                    f"{label}: некорректный IP адрес '{ip}'"
                )

            # Проверка порта — должен быть числом от 1 до 65535
            port = host_vars.get("ansible_port")
            if port is not None:
                try:
                    port_int = int(port)
                    if not (1 <= port_int <= 65535):
                        errors.append(
                            f"{label}: порт {port} вне допустимого диапазона (1-65535)"
                        )
                except (ValueError, TypeError):
                    errors.append(
                        f"{label}: поле 'ansible_port' должно быть числом, получено: '{port}'"
                    )

            # Проверка ansible_connection
            connection = host_vars.get("ansible_connection", "")
            if connection and connection not in ["ssh", "local", "paramiko"]:
                errors.append(
                    f"{label}: неизвестный тип подключения '{connection}' "
                    f"— ожидается 'ssh'"
                )

    if total_hosts == 0:
        errors.append("Не найдено ни одного хоста во всём inventory")

    return errors


def main():
    print(f"Проверка {HOSTS_FILE}...")
    errors = validate_hosts(HOSTS_FILE)

    if errors:
        print(f"\n❌ Найдено ошибок: {len(errors)}")
        for err in errors:
            print(f"   ✗ {err}")
        sys.exit(1)
    else:
        # Для отчёта считаем хосты
        with open(HOSTS_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        hosts = data["all"]["children"]
        total = sum(
            len(g.get("hosts", {}))
            for g in hosts.values()
            if isinstance(g, dict)
        )
        print(f"✓ OK — {total} хостов, структура корректна")
        sys.exit(0)


if __name__ == "__main__":
    main()
