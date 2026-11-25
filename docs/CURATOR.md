# Куратор кабинеті

Қазақша: `/curator/` бөлімінде топ батырмалары, тіркелу/жүктеу есебі және магистранттардың соңғы нәтижелері көрсетіледі. Әкімші барлық топты көреді. Тек белгілі топты басқаратын кураторды әкімші Study groups → Curators өрісінде тағайындайды; оған staff құқығын беру қажет емес. Магистрант басқа студенттің тізімін немесе құжатын көрмейді.

Топ тізіміндегі «Тіркелу коды» бағанын ашып, кодты тек тиісті магистрантқа жеке беріңіз. Ол тіркелу кезінде тобын таңдап, кодты енгізеді. Бұрын тіркелген пайдаланушы жеке кабинетіндегі «Топқа қосылу» сілтемесін пайдаланады. Код тіркелгіге бір рет байланысады. Бұл код есептік жазбаның құпиясөзі емес. Платформа ешкімге хабарлама жібермейді.

Бір студент бірнеше PDF жүктесе, соңғысы ғана есепке алынады. «Жүктеуі қалған» санына әлі тіркелмегендер де кіреді. Тексерудің аяқталуы жұмыстың талаптарға сай өткенін білдірмейді. Бұзушылықтар, дерек жеткіліксіздігі және техникалық қателер бөлек есептеледі.

# Кабинет куратора

Русский: `/curator/` показывает группы, регистрацию, загрузки и последние результаты. Администраторы видят все группы; обычный куратор — только назначенные ему через административный интерфейс. Не выдавайте ограниченному куратору staff-доступ: staff имеет доступ ко всем группам.

Персональный код из строки студента передаётся только этому студенту. При регистрации он выбирает группу и вводит код; существующий аккаунт использует «Присоединиться к группе». Код не заменяет пароль и не позволяет войти в уже созданный аккаунт. Списки и коды не публикуются.

Последняя загрузка заменяет предыдущий результат в статистике. «Осталось загрузить» включает незарегистрированных. Завершённые проверки, соответствие требованиям, исправления, недостаток данных и ошибки различаются. Куратор может просматривать отчёт своей группы, но не удалять документы студентов.

# Curator dashboard

English: `/curator/` provides group buttons, registration/upload progress and latest student outcomes. Administrators see all groups; an ordinary curator sees only groups assigned by an administrator. Do not grant staff access to a curator who should be limited to assigned groups.

Share each private registration code only with its student. New students select a group and enter their code; existing accounts use Join a group. Codes bind a roster entry once and are not account passwords. No messages are sent automatically.

Statistics count each student once, using the latest upload. Awaiting upload includes unregistered students. Completed reviews, passes, required revisions, inconclusive results and technical failures are separate. A curator can read a scoped report but cannot delete another user's document.

## Private import for administrators

Actual student names belong in private `data/`, never in source files, migrations, Git, screenshots for publication or release assets. The public Windows ZIP contains an empty installation; copy the whole private data directory to transfer accounts and rosters between your own computers while the application is stopped.

The import command consumes JSON shaped as `groups[{code, students:[full_name, ...]}]`. Entries are numbered in the supplied order. Use the same `APA_DATA_DIR` as the running installation:

```powershell
python manage.py import_students data/roster.json --dry-run
python manage.py import_students data/roster.json
```

An identical repeated import preserves row IDs, codes and account bindings. Conflicting replacements are rejected atomically. An unloaded roster is shown as unknown rather than zero. Back up the whole private data directory, including its generated secret, to preserve unused registration codes.
