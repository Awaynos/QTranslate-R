# Как помочь проекту

**Русский** · [English](CONTRIBUTING.en.md)

Спасибо, что заглянул. QTranslate Remake — небольшой личный проект, и любая помощь приветствуется: сообщение о баге, правка в одну строку, перевод интерфейса, идея.

## Что можно сделать

- **Сообщить о баге** — [открой issue](https://github.com/Awaynos/QTranslate-R/issues/new) и напиши, как воспроизвести: что делал, что ожидал, что получил.
- **Починить баг** — даже если это одна строка.
- **Добавить язык интерфейса** — скопируй `languages/en.json`, переименуй под свой язык (например `de.json`), переведи значения. Кода трогать не нужно.
- **Улучшить документацию** — README, комментарии, эта инструкция.
- **Предложить идею** — коротко и по делу, в issue.

## Перед началом

- Мелкую правку (опечатка, баг в одной функции) можно присылать сразу.
- Крупное изменение — сначала открой issue и опиши замысел. Так никто не потратит время зря.
- Проверь, нет ли уже открытого issue про это же.

## Как запустить у себя

```powershell
git clone https://github.com/Awaynos/QTranslate-R.git
cd QTranslate-R

python -m venv _local\.venv
& "_local\.venv\Scripts\python.exe" -m pip install -r requirements.txt
& "_local\.venv\Scripts\python.exe" run.py
```

Нужен **Python 3.11+**. Пока поддерживается только Windows.

## Проверки

Тестового фреймворка нет — в `tools/` лежат небольшие скрипты, запускаются вручную:

```powershell
.\.venv\Scripts\python.exe tools\core_test.py        # логика ядра, без сети
.\.venv\Scripts\python.exe tools\autopair_test.py    # авто-пара «Родной–Второй»
.\.venv\Scripts\python.exe tools\providers_test.py   # переводчики (нужна сеть)
.\.venv\Scripts\python.exe tools\dictionary_test.py  # словарь
.\.venv\Scripts\python.exe tools\document_test.py    # документы
.\.venv\Scripts\python.exe tools\persist_test.py     # сохранение настроек
```

Добавил функцию — добавь и проверку рядом, в том же стиле.

## Стиль кода

- Python 3.11, аннотации типов, отступ 4 пробела.
- Комментарии — только там, где объясняют **почему**, а не **что**. Очевидное не комментируем.
- Строки интерфейса не хардкодим: они берутся из `languages/*.json` через `tr(...)`.
- Слои не смешиваем: `domain` не знает про интерфейс, `services` описывают контракты, `ui` не содержит бизнес-логики.
- Новый сервис (переводчик, словарь, озвучка) — отдельный модуль в `qtranslate_r/services/providers/`, регистрируется в `core/setup.py`.

## Коммиты

Conventional Commits, по-английски, в повелительном наклонении:

```
feat(services): add Mozhi translator
fix(ui): stop clipping the copy button
docs: fix typo in README
```

В скобках — область: `services`, `ui`, `core`, `config`, `docs`.

## Ветки и pull request

- Ветка от `main`: `feature/короткое-название` или `fix/короткое-название`.
- В описании PR: что сделано, зачем и как проверить.
- Менял интерфейс — приложи скриншот.
- Один PR — одна задача.

## Лицензия вклада

Проект распространяется под [PolyForm Noncommercial 1.0.0](LICENSE).

Отправляя pull request, ты соглашаешься, что твой вклад лицензируется на тех же условиях — его можно свободно использовать, менять и распространять в некоммерческих целях.
