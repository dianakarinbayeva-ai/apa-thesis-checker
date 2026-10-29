"""All student-facing strings. Report keys remain stable across languages."""

ROWS = '''
brand|Академиялық нормобақылау|Академический нормконтроль|Academic format review
academy|Қазақстан Республикасы Президентінің жанындағы Мемлекеттік басқару академиясы|Академия государственного управления при Президенте Республики Казахстан|Academy of Public Administration under the President of the Republic of Kazakhstan
tagline|Зерттеуіңізге назар аударыңыз. Рәсімдеуді біз тексереміз.|Сосредоточьтесь на исследовании. Оформление проверим мы.|Focus on your research. We will review the formatting.
dashboard|Жеке кабинет|Личный кабинет|Dashboard
history|Тексерулер тарихы|История проверок|Review history
guide|Рәсімдеу нұсқаулығы|Руководство по оформлению|Formatting guide
login|Кіру|Войти|Sign in
logout|Шығу|Выйти|Sign out
register|Тіркелу|Создать аккаунт|Create account
username|Пайдаланушы аты|Имя пользователя|Username
password|Құпиясөз|Пароль|Password
password2|Құпиясөзді қайталаңыз|Повторите пароль|Confirm password
password_hint|Кемінде 10 таңба. Кең таралған немесе тек сандардан тұратын құпиясөзді қолданбаңыз.|Минимум 10 символов. Не используйте распространённые пароли или только цифры.|At least 10 characters. Avoid common or entirely numeric passwords.
auth_error|Пайдаланушы аты немесе құпиясөз қате.|Неверное имя пользователя или пароль.|Incorrect username or password.
register_error|Пайдаланушы аты бос емес, 3–50 латын әрпі, сан немесе _ таңбасынан тұруы керек.|Имя занято или некорректно: используйте 3–50 латинских букв, цифр или _.|Username is taken or invalid. Use 3–50 Latin letters, digits or underscores.
password_error|Құпиясөздер сәйкес келуі және қауіпсіздік талаптарына сай болуы керек.|Пароли должны совпадать и соответствовать требованиям безопасности.|Passwords must match and meet the security requirements.
welcome|Жұмысыңызды тексеруге дайынсыз ба?|Готовы проверить вашу работу?|Ready to review your thesis?
intro|PDF жүктеңіз. Академия талаптарына сай тексеру мен түсінікті ұсыныстар алыңыз.|Загрузите PDF и получите проверку по требованиям Академии с понятными рекомендациями.|Upload a PDF for an Academy-specific review with clear recommendations.
new_check|Жаңа тексеру|Новая проверка|New review
total|Барлық жұмыстар|Всего работ|Total submissions
completed|Тексерілді|Проверено|Completed
pending|Өңделуде|В обработке|In progress
latest|Соңғы жұмыстар|Последние работы|Recent submissions
all_history|Барлық тарих|Вся история|View all history
empty|Әзірге жұмыстар жоқ. Алғашқы PDF файлын жүктеңіз.|Пока нет работ. Загрузите первый PDF.|No submissions yet. Upload your first PDF.
document|Жұмыс|Работа|Submission
date|Күні|Дата|Date
status|Күйі|Статус|Status
open|Ашу|Открыть|Open
queued|Кезекте|В очереди|Queued
processing|Тексерілуде|Проверяется|Processing
done|Есеп дайын|Отчёт готов|Report ready
failed|Тексеру орындалмады|Проверка не выполнена|Review failed
title|Жұмыс атауы|Название работы|Submission title
pdf_file|PDF құжаты|PDF-документ|PDF document
file_hint|Мәтіндік PDF · 30 МБ дейін · 300 бетке дейін|Текстовый PDF · до 30 МБ · до 300 страниц|Text-based PDF · up to 30 MB · up to 300 pages
document_language|Жұмыс тілі|Язык работы|Document language
duration|Оқу ұзақтығы|Длительность программы|Programme duration
one_year|1 жыл — кемінде 40 бет|1 год — минимум 40 страниц|1 year — at least 40 pages
one_half|1,5 жыл — кемінде 60 бет|1,5 года — минимум 60 страниц|1.5 years — at least 60 pages
two_year|2 жыл — кемінде 60 бет|2 года — минимум 60 страниц|2 years — at least 60 pages
start|Тексеруді бастау|Начать проверку|Start review
privacy|Құжат жеке кабинетте сақталады. Басқа студенттерге қолжетімсіз. Түпнұсқа өзгермейді.|Документ хранится в вашем кабинете и недоступен другим студентам. Оригинал не изменяется.|Your document stays private to your account. The original is never modified.
waiting|Тексеру жалғасуда. Бұл бет автоматты түрде жаңарады.|Проверка выполняется. Страница обновится автоматически.|Review is in progress. This page will refresh automatically.
report|Нормобақылау есебі|Отчёт нормконтроля|Format review report
download_pdf|PDF есебін жүктеу|Скачать отчёт PDF|Download PDF report
download_json|JSON есебін жүктеу|Скачать отчёт JSON|Download JSON report
original|Түпнұсқа PDF|Исходный PDF|Original PDF
delete|Жұмысты жою|Удалить работу|Delete submission
delete_confirm|Құжатты және есепті жою керек пе?|Удалить документ и отчёт?|Delete the document and report?
pass|Сәйкес келеді|Соответствует|Pass
fail|Бұзушылық|Нарушение|Violation
uncertain|Деректер жеткіліксіз|Недостаточно данных|Insufficient evidence
na|Қолданылмайды|Не применимо|Not applicable
page|Бет|Страница|Page
pages|Беттер саны|Количество страниц|Page count
body_pages|Қосымшасыз беттер|Страниц без приложений|Pages excluding appendices
rule|Талап|Требование|Requirement
evidence|Табылған деректер|Найденные данные|Evidence
recommendation|Ұсыныс|Рекомендация|Recommendation
source_clause|Нұсқаулық тармағы|Пункт руководства|Guide clause
method|Тексеру әдісі|Метод проверки|Check method
limitations|Автоматты тексерудің шектері|Ограничения автоматической проверки|Automated review limits
limits_text|PDF бастапқы Word параметрлерін толық сақтамайды. Тексеру автоматты орындалады; деректер жеткіліксіз болса, есепте көрсетіледі. Бұл есеп ресми рұқсат емес.|PDF не сохраняет все параметры исходного Word. Все проверки выполняются автоматически; недостаток данных отмечается в отчёте. Отчёт не является официальным допуском.|PDF does not retain every source Word setting. All checks run automatically; insufficient evidence is identified in the report. This report is not an official approval.
profile|Талаптар нұсқасы|Версия требований|Rules version
official_guide|Академияның ресми материалдары|Официальные материалы Академии|Official Academy resources
guide_intro|Негіз: 13.09.2024 жылғы № 586 бұйрыққа 1-қосымша. Ескі құжаттардағы басқа мәндер қолданылмайды.|Основа: приложение 1 к приказу от 13.09.2024 № 586. Отличающиеся значения из старых документов не применяются.|Based on Appendix 1 to Order No. 586 dated 13 September 2024. Conflicting values from older documents are not applied.
academic_policy|Академиялық саясат беті|Страница академической политики|Academic policy page
requirements|Құрылым мен рәсімдеу талаптары|Требования к структуре и оформлению|Structure and formatting requirements
guide_unavailable|Ресми электрондық нұсқаулық сілтемесі уақытша қолжетімсіз болуы мүмкін. Талаптар қосымшасын пайдаланыңыз.|Ссылка на официальное электронное руководство может быть временно недоступна. Используйте приложение с требованиями.|The official electronic manual may be temporarily unavailable. Use the requirements appendix.
format_summary|A4 · Times New Roman 14 · бір интервал · өрістер 30/10/20/20 мм|A4 · Times New Roman 14 · одинарный интервал · поля 30/10/20/20 мм|A4 · Times New Roman 14 · single spacing · margins 30/10/20/20 mm
source_code|Бастапқы код және лицензиялар|Исходный код и лицензии|Source code and licences
independent|Академия талаптарына негізделген ашық бастапқы кодты құрал.|Инструмент с открытым кодом на основе требований Академии.|An open-source tool based on the Academy's requirements.
bad_pdf|PDF файлы бүлінген немесе оқылмайды.|PDF повреждён или не читается.|The PDF is damaged or unreadable.
encrypted|Құпиясөзбен қорғалған PDF қабылданбайды. Қорғаусыз көшірмені жүктеңіз.|Защищённый паролем PDF не принимается. Загрузите копию без защиты.|Password-protected PDFs are not accepted. Upload an unprotected copy.
scan|Мәтіндік қабат табылмады немесе беттердің көбі сканерленген. OCR қолдау көрсетілмейді.|Текстовый слой отсутствует или большинство страниц — сканы. OCR не поддерживается.|No text layer was found, or most pages are scans. OCR is not supported.
too_large|Файл көлемі 30 МБ-тан аспауы керек.|Размер файла не должен превышать 30 МБ.|The file must not exceed 30 MB.
too_many_pages|PDF 1–300 беттен тұруы керек.|PDF должен содержать от 1 до 300 страниц.|The PDF must contain 1–300 pages.
invalid_form|Барлық өрістерді дұрыс толтырыңыз және PDF таңдаңыз.|Заполните все поля корректно и выберите PDF.|Complete every field correctly and select a PDF.
worker_error|Тексеру аяқталмады. Қайта жүктеп көріңіз немесе әкімшіге хабарласыңыз.|Проверка не завершилась. Повторите загрузку или обратитесь к администратору.|The review did not complete. Try uploading again or contact an administrator.
timeout|Тексеру уақыты аяқталды. Құжатты қайта жүктеңіз.|Время проверки истекло. Загрузите документ повторно.|The review timed out. Upload the document again.
rate_limit|Тым көп әрекет. Бірнеше минуттан кейін қайталаңыз.|Слишком много попыток. Повторите через несколько минут.|Too many attempts. Try again in a few minutes.
not_found|Бет табылмады немесе сізге қолжетімсіз.|Страница не найдена или недоступна вам.|The page was not found or is unavailable to you.
back|Жеке кабинетке оралу|Вернуться в кабинет|Back to dashboard
source_note|Мұрағатта код пен лицензиялар бар. Жеке құжаттар мен құпиялар қосылмаған.|Архив содержит код и лицензии. Личные документы и секреты не включены.|The archive contains source code and licences, excluding private documents and secrets.
R_SIZE|Бет пішімі A4|Формат страниц A4|A4 page size
R_LENGTH|Жұмыс көлемі|Объём работы|Submission length
R_FONT|Негізгі мәтін қарпі|Шрифт основного текста|Body font
R_COLOR|Негізгі мәтін түсі|Цвет основного текста|Body text colour
R_MARGIN|Мәтіннің орналасуы мен өрістер|Расположение текста и поля|Text placement and margins
R_NUMBER|Беттер нөмірленуі|Нумерация страниц|Page numbering
R_STRUCTURE|Міндетті бөлімдер|Обязательные разделы|Required sections
R_HEADING|Бөлім тақырыптары|Заголовки разделов|Section headings
R_FIGURE|Сурет атаулары|Подписи рисунков|Figure captions
R_TABLE|Кесте атаулары|Подписи таблиц|Table captions
R_REFERENCE|Дереккөздерге сілтемелер|Ссылки на источники|Source citations
R_APPENDIX|Қосымшалар|Приложения|Appendices
R_SPACING|Жоларалық интервал|Межстрочный интервал|Line spacing
R_VISUAL|Күрделі элементтер|Сложные элементы|Complex elements
geometry|PDF координаттарын өлшеу|Измерение координат PDF|PDF coordinate measurements
text_method|Мәтін мен құрылымды тану|Распознавание текста и структуры|Text and structure recognition
font_method|Мәтін фрагменттерінің метадеректері|Метаданные текстовых фрагментов|Text span metadata
inference_method|Автоматты бағалау|Автоматическая оценка|Automated assessment
expected|Талап етіледі|Ожидается|Expected
observed|Анықталды|Обнаружено|Observed
review_original|Мәтіні мен ендірілген қаріптері бар PDF сақтап, тексеруді қайта іске қосыңыз.|Сохраните PDF с текстовым слоем и внедрёнными шрифтами и запустите проверку повторно.|Export a text-based PDF with embedded fonts and run the review again.
fix_format|Көрсетілген элементтің рәсімделуін түзетіп, PDF қайта жасаңыз.|Исправьте оформление указанного элемента и заново экспортируйте PDF.|Correct the indicated formatting and export the PDF again.
not_measurable|PDF деректері нақты қорытынды жасауға жеткіліксіз.|Данных PDF недостаточно для достоверного вывода.|PDF evidence is insufficient for a reliable conclusion.
no_evidence|Бұл элемент сенімді түрде анықталмады.|Элемент не удалось надёжно определить.|The element could not be reliably identified.
number_order|Бет нөмірлері төменгі орталықта, араб цифрларымен берілуі керек.|Номера страниц должны идти последовательно, арабскими цифрами, внизу по центру.|Page numbers must be consecutive Arabic numerals at the bottom centre.
structure_names|Мазмұны, кіріспе, қорытынды, пайдаланылған дереккөздер тізімі|Содержание, введение, заключение, список использованных источников|Contents, introduction, conclusion, references
minimum|Ең аз бет саны|Минимум страниц|Minimum pages
mixed_scans|Кейбір беттерде мәтін жоқ. Олардың талаптарға сәйкестігін анықтау үшін деректер жеткіліксіз.|На некоторых страницах нет текста. Данных для определения их соответствия недостаточно.|Some pages have no text. Their compliance cannot be established from the available data.
create_admin|Әкімші жасау|Создать администратора|Create administrator
admin_hint|Бірінші іске қосқанда тіркелген алғашқы пайдаланушы жергілікті әкімші болады.|При первом локальном запуске первый зарегистрированный пользователь становится администратором.|On the first local launch, the first registered user becomes the administrator.
admin_panel|Әкімшілік панель|Панель администратора|Administration
filter_all|Барлық нәтижелер|Все результаты|All results
no_changes|Өзгерістер қажет емес.|Изменения не требуются.|No changes required.
section_contents|Мазмұны|Содержание|Contents
section_introduction|Кіріспе|Введение|Introduction
section_conclusion|Қорытынды|Заключение|Conclusion
section_references|Пайдаланылған дереккөздер тізімі|Список использованных источников|References
image_count|Растрлық суреттер саны|Количество растровых иллюстраций|Raster illustration count
unchanged|Түпнұсқа өзгертілген жоқ|Оригинал не изменён|Original unchanged
how_it_works|Үш қарапайым қадам|Три простых шага|Three simple steps
step1|PDF жүктеңіз|Загрузите PDF|Upload your PDF
step2|Талаптарды тексереміз|Проверим требования|We check the rules
step3|Ұсыныстар алыңыз|Получите рекомендации|Get clear recommendations
draft|Алдын ала нұсқа|Предварительная версия|Preview release
home|Басты бет|Главная|Home
platform_label|Магистранттарға арналған платформа|Платформа для магистрантов|A platform for master's students
hero_title|Магистрлік жұмысыңызды сенімді тапсырыңыз|Подготовьте вашу работу к сдаче|Prepare your thesis for submission
hero_description|PDF құжатын жүктеңіз. Академия талаптарына сай рәсімдеуді автоматты тексеріп, әр бет бойынша түсінікті есеп алыңыз.|Загрузите PDF. Получите автоматическую проверку оформления по требованиям Академии и понятный отчёт по страницам.|Upload your PDF. Get an automatic review against the Academy's requirements and clear page-by-page findings.
academy_website|Академия сайты|Сайт Академии|Academy website
learn_more|Талаптармен танысу|Посмотреть требования|Explore the requirements
file_size_label|Файл көлемі|Размер файла|File size
page_limit_label|Құжат көлемі|Объём документа|Document length
languages_label|Интерфейс және есеп|Интерфейс и отчёт|Interface and reports
standard_label|Академия талаптары|Требования Академии|Academy requirements
upload_description|Жұмысыңыздың PDF нұсқасын таңдап, тіл мен оқу ұзақтығын көрсетіңіз.|Выберите PDF вашей работы, укажите язык и длительность программы.|Choose your thesis PDF, document language and programme duration.
processing_description|Жүйе бет пішімін, қаріпті, нөмірленуді және құрылымды автоматты тексереді.|Система автоматически проверит формат страниц, шрифт, нумерацию и структуру.|The system automatically checks page size, fonts, numbering and structure.
report_description|Ескертулерді беттерімен бірге көріп, PDF немесе JSON есебін жүктеңіз.|Просмотрите замечания с номерами страниц и скачайте отчёт PDF или JSON.|View findings with page numbers and download a PDF or JSON report.
ready_to_start|Жұмысыңыз дайын ба?|Готовы загрузить работу?|Ready to upload your thesis?
workspace_subtitle|Барлық жұмысыңыз бен тексеру нәтижелері бір жерде.|Все ваши работы и результаты проверок в одном месте.|Your submissions and review results, together in one place.
selected_standard|Тексеру талаптары|Требования проверки|Review requirements
upload_zone|PDF файлын осы жерге апарыңыз|Перетащите PDF сюда|Drop your PDF here
or_choose|немесе файлды таңдаңыз|или выберите файл|or choose a file
choose_file|Файл таңдау|Выбрать файл|Choose file
selected_file|Таңдалған файл|Выбранный файл|Selected file
no_file_selected|Файл таңдалмаған|Файл не выбран|No file selected
account_intro|Жұмыстарыңыз бен есептеріңізді жеке кабинетте сақтаңыз.|Храните ваши работы и отчёты в личном кабинете.|Keep your submissions and reports in your personal workspace.
have_account|Тіркелгіңіз бар ма?|Уже есть аккаунт?|Already have an account?
new_account|Әлі тіркелмедіңіз бе?|Ещё нет аккаунта?|New to the platform?
upload_step|Құжат|Документ|Document
review_step|Тексеру|Проверка|Review
report_step|Нәтиже|Результат|Results
preview|Құжатты көру|Просмотр документа|Document preview
open_pdf|PDF-ті ашу|Открыть PDF|Open PDF
view_page|Бетке өту|Перейти к странице|Go to page
preview_hint|Есептегі бет нөмірін басып, PDF құжатында сол бетке өтіңіз.|Нажмите номер страницы в отчёте, чтобы перейти к ней в PDF.|Select a page number in the report to jump to that page in the PDF.
automatic_label|Автоматты тексеру|Автоматическая проверка|Automated review
back_to_history|Тарихқа оралу|Вернуться к истории|Back to history
left_margin|Сол жақ|Слева|Left
right_margin|Оң жақ|Справа|Right
top_margin|Жоғары|Сверху|Top
bottom_margin|Төмен|Снизу|Bottom
skip_content|Мазмұнға өту|Перейти к содержимому|Skip to content
navigation|Негізгі мәзір|Основное меню|Main navigation
show_password|Құпиясөзді көрсету|Показать пароль|Show password
hide_password|Құпиясөзді жасыру|Скрыть пароль|Hide password
local_privacy|Түпнұсқа сақталады|Оригинал сохраняется|Original preserved
footer_description|Магистрлік жұмыстардың рәсімделуін тексеруге арналған цифрлық орта.|Цифровая среда для проверки оформления магистерских работ.|A digital workspace for reviewing master's thesis formatting.
'''

TEXT = {lang: {} for lang in ("kk", "ru", "en")}
for row in ROWS.strip().splitlines():
    key, *values = row.split("|")
    for lang, value in zip(TEXT, values):
        TEXT[lang][key] = value


def strings(lang):
    return TEXT.get(lang, TEXT["kk"])


def context(request):
    from .version import VERSION
    return {"t": strings(request.LANGUAGE_CODE), "interface_language": request.LANGUAGE_CODE, "app_version": VERSION}


def finding_text(finding, lang):
    t = strings(lang)
    result = dict(finding)
    result.update(title=t[finding["rule_id"]], status_label=t[finding["status"]],
                  method_label=t[finding["method"]],
                  explanation=t[finding.get("message", "observed")],
                  recommendation=t["no_changes" if finding["status"] in ("pass", "na") else "fix_format" if finding["status"] == "fail" else "review_original"])
    if result["evidence"] in ("contents", "introduction", "conclusion", "references"):
        result["evidence"] = t["section_" + result["evidence"]]
    if result["evidence"].startswith("Raster illustrations:"):
        result["evidence"] = t["image_count"] + ": " + result["evidence"].split(":", 1)[1].strip()
    return result
