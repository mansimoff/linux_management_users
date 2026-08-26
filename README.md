<div align="center">

# 🔐 GitOps User Management

### Управление учётными записями на Linux-серверах через GitLab как единый источник истины

Декларативное, идемпотентное, аудируемое управление пользователями:
изменение одного YAML-файла → двойная валидация → dry-run → выкат
на все серверы через Ansible.

[![Ansible](https://img.shields.io/badge/Ansible-Core-EE0000?style=flat-square&logo=ansible&logoColor=white)](#)
[![GitLab CI/CD](https://img.shields.io/badge/GitLab-CI%2FCD-FC6D26?style=flat-square&logo=gitlab&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-3-3776AB?style=flat-square&logo=python&logoColor=white)](#)
[![YAML](https://img.shields.io/badge/YAML-source%20of%20truth-CB171E?style=flat-square&logo=yaml&logoColor=white)](#)
[![Bash](https://img.shields.io/badge/Bash-hooks-4EAA25?style=flat-square&logo=gnubash&logoColor=white)](#)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](#)

</div>

---

## 💡 Идея

Классическая проблема любой инфраструктуры: заведение и блокировка
пользователей на десятках серверов вручную — это либо забытый сервер,
либо разный набор групп/прав на разных хостах, либо "кто-то зашёл и
поправил руками", после чего никто не может сказать, что происходит
в системе на самом деле.

Здесь применён подход **GitOps**: единственный способ что-то изменить —
это Pull Request/Merge Request в Git. Сам Git становится журналом аудита
(кто, когда и зачем завёл или заблокировал пользователя — видно в истории
коммитов), а состояние серверов всегда стремится к состоянию,
описанному в репозитории.

```
                     ┌──────────────────────┐
                     │   files/users.yml    │  ← единый источник истины
                     └──────────┬───────────┘
                                │  git push
                                ▼
                     ┌──────────────────────┐
                     │   GitLab CI Pipeline │
                     │ validate → dry-run    │
                     │        → deploy       │
                     └──────────┬───────────┘
                                │ ansible-playbook
                 ┌──────────────┼──────────────┐
                 ▼              ▼              ▼
             server-01      server-02      server-N
           (состояние приводится к описанному в Git)
```

---

## 🧩 Что умеет проект

Один репозиторий — три сценария управления доступом, каждый запускается
простым изменением YAML-файла.

| Сценарий | Триггер | Что происходит |
|---|---|---|
| 👤 **Новый пользователь** | добавлена запись в `files/users.yml` | пользователь создаётся **на всех** серверах из inventory |
| 🖥 **Новый сервер** | добавлен хост в `inventory/hosts.yml` | на новый сервер накатываются **все** существующие пользователи |
| 🔒 **Блокировка доступа** | добавлена запись в `files/users_lock.yml` | учётная запись блокируется (`passwd -l`, shell → `/sbin/nologin`) |

Дополнительно "из коробки":
- ⚙️ Полная **идемпотентность** — playbook можно гонять сколько угодно раз, существующие пользователи не трогаются повторно
- 🔑 Автогенерация пароля (16 символов, `ascii_letters+digits+punctuation`) и **принудительная смена пароля** при первом входе (`chage -d 0`)
- 📧 Автоматическая отправка данных для входа на почту через Postfix/`mail`
- 🛡️ **Два независимых уровня валидации**: git-hook (pre-commit, локально) + CI-стадия (финальный барьер, работает и при правках через веб-интерфейс GitLab, где git-hook не сработает)
- 🙈 `no_log: true` на всех задачах с паролями — секреты никогда не попадают в вывод/логи Ansible и GitLab CI
- 🔍 Dry-run стадия (`--check` + `ansible ping`) перед реальным выкатом — можно посмотреть diff до нажатия Deploy

---

## 🏗 Принцип работы

**Источник истины — Git.** Playbook не "выполняет команду", а приводит
состояние сервера к описанному в YAML:

```
При создании (create.yml):
  пользователь есть в users.yml?
    → нет на сервере   → создать, сгенерировать пароль, отправить письмо
    → уже есть         → пропустить, пароль не трогать

При блокировке (lock_user.yml):
  пользователь есть в users_lock.yml?
    → есть на сервере  → заблокировать (passwd -l, nologin)
    → нет на сервере   → пропустить, ничего не делать
```

Проверка существования пользователя идёт через `id` / `getent passwd`
на самом хосте — не по локальному состоянию, а по факту на сервере,
поэтому playbook безопасно перезапускать и он не расходится
с реальностью.

---

## 🛠 Стек

```
Ansible (ansible.builtin: user, service, package, command)
GitLab CI/CD          — 3-стадийный пайплайн (validate → dry-run → deploy)
Python 3 + PyYAML      — валидация YAML/структуры/полей до запуска Ansible
Bash + git hooks        — pre-commit защита на локальной машине
Postfix + s-nail        — доставка учётных данных на почту
SSH (нестандартный порт) — транспорт для Ansible, ansible.cfg с pipelining
```

---

## 📁 Структура проекта
- [ ] **Molecule**-тесты для playbook'ов
```
management_user/
├── README.md
├── ansible.cfg              # host_key_checking off, pipelining, timeout 30s
├── create.yml                # playbook: создание пользователей
├── lock_user.yml              # playbook: блокировка пользователей
├── setup-hooks.sh              # разовая установка git hooks (core.hooksPath)
├── .githooks/
│   └── pre-commit                # локальная валидация перед коммитом
├── files/
│   ├── users.yml                  # 📌 источник истины: кто должен быть на серверах
│   └── users_lock.yml              # 📌 источник истины: кого заблокировать
├── inventory/
│   └── hosts.yml                    # список серверов (dev/test/prod группы)
└── scripts/
    ├── validate_yml.py                # синтаксис YAML во всех файлах проекта
    ├── validate_users.py               # обязательные поля, формат login/email
    ├── validate_users_lock.py           # структура users_lock.yml
    └── validate_inventory.py             # структура inventory, IP, диапазон портов
```

---

## 🚀 Использование

### Локально (для админа с доступом к репозиторию)

```bash
git clone <repo>
cd management_user

# один раз после клонирования — подключает git hook,
# который не даст закоммитить невалидный YAML
bash setup-hooks.sh

# дальше обычный цикл:
git pull
vim files/users.yml            # или users_lock.yml / inventory/hosts.yml
git commit -m "TASK-123: add user ivan.petrov"
git push                        # pipeline запускается автоматически, но с ручным подтверждением деплоя
```

### Через веб-интерфейс GitLab (без локального клонирования)

Правки файлов прямо в браузере (Web IDE) → commit в ветку → тот же
pipeline отрабатывает валидацию как финальный барьер, даже если
локальный git-hook не был задействован.

### Формат данных

**`files/users.yml`**
```yaml
users:
  - { login: "ivan.petrov", firstname: "Ivan", lastname: "Petrov",
      email: "ivan.petrov@company.net", groups: ["users", "wheel"] }
```

**Требования к `login`** — строчные латинские буквы, цифры, точка:
```
✓  ivan.petrov
✗  Ivan.Petrov     (заглавные буквы запрещены)
✗  ivan_petrov     (подчёркивание запрещено)
```

**Требования к `email`** — только корпоративный домен:
```
✓  ivan.petrov@company.net
✗  ivan.petrov@gmail.com
```

---

## ⚙️ CI/CD пайплайн

Пайплайн автоматически стартует при любом изменении `.yml`/`.py` файлов
проекта и состоит из трёх последовательных стадий:

| # | Стадия | Что делает | Когда останавливает |
|---|---|---|---|
| 1 | **validate** | синтаксис YAML, обязательность и формат полей (`login`, `email`, `groups`, IP, порт) через `scripts/validate_*.py` | любая ошибка формата — pipeline падает, деплой невозможен |
| 2 | **dry-run** | `ansible -m ping` — проверка доступности серверов; `ansible-playbook --check` — что изменится, без реального применения | недоступен сервер / синтаксическая ошибка playbook |
| 3 | **deploy** | `ansible-playbook` с последним коммитом, запускается **вручную** нажатием Run в GitLab | — |

```
Локальный админ                    Web IDE / GitLab UI
──────────────                     ────────────────────
git add users.yml                  правка файла в браузере
git commit                         Commit
    │                                    │
    ▼                                    │
pre-commit hook                          │  (hook не работает
  python3 validate_*.py                  │   в браузере)
    │                                    │
    ├── ошибка → коммит отклонён         │
    └── OK → коммит создан               │
         │                               │
         git push ───────────────────────┘
                          │
                          ▼
                 GitLab CI Pipeline
                          │
           ┌──────────────┼───────────────┐
           ▼              ▼               ▼
        validate       dry-run          deploy
       (статика,     (ansible ping,   (ansible-playbook,
        YAML/поля)    --check diff)    вручную по кнопке)
```

### Что нужно для автоматизации (настройка нового окружения)

1. **GitLab Runner** — установлен и зарегистрирован на управляющем сервере, откуда есть SSH-доступ
   ко всем управляемым хостам.
2. **Технический пользователь Ansible на каждом целевом сервере**:
   ```bash
   useradd -m gitlab-runner-ansible
   mkdir -p /home/gitlab-runner-ansible/.ssh
   echo "ssh-ed25519 AAAA... gitlab-runner@ci" >> /home/gitlab-runner-ansible/.ssh/authorized_keys
   ```
   и проверка подключения раннера к новому хосту до добавления его в `inventory/hosts.yml`.
3. **Read-only токен репозитория** для Runner'а — только `git clone`/`pull`,
   без прав на запись (принцип наименьших привилегий).
4. **Postfix**, настроенный на relay для отправки писем с учётными данными
   (проверяется и поднимается самим playbook при первом запуске, если пакет
   отсутствует).
5. Файл `.gitlab-ci.yml` с тремя стадиями (`validate`/`dry_run`/`deploy`)
   и `.githooks/pre-commit`, вызывающий `python3 scripts/validate_yml.py`.

---

## 🔒 Security-заметки

Проект изначально проектировался под требования fintech-инфраструктуры
(PCI DSS), поэтому:

- Пароли никогда не попадают в git — генерируются на лету через
  `lookup('password', ...)`, хранятся только в памяти Ansible-факта
  и хешируются `sha512` перед записью в `/etc/shadow`.
- `no_log: true` на всех задачах, где фигурирует пароль — не светится
  ни в выводе Ansible, ни в логах GitLab CI job.
- Обязательная смена пароля при первом входе (`chage -d 0`) —
  сгенерированный пароль не может использоваться постоянно.
- Read-only токен у CI-раннера на сам репозиторий — компрометация
  раннера не даёт возможности переписать историю/пайплайн.
- Два независимых барьера валидации (git-hook + CI-стадия) — 
  ошибка формата не может попасть даже в dry-run, не то что в деплой.

---

## 🧭 Roadmap / что добавить дальше

- [ ] **Update-режим** — применять изменения полей (`groups`, `lastname`)
      к уже существующим пользователям, а не только к новым
- [ ] **`unlock_user.yml`** — симметричный playbook разблокировки
- [ ] **Сброс пароля** - если пользователь забыл пароль
- [ ] Поддержка **SSH-ключей** как альтернативы/дополнения к паролю


---

## ⚠️ Дисклеймер

Проект, воспроизводящий паттерн production-эксплуатации
(GitOps + Ansible + двойная валидация). Значения в `files/`, `inventory/`
— демонстрационные данные для портфолио.

---

<div align="center">

Сделано как демонстрация подхода Infrastructure as Code
и GitOps для управления доступом в Linux-инфраструктуре ✨

**Автор:** Ruslan Mansimov

</div>
