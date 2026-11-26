"""Human correction steps for the retained Academy rule registry.

Examples illustrate formatting using placeholders; they never rewrite research,
invent titles or references, or claim that uncertain PDF evidence is a violation.
Normative scope follows checker.REGISTRY and docs/CHECKS.md, Order No. 586 (2024).
"""
from .checker import DEFAULT_PROFILE


# Each language has (expected requirement, action, illustrative formatting).
_GUIDANCE = {
    "R_SIZE": {
        "kk": ("A4: 210 × 297 мм.", "Бет параметрлерінен A4 өлшемін таңдаңыз. Қайта PDF сақтап, бет өлшемін тексеріңіз.", "Бет өлшемі: A4 (210 × 297 мм)."),
        "ru": ("A4: 210 × 297 мм.", "Выберите A4 в параметрах страницы. Сохраните новый PDF и проверьте размер страниц.", "Размер страницы: A4 (210 × 297 мм)."),
        "en": ("A4: 210 × 297 mm.", "Choose A4 in page settings. Export a new PDF and check its page dimensions.", "Page size: A4 (210 × 297 mm)."),
    },
    "R_LENGTH": {
        "kk": ("Қосымшаларсыз кемінде {minimum} бет.", "Қосымша басталғанға дейінгі көлемді тексеріңіз. Қажет болса, зерттеуді мазмұнды түрде толықтырыңыз; бос беттер қоспаңыз.", "Көлем есебінің үлгісі: негізгі жұмыс ≥ {minimum} бет; қосымшалар бөлек."),
        "ru": ("Не менее {minimum} страниц без приложений.", "Проверьте объём до начала приложений. При необходимости содержательно дополните исследование; не добавляйте пустые страницы.", "Пример подсчёта объёма: основная работа ≥ {minimum} страниц; приложения отдельно."),
        "en": ("At least {minimum} pages excluding appendices.", "Check the page count before the appendices. Develop the research where needed; do not add blank pages.", "Page-count example: main work ≥ {minimum} pages; appendices counted separately."),
    },
    "R_FONT": {
        "kk": ("Негізгі мәтін: Times New Roman, {font_size} pt.", "Бастапқы құжаттағы негізгі мәтін стиліне Times New Roman және {font_size} pt орнатыңыз. PDF ішіндегі қаріптерді тексеріңіз.", "Стиль параметрі: Times New Roman · {font_size} pt."),
        "ru": ("Основной текст: Times New Roman, {font_size} pt.", "Установите в стиле основного текста исходного документа Times New Roman и {font_size} pt. Проверьте шрифты после экспорта в PDF.", "Параметр стиля: Times New Roman · {font_size} pt."),
        "en": ("Body text: Times New Roman, {font_size} pt.", "Set the source document's body style to Times New Roman at {font_size} pt. Check the fonts after PDF export.", "Style setting: Times New Roman · {font_size} pt."),
    },
    "R_COLOR": {
        "kk": ("Негізгі мәтіннің түсі — қара (#000000).", "Көрсетілген негізгі мәтінге қара қаріп түсін орнатып, PDF файлын қайта сақтаңыз.", "Қаріп түсі: қара · #000000."),
        "ru": ("Цвет основного текста — чёрный (#000000).", "Задайте чёрный цвет шрифта для указанного основного текста и повторно сохраните PDF.", "Цвет шрифта: чёрный · #000000."),
        "en": ("Body text is black (#000000).", "Set the indicated body text's font colour to black and export the PDF again.", "Font colour: black · #000000."),
    },
    "R_MARGIN": {
        "kk": ("Жиектер: сол {margin_left}, оң {margin_right}, жоғарғы {margin_top}, төменгі {margin_bottom} мм.", "Бөлім параметрлеріне осы жиектерді орнатыңыз. Көрсетілген жолдың шегінісін және кесте не суреттің жиектен шығуын түзетіңіз. PDF мәтінінің шекарасы бастапқы баптауды толық дәлелдемейді.", "Бет параметрлері (мм): сол {margin_left}; оң {margin_right}; жоғарғы {margin_top}; төменгі {margin_bottom}."),
        "ru": ("Поля: слева {margin_left}, справа {margin_right}, сверху {margin_top}, снизу {margin_bottom} мм.", "Задайте эти поля в параметрах раздела. Исправьте отступ указанной строки и выход таблиц или рисунков за поля. Границы текста PDF не доказывают настройки исходного документа.", "Параметры страницы (мм): слева {margin_left}; справа {margin_right}; сверху {margin_top}; снизу {margin_bottom}."),
        "en": ("Margins: left {margin_left}, right {margin_right}, top {margin_top}, bottom {margin_bottom} mm.", "Set these margins in the source section settings. Adjust the indicated line's indent and any tables or figures extending into the margins. PDF text bounds cannot prove source settings.", "Page settings (mm): left {margin_left}; right {margin_right}; top {margin_top}; bottom {margin_bottom}."),
    },
    "R_NUMBER": {
        "kk": ("Бет нөмірі төменгі ортада араб цифрларымен беріледі; титулдық бет саналады, бірақ нөмірі көрсетілмейді.", "Төменгі колонтитулға автоматты нөмір қойыңыз. Титулдық бетті бірінші деп санап, оның нөмірін жасырыңыз; бөлімдерде санауды қайта бастамаңыз.", "Нөмірлеу үлгісі: PDF 1-беті — нөмірсіз; 2-беті — 2; 3-беті — 3."),
        "ru": ("Арабский номер страницы внизу по центру; титульный лист учитывается, но номер не печатается.", "Вставьте автоматический номер в нижний колонтитул. Считайте титульный лист первым и скройте его номер; не перезапускайте нумерацию в разделах.", "Пример нумерации: страница PDF 1 — без номера; страница 2 — 2; страница 3 — 3."),
        "en": ("Arabic page numbers at bottom centre; the title page is counted but its number is hidden.", "Insert automatic page numbers in the footer. Count the title page as page 1 and hide its number; continue numbering across sections.", "Numbering example: PDF page 1 — no printed number; page 2 — 2; page 3 — 3."),
    },
    "R_STRUCTURE": {
        "kk": ("Мазмұны, кіріспе, қорытынды және пайдаланылған әдебиеттер тізімі танылуы тиіс.", "Қажетті бөлімнің барын және тақырыбы жеке жолда берілгенін тексеріңіз. Бөлім мазмұнын өз зерттеуіңізге сәйкес жазыңыз.", "Құрылым үлгісі: МАЗМҰНЫ → КІРІСПЕ → [негізгі бөлімдер] → ҚОРЫТЫНДЫ → ПАЙДАЛАНЫЛҒАН ӘДЕБИЕТТЕР ТІЗІМІ."),
        "ru": ("Должны распознаваться содержание, введение, заключение и список использованных источников.", "Проверьте наличие требуемого раздела и отдельной строки заголовка. Содержание раздела напишите по собственному исследованию.", "Пример структуры: СОДЕРЖАНИЕ → ВВЕДЕНИЕ → [основные разделы] → ЗАКЛЮЧЕНИЕ → СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ."),
        "en": ("Contents, introduction, conclusion and references must be identifiable.", "Check that the required section exists and its heading is on a separate line. Write the section using your own research.", "Structure example: CONTENTS → INTRODUCTION → [main sections] → CONCLUSION → REFERENCES."),
    },
    "R_HEADING": {
        "kk": ("Құрылымдық бөлімнің тақырыбы жаңа беттің басында, қалың қаріппен беріледі.", "Бөлім алдына бет үзілімін қойып, тақырып стилін қалың қаріпке өзгертіңіз. PDF ішіндегі нақты бетті тексеріңіз.", "Рәсімдеу үлгісі: жаңа бет → КІРІСПЕ (қалың қаріп) → [өзіңіздің мәтініңіз]."),
        "ru": ("Заголовок структурного раздела — в начале новой страницы, полужирным шрифтом.", "Вставьте разрыв страницы перед разделом и задайте полужирный стиль заголовка. Проверьте соответствующую страницу PDF.", "Пример оформления: новая страница → ВВЕДЕНИЕ (полужирный) → [ваш текст]."),
        "en": ("A structural heading starts a new page and uses bold type.", "Insert a page break before the section and apply a bold heading style. Check the corresponding PDF page.", "Formatting example: new page → INTRODUCTION (bold) → [your text]."),
    },
    "R_FIGURE": {
        "kk": ("Сурет жазуында нөмір мен бос емес атау болуы керек (5.4.1–5.4.7).", "Суреттің нақты нөмірі мен мазмұнға сай атауын көрсетіңіз. Орналасуы мен рәсімделуін нұсқаулықтың 5.4 тармағымен салыстырыңыз.", "Тек рәсімдеу үлгісі: Сурет 2 — [суреттің нақты атауы]. Жақшадағы мәтінді өз атауыңызбен ауыстырыңыз."),
        "ru": ("Подпись рисунка содержит номер и непустое название (5.4.1–5.4.7).", "Укажите фактический номер рисунка и название по его содержанию. Проверьте расположение и оформление по пункту 5.4 руководства.", "Только пример оформления: Рисунок 2 — [фактическое название рисунка]. Замените текст в скобках своим названием."),
        "en": ("A figure caption contains a number and a non-empty title (5.4.1–5.4.7).", "Add the figure's actual number and a title describing its content. Check placement and formatting against guide section 5.4.", "Formatting template only: Figure 2 — [actual figure title]. Replace the placeholder with your title."),
    },
    "R_TABLE": {
        "kk": ("Кесте жазуында нөмір мен бос емес атау болуы керек (5.5.1–5.5.8).", "Кестенің нақты нөмірі мен атауын жазыңыз. Дереккөз қолданылса, нақты дерекке сілтеме жасап, оны әдебиеттер тізімімен сәйкестендіріңіз; рәсімделуін 5.5 және 5.7–5.8 тармақтарымен салыстырыңыз.", "Тек рәсімдеу үлгісі: Кесте 2 — [кестенің нақты атауы]. Сілтеме үлгісі: [1] → [әдебиеттер тізіміндегі нақты дереккөз]."),
        "ru": ("Подпись таблицы содержит номер и непустое название (5.5.1–5.5.8).", "Укажите фактический номер и название таблицы. При использовании источника дайте ссылку на реальные данные и сопоставьте её со списком источников; проверьте оформление по пунктам 5.5 и 5.7–5.8.", "Только пример оформления: Таблица 2 — [фактическое название таблицы]. Пример ссылки: [1] → [реальный источник в списке]."),
        "en": ("A table caption contains a number and a non-empty title (5.5.1–5.5.8).", "Add the table's actual number and title. When using a source, cite the real data and match the citation to the bibliography; check guide sections 5.5 and 5.7–5.8 for formatting.", "Formatting template only: Table 2 — [actual table title]. Citation template: [1] → [real bibliography entry]."),
    },
    "R_REFERENCE": {
        "kk": ("Дереккөздер мәтінде алғашқы кездесу ретімен нөмірленіп, шаршы жақшамен беріледі (5.7.3–5.8.1).", "Алғашқы сілтемені [1] деп белгілеп, кейінгі жаңа дереккөздерді ретімен нөмірлеңіз. Қайталанған дереккөзге бұрынғы нөмірін қолданыңыз және әдебиеттер тізімімен салыстырыңыз.", "Тек сілтеме пішімінің үлгісі: [1], [2], қайта [1]. Әр нөмір нақты дереккөзге сәйкес болуы керек."),
        "ru": ("Источники нумеруются по первому упоминанию; ссылки заключаются в квадратные скобки (5.7.3–5.8.1).", "Обозначьте первую ссылку [1], затем нумеруйте новые источники по порядку. При повторном цитировании сохраняйте номер и сверяйте его со списком источников.", "Только пример формы ссылок: [1], [2], повторно [1]. Каждый номер должен соответствовать реальному источнику."),
        "en": ("Sources are numbered by first appearance and cited in square brackets (5.7.3–5.8.1).", "Start with [1] and number new sources in first-appearance order. Reuse the same number for repeated citations and cross-check the bibliography.", "Citation-format example only: [1], [2], then [1] again. Every number must refer to a real source."),
    },
    "R_APPENDIX": {
        "kk": ("Қосымша тақырыптарында араб цифрларымен нөмір қолданылады (5.9.1–5.9.6).", "Қосымшаның тақырыбы мен нөмірін жеке жолға жазыңыз. Оның басталуын және негізгі жұмыс көлемінен бөлек есептелуін тексеріңіз.", "Тақырып пішімінің үлгісі: ҚОСЫМША 1 → [өзіңіздің қосымша материалыңыз]."),
        "ru": ("Приложения обозначаются заголовком с арабским номером (5.9.1–5.9.6).", "Поместите название и номер приложения в отдельную строку. Проверьте его начало и исключение приложений из основного объёма работы.", "Пример формы заголовка: ПРИЛОЖЕНИЕ 1 → [ваш материал приложения]."),
        "en": ("Appendix headings use Arabic numbers (5.9.1–5.9.6).", "Put the appendix heading and number on a separate line. Check its start and ensure appendices are excluded from the main page count.", "Heading-format example: APPENDIX 1 → [your appendix material]."),
    },
    "R_SPACING": {
        "kk": ("Негізгі мәтіннің жоларалық интервалы — дара.", "Бастапқы құжаттың абзац стилінде дара интервал орнатыңыз. PDF бойынша арақашықтық бағасы жуық екенін ескеріп, бастапқы стиль параметрін тексеріңіз.", "Абзац параметрі: жоларалық интервал — дара (1,0)."),
        "ru": ("Межстрочный интервал основного текста — одинарный.", "Установите одинарный интервал в стиле абзаца исходного документа. Оценка расстояний в PDF приблизительна, поэтому проверьте исходный стиль.", "Параметр абзаца: межстрочный интервал — одинарный (1,0)."),
        "en": ("Body text uses single line spacing.", "Set single line spacing in the source paragraph style. PDF line-distance estimates are approximate, so verify the source style setting.", "Paragraph setting: line spacing — single (1.0)."),
    },
    "R_VISUAL": {
        "kk": ("Көрнекі материалдар мен оқылуы нашар беттерді толық бағалауға PDF мәтіні жеткіліксіз.", "Белгіленген бетті және нұсқаулықтағы 4, 5.4.8, 5.5.8 тармақтарын салыстырыңыз. Мүмкін болса, скан орнына мәтіндік PDF экспорттаңыз. Дәлелдің жеткіліксіздігі түзетілгенін растамайды.", "Экспорт параметрінің үлгісі: ізделетін мәтіні бар PDF; кесте мен сурет анық көрінеді."),
        "ru": ("Извлечённого текста недостаточно для полной оценки иллюстраций и плохо читаемых страниц.", "Сопоставьте указанную страницу с пунктами 4, 5.4.8, 5.5.8 руководства. По возможности экспортируйте текстовый PDF вместо скана. Недостаток данных не подтверждает исправление.", "Пример параметра экспорта: PDF с доступным для поиска текстом; таблицы и рисунки читаемы."),
        "en": ("Extracted text cannot fully establish visual-material compliance or readability of scanned pages.", "Compare the indicated page with guide sections 4, 5.4.8 and 5.5.8. Export a text-based PDF instead of a scan where possible. Insufficient evidence does not prove a correction.", "Export-setting example: PDF with searchable text and readable figures and tables."),
    },
}


def guidance_for(finding, profile, duration="1", language="kk"):
    """Return localized ``expected``, ``recommendation``, ``correct_example`` text.

    The submission's profile snapshot overrides defaults, including font size,
    margins and programme minimums. Finding evidence is deliberately not copied
    into an example: PDF evidence may be truncated or contain substantive claims.
    """
    values = dict(DEFAULT_PROFILE, **(profile or {}))
    values["minimum"] = values["min_pages_one"] if duration == "1" else values["min_pages_long"]
    values = {key: format(value, "g") if isinstance(value, (float, int)) else value for key, value in values.items()}
    language = language if language in ("kk", "ru", "en") else "kk"
    # Unknown historical rule identifiers get an evidence-limit recommendation.
    messages = _GUIDANCE.get(finding.get("rule_id"), _GUIDANCE["R_VISUAL"])[language]
    return dict(zip(("expected", "recommendation", "correct_example"), (message.format(**values) for message in messages)))
