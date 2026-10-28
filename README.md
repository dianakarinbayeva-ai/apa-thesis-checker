# APA Thesis Checker

[Қазақша](README.kk.md) · [Русский](README.ru.md) · [English](README.en.md)

Трёхъязычная платформа автоматической проверки PDF магистерских работ по
требованиям Академии государственного управления при Президенте Республики
Казахстан. Личные кабинеты, история, отчёты PDF/JSON и готовая Windows-сборка.

**Windows:** скачайте архив выпуска, распакуйте и запустите `APA Thesis Checker.exe`.
Откроется http://127.0.0.1:8765. При первом локальном запуске создайте аккаунт:
первый пользователь станет администратором. Python и Docker не требуются.
Остановка — Ctrl+C или закрытие окна приложения.

Исходный проект: [Tsinghua Checker](https://github.com/jacky-rui/tsinghua-thesis-format-checker-skill),
зафиксированный коммит `f19b8392a111eacff7b6e80211560298abca852e`.
PDF-only адаптация и правила Академии реализованы в `platform_app/checker.py`.

Все проверки выполняются автоматически. Результаты: соответствует, нарушение,
недостаточно данных, не применимо. Никаких ручных этапов и платных API.
Недостаток данных не считается соответствием. Это предварительный нормконтроль,
а не официальное решение о допуске. [Покрытие проверок](docs/CHECKS.md).

## Из исходников

Python 3.12, Windows или Linux:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python launcher.py
```

Linux: используйте `.venv/bin/python`. База и документы сохраняются в `data/`.
Резервное копирование: остановите приложение и скопируйте эту папку целиком.
Без исходной папки `data` аккаунты и история не восстанавливаются.
Не переносите её в GitHub. Удаление работы в кабинете удаляет файл и отчёт.
Сброс пароля: `python manage.py changepassword USERNAME` с тем же `APA_DATA_DIR`.

## Проверки, сборка и развёртывание

```powershell
python manage.py test tests
python -m pip install -r requirements-build.txt
python build_windows.py
```

Windows-сборка создаётся на Windows x64. Комплект Linux/PostgreSQL/HTTPS:
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). GitHub Pages не запускает сервер
Python и личные кабинеты. Платный сервер не заказывается автоматически.

Основной источник: [приложение 1 от 13.09.2024 № 586](https://www.apa.kz/wp-content/uploads/2024/09/Приложение-1-Требования-к-оформлению.docx).
Принимаются текстовые PDF до 30 МБ и 300 страниц. OCR, проверка плагиата,
научной достоверности и автоматическое редактирование диссертации не входят.

AGPL-3.0-or-later; исходный MIT-код и уведомления сохранены. [NOTICE.md](NOTICE.md).
