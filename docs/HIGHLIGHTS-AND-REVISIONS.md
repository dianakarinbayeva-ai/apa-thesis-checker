# PDF evidence and corrected versions / Сары белгілер / Выделение ошибок

## Қазақша

Есептегі **«Бет 33»** сілтемесін басыңыз: оң жақтағы PDF көрінісінде дәл сол бет ашылады, қате жолдар сары түспен белгіленеді. Таңдалған ескертуге қатысты жолға көрініс автоматты жылжиды. Бет ауыстыру, нөмірін енгізу және масштаб батырмалары бар. Белгі түпнұсқаға жазылмайды.

Әр ескертуде табылған дерек, талап етілетін мән, түзету қадамдары және дұрыс рәсімдеу үлгісі бар. Үлгілер зерттеу мазмұнын ойдан жазбайды. A4, бет саны, жоқ бөлім сияқты нақты жолы жоқ талаптар есепте түсіндіріледі.

Word-та түзетіп, жаңа PDF сақтаңыз. Есепте **«Түзетілген нұсқаны жүктеу»** батырмасын басып, сол PDF-ті жіберіңіз. Тексеру аяқталғанда алдыңғы нұсқамен салыстыруда **түзетілді / қалды / жаңа қателер / өзгеріс расталмады** көрсетіледі. Бет нөмірінің ауысуы өздігінен түзетілді деп есептелмейді. Мәтін жойылса, өзгерсе немесе өлшем анық болмаса, жүйе расталмағанын көрсетеді. Бұрынғы нұсқалар тарихта қалады.

## Русский

Нажмите **«Страница 33»** в отчёте: встроенный просмотр откроет именно эту страницу, строки с подтверждёнными ошибками выделятся жёлтым. Просмотр переместится к выбранному замечанию. Доступны переход по номеру, соседние страницы и масштаб. Оригинальный PDF не изменяется.

Замечание содержит найденный фрагмент, требуемое значение, шаги исправления и пример правильного оформления. Примеры не придумывают содержание исследования. Требования без конкретной строки (размер страницы, объём, отсутствующий раздел) объясняются отдельно в отчёте.

Исправьте проект в Word и сохраните новый PDF. Нажмите **«Загрузить исправленную версию»** в отчёте и отправьте его. После проверки появится сравнение: **исправлено / осталось / новые ошибки / изменение не подтверждено**. Перенос текста на другую страницу не считается исправлением. Исчезновение текста, неоднозначные измерения и изменённые условия проверки не создают ложный успешный результат. Предыдущие версии остаются в истории.

## English

Select **“Page 33”** in a finding. The built-in viewer opens that physical PDF page and highlights confirmed error lines in yellow, scrolling to the selected evidence. Page navigation and zoom are available. The original PDF is never modified.

Each finding includes evidence, the expected requirement, correction steps and a formatting example. Examples do not invent research content. Document-wide findings without a real text location, such as page count or missing sections, are explained in the report.

Edit the project in Word and save a new PDF. Select **“Upload corrected version”** from its report. After review, the comparison shows **corrected / remaining / new errors / change not confirmed**. Page shifts alone do not prove a correction. Changed/deleted text, uncertain measurements and incompatible review settings never become false passes. Earlier versions remain in history.

## Technical and privacy notes

Schema2 findings preserve unrotated PDF text coordinates and inspected anchors. Coordinates and evidence are bounded; truncated evidence cannot establish corrections. Older reports remain readable and receive conservative, page-local localization where actual evidence is available. A built-in, authenticated HTML/PNG viewer avoids dependence on browser PDF-fragment behavior. It limits rendering to one request at a time, <=1400×2000 pixels, checks the original SHA256, and adds annotations only in memory. All viewer and image routes enforce the same owner/curator scopes as reports and send private/no-store responses.

Revisions have a nullable self-reference. The upload action accepts only a completed, valid baseline owned by the uploading student. Checks, guidance and comparison use stored rule-profile values. Original documents are independently stored, and deleting a predecessor does not delete a revision. This feature does not observe changes in an external Word application or automatically rewrite the research.
