#!/usr/bin/env bash
# =============================================================================
# setup-hooks.sh
#
# Устанавливает git hooks из папки .githooks/ в .git/hooks/
# Запускается ОДИН РАЗ после git clone
#
# Использование:
#   bash setup-hooks.sh
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Установка git hooks..."

# Проверяем что мы в корне репозитория
if [ ! -d ".git" ]; then
    echo "Ошибка: запустите скрипт из корня репозитория"
    exit 1
fi

# Проверяем что папка .githooks существует
if [ ! -d ".githooks" ]; then
    echo "Ошибка: папка .githooks не найдена"
    exit 1
fi

# Самый простой способ — сказать git где искать hooks
# Это работает начиная с git 2.9 и не требует копировать файлы
git config core.hooksPath .githooks

# Делаем все hooks исполняемыми
chmod +x .githooks/*

echo -e "${GREEN}✓ Hooks установлены${NC}"
echo ""
echo "Теперь при каждом 'git commit' будет запускаться проверка."
echo ""
echo -e "${YELLOW}Требования:${NC}"
echo "  - python3 должен быть установлен"
echo "  - запускать git commit из корня репозитория"
