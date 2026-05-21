"""Translate checks.py to Russian."""
path = r'd:\PycharmProjects\check_RF_site\backend\app\scanner\checks.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    # HTTPS
    ('"title": "HTTPS"', '"title": "Защищённое соединение HTTPS"'),
    ('"details": "HTTPS + HSTS"', '"details": "HTTPS настроен, HSTS включён"'),
    ('"details": "HTTPS OK, no HSTS"', '"details": "HTTPS работает, но HSTS не настроен"'),
    ('"title": "No HSTS"', '"title": "Не настроен HSTS"'),
    ('"description": "Strict-Transport-Security missing."', '"description": "Заголовок Strict-Transport-Security отсутствует. Без HSTS возможны атаки с понижением протокола."'),
    ('"recommendation": "Add HSTS header."', '"recommendation": "Добавьте заголовок Strict-Transport-Security: max-age=31536000; includeSubDomains"'),
    ('"details": "No HTTPS"', '"details": "Сайт не использует HTTPS — данные передаются в открытом виде"'),
    ('"title": "No HTTPS"', '"title": "Сайт не использует HTTPS"'),
    ('"description": "Data transmitted in plain text."', '"description": "Сайт работает по незащищённому протоколу HTTP. Данные пользователей (пароли, личная информация) передаются в открытом виде и могут быть перехвачены."'),
    ('"recommendation": "Install SSL certificate."', '"recommendation": "Установите SSL-сертификат (Let\'s Encrypt — бесплатно) и настройте редирект с HTTP на HTTPS."'),

    # Privacy Policy
    ('"title": "Privacy Policy"', '"title": "Политика обработки персональных данных"'),
    ('"details": f"Found ({sections_found}/{total} sections)"', '"details": f"Политика найдена, содержание раскрыто ({sections_found}/{total} разделов)"'),
    ('"details": f"Incomplete ({sections_found}/{total})"', '"details": f"Политика найдена, но раскрыта не полностью ({sections_found}/{total} разделов)"'),
    ('"title": "Incomplete privacy policy"', '"title": "Политика обработки данных раскрыта не полностью"'),
    ('"description": f"Only {sections_found}/{total} sections found."', '"description": f"В политике найдено только {sections_found} из {total} обязательных разделов. Отсутствуют: цели обработки, перечень данных, сроки хранения, права субъектов, меры защиты или информация о третьих лицах."'),
    ('"recommendation": "Complete the policy per 152-FZ."', '"recommendation": "Дополните политику недостающими разделами согласно требованиям ФЗ-152 «О персональных данных»."'),
    ('"details": "Minimal content"', '"details": "Страница политики найдена, но содержание минимально"'),
    ('"title": "Minimal privacy policy"', '"title": "Политика обработки данных содержит минимум информации"'),
    ('"description": "Key sections missing per 152-FZ."', '"description": "Страница политики найдена, но в ней отсутствуют ключевые разделы, требуемые ФЗ-152: цели обработки, перечень данных, сроки хранения, права субъектов."'),
    ('"recommendation": "Develop a full privacy policy."', '"recommendation": "Разработайте полноценную политику обработки персональных данных, включив все обязательные разделы."'),
    ('"details": "Not found"', '"details": "Политика обработки персональных данных не найдена"'),
    ('"title": "Missing privacy policy"', '"title": "Отсутствует политика обработки персональных данных"'),
    ('"description": "Violation of Art. 18.1 152-FZ."', '"description": "На сайте не найдена политика обработки персональных данных. Это прямое нарушение ст. 18.1 ФЗ-152 «О персональных данных»."'),
    ('"recommendation": "Publish a privacy policy."', '"recommendation": "Разместите политику обработки персональных данных. Документ должен быть доступен по прямой ссылке с любой страницы сайта и содержать: цели обработки, перечень данных, сроки хранения, права субъектов, меры защиты, информацию о передаче третьим лицам."'),

    # User Agreement
    ('"title": "User Agreement"', '"title": "Пользовательское соглашение"'),
    ('"details": f"Found: {found_url}"', '"details": f"Пользовательское соглашение найдено: {found_url}"'),
    ('"details": "Mentioned, no dedicated page"', '"details": "Упоминание пользовательского соглашения найдено, но отдельная страница не обнаружена"'),
    ('"title": "No dedicated agreement page"', '"title": "Пользовательское соглашение не вынесено на отдельную страницу"'),
    ('"description": "Harder to access."', '"description": "Пользовательское соглашение упоминается, но не имеет отдельной страницы, что затрудняет его доступность."'),
    ('"recommendation": "Create a dedicated page."', '"recommendation": "Создайте отдельную страницу с пользовательским соглашением и разместите ссылку в футере сайта."'),
    ('"title": "Missing user agreement"', '"title": "Отсутствует пользовательское соглашение"'),
    ('"description": "Required for sites with registration/payments."', '"description": "На сайте не найдено пользовательское соглашение. Для сайтов с регистрацией, личным кабинетом или платными услугами это обязательный документ."'),
    ('"recommendation": "Create and publish."', '"recommendation": "Разработайте и разместите пользовательское соглашение, регулирующее отношения между владельцем сайта и пользователями."'),

    # Form Consent
    ('"title": "Form Consent"', '"title": "Согласие на обработку данных в формах"'),
    ('"details": "No personal data forms found"', '"details": "Формы сбора персональных данных не обнаружены"'),
    ('"details": f"All {forms_found} forms have consent{extra}"', '"details": f"Во всех {forms_found} формах найдено согласие{extra}"'),
    ('"details": f"{missing}/{forms_found} forms lack consent"', '"details": f"В {missing} из {forms_found} форм не найдено согласие"'),
    ('"title": "Missing form consent"', '"title": "Отсутствует согласие на обработку данных в форме"'),
    ('"description": f"{missing} forms lack consent. Violation of Art. 9 152-FZ."', '"description": f"В {missing} из {forms_found} форм сбора персональных данных отсутствует явное согласие пользователя. Нарушение ст. 9 ФЗ-152."'),
    ('"recommendation": "Add consent checkbox with link to privacy policy."', '"recommendation": "Добавьте рядом с каждой формой чекбокс: «Я даю согласие на обработку персональных данных» со ссылкой на политику конфиденциальности. Чекбокс не должен быть предустановлен."'),

    # Cookie Banner
    ('"title": "Cookie Banner"', '"title": "Уведомление об использовании cookie"'),
    ('"details": "Banner with accept/reject"', '"details": "Cookie-баннер с кнопками принятия/отклонения найден"'),
    ('"details": "Banner without reject option"', '"details": "Cookie-баннер найден, но нет возможности отклонить cookie"'),
    ('"title": "No reject button"', '"title": "Cookie-баннер не позволяет отклонить cookie"'),
    ('"description": "Banner lacks explicit reject."', '"description": "Баннер информирует о cookie, но не предоставляет явной возможности отказаться. Это может не соответствовать требованиям GDPR и рекомендациям Роскомнадзора."'),
    ('"recommendation": "Add reject button."', '"recommendation": "Добавьте кнопку «Отклонить» или «Настроить» в cookie-баннер."'),
    ('"details": "Cookie mention without banner"', '"details": "Найдено упоминание cookie, но баннер не обнаружен"'),
    ('"title": "No explicit banner"', '"title": "Нет явного cookie-баннера"'),
    ('"description": "Cookies mentioned without banner."', '"description": "Cookie упоминаются на сайте, но нет явного баннера с уведомлением и выбором."'),
    ('"recommendation": "Add cookie banner."', '"recommendation": "Добавьте всплывающий баннер с информацией об использовании cookie и кнопками «Принять» / «Отклонить»."'),
    ('"title": "Missing cookie notice"', '"title": "Отсутствует уведомление об использовании cookie"'),
    ('"description": "Recommended to inform about cookies."', '"description": "На сайте не найдено уведомление об использовании cookie-файлов. Рекомендуется информировать пользователей."'),
    ('"recommendation": "Add cookie banner."', '"recommendation": "Добавьте cookie-баннер с информацией об использовании файлов cookie и возможностью принять или отклонить их."'),

    # Advertising
    ('"title": "Ad Marking (ERID)"', '"title": "Маркировка рекламы (ERID)"'),
    ('"details": "No ads detected"', '"details": "Признаки рекламных материалов не обнаружены"'),
    ('"details": "ERID present"', '"details": "Рекламные материалы содержат маркировку ERID"'),
    ('"details": "Ads without ERID"', '"details": "Обнаружены признаки рекламы без маркировки ERID"'),
    ('"title": "Missing ERID marking"', '"title": "Отсутствует маркировка рекламы (ERID)"'),
    ('"description": "Ads detected without ERID token. Violation of 347-FZ."', '"description": "На сайте обнаружены признаки рекламных материалов, но маркировка ERID не найдена. С 1 сентября 2022 года интернет-реклама в РФ должна маркироваться (ФЗ-347)."'),
    ('"recommendation": "Register with ORD and get ERID tokens."', '"recommendation": "Зарегистрируйтесь в ОРД (оператор рекламных данных), получите токен ERID и разместите его на всех рекламных материалах вместе с пометкой «реклама» и указанием рекламодателя."'),

    # Company Requisites
    ('"title": "Company Requisites"', '"title": "Реквизиты компании"'),
    ('"details": f"Found ({score}/7)"', '"details": f"Реквизиты компании найдены ({score}/7)"'),
    ('"details": f"Partial ({score}/7). Missing: {missing_items}"', '"details": f"Реквизиты найдены частично ({score}/7). Отсутствует: {missing_items}"'),
    ('"title": "Incomplete requisites"', '"title": "Неполные реквизиты компании"'),
    ('"description": f"Missing: {missing_items}."', '"description": f"Найдено {score} из 7 реквизитов. Отсутствует: {missing_items}. Ст. 10 ЗоЗПП требует полного раскрытия информации о продавце."'),
    ('"recommendation": "Add missing company details."', '"recommendation": "Добавьте недостающие реквизиты на страницу «О компании» или «Реквизиты»."'),
    ('"details": f"Minimal ({score}/7)"', '"details": f"Найдены минимальные реквизиты ({score}/7)"'),
    ('"title": "Minimal requisites"', '"title": "Минимальные реквизиты компании"'),
    ('"description": f"Only {score}/7 found."', '"description": f"Найдено только {score} из 7 реквизитов. Для интернет-магазинов и сервисов это критично."'),
    ('"recommendation": "Add full company details."', '"recommendation": "Разместите полные реквизиты: наименование, ИНН, ОГРН, КПП, юридический адрес, телефон, email, ФИО руководителя."'),
    ('"title": "Missing requisites"', '"title": "Отсутствуют реквизиты компании"'),
    ('"description": "No company details found."', '"description": "На сайте не найдены реквизиты компании. Ст. 10 ЗоЗПП обязывает продавцов раскрывать: наименование, ИНН, ОГРН, адрес, контакты."'),
    ('"recommendation": "Create a requisites page."', '"recommendation": "Создайте страницу «Реквизиты» с полными данными компании."'),

    # Consumer Rights
    ('"title": "Consumer Documents"', '"title": "Документы для потребителей"'),
    ('"details": f"Found ({found_count}/5)"', '"details": f"Основные документы для потребителей найдены ({found_count}/5)"'),
    ('"details": f"Missing: {missing}"', '"details": f"Не найдены: {missing}"'),
    ('"title": f"Missing: {missing}"', '"title": f"Отсутствуют документы: {missing}"'),
    ('"description": f"Missing documents: {missing}."', '"description": f"Не найдены: {missing}. ЗоЗПП требует предоставления полной информации об условиях продажи."'),
    ('"recommendation": f"Add pages for: {missing}."', '"recommendation": f"Разместите страницы: {missing}. Информация должна быть доступна до покупки."'),
    ('"details": f"Most missing ({found_count}/5)"', '"details": f"Практически все документы отсутствуют. Найдено: {found_count}/5"'),
    ('"title": "Critical lack of consumer docs"', '"title": "Критическое отсутствие документов для потребителей"'),
    ('"description": f"Only {found_count}/5 documents found."', '"description": f"Найдено только {found_count} из 5 обязательных документов. Это серьёзное нарушение ЗоЗПП."'),
    ('"recommendation": "Add all required consumer documents urgently."', '"recommendation": "Срочно разместите: оферту/договор, условия возврата, доставки, оплаты и гарантийные обязательства."'),

    # Age Marking
    ('"title": "Age Marking (18+)"', '"title": "Возрастная маркировка (18+)"'),
    ('"details": "No adult content"', '"details": "Контент для взрослых не обнаружен"'),
    ('"details": "Age marking present"', '"details": "Возрастная маркировка присутствует"'),
    ('"details": "Adult content without marking"', '"details": "Обнаружен контент для взрослых без возрастной маркировки"'),
    ('"title": "Missing 18+ marking"', '"title": "Отсутствует возрастная маркировка 18+"'),
    ('"description": "Adult content without age marking. Violation of 436-FZ."', '"description": "На сайте обнаружен контент, который может относиться к категории 18+, но маркировка отсутствует. Нарушение ФЗ-436 «О защите детей от информации»."'),
    ('"recommendation": "Add 18+ marking."', '"recommendation": "Добавьте маркировку «18+» на сайт и все страницы с соответствующим контентом."'),

    # Copyright
    ('"title": "Copyright"', '"title": "Копирайт и правовая информация"'),
    ('"details": "Copyright found"', '"details": "Информация о правообладателе найдена"'),
    ('"title": "Missing copyright"', '"title": "Отсутствует копирайт"'),
    ('"description": "No copyright notice."', '"description": "На сайте не указан правообладатель и год. Это не нарушение, но снижает доверие и затрудняет защиту авторских прав."'),
    ('"recommendation": "Add copyright in footer."', '"recommendation": "Добавьте в футер: © [Год] [Название компании]. Все права защищены."'),

    # Contacts
    ('"title": "Contact Info"', '"title": "Контактная информация"'),
    ('"details": f"Found ({score}/5)"', '"details": f"Контакты указаны ({score}/5)"'),
    ('"details": f"Partial ({score}/5). Missing: {missing}"', '"details": f"Контакты указаны частично ({score}/5). Нет: {missing}"'),
    ('"title": "Incomplete contacts"', '"title": "Неполная контактная информация"'),
    ('"description": f"Missing: {missing}."', '"description": f"Отсутствует: {missing}. Пользователи должны иметь возможность связаться с компанией."'),
    ('"recommendation": "Add missing contact info."', '"recommendation": "Добавьте недостающую контактную информацию на сайт."'),
    ('"details": "Almost no contacts"', '"details": "Контактная информация практически отсутствует"'),
    ('"title": "Missing contacts"', '"title": "Отсутствует контактная информация"'),
    ('"description": "No contact information found."', '"description": "На сайте не найдены контакты: телефон, email, адрес. Это подрывает доверие и нарушает требования к раскрытию информации."'),
    ('"recommendation": "Add phone, email, address."', '"recommendation": "Разместите на видном месте телефон, email, физический адрес и график работы."'),

    # Payment Security
    ('"title": "Payment Security"', '"title": "Безопасность платежей"'),
    ('"details": "No payment forms"', '"details": "Платёжные формы не обнаружены"'),
    ('"details": "Security info present"', '"details": "Информация о безопасности платежей присутствует"'),
    ('"details": "Payments without security info"', '"details": "Есть приём платежей, но нет информации о безопасности"'),
    ('"title": "No payment security info"', '"title": "Нет информации о безопасности платежей"'),
    ('"description": "Site accepts payments without security disclosure."', '"description": "Сайт принимает платежи, но не информирует пользователей о безопасности транзакций. Это снижает доверие и может нарушать требования платёжных систем."'),
    ('"recommendation": "Add SSL, PCI DSS, 3D Secure info."', '"recommendation": "Разместите информацию о безопасности платежей: использование SSL, соответствие PCI DSS, 3D Secure."'),

    # Technical
    ('"title": "<title>"', '"title": "Тег <title>"'),
    ('"details": f"Title: {title_text[:80]}"', '"details": f"Title: {title_text[:80]}"'),
    ('"details": f"Too short ({title_len} chars)"', '"details": f"Title слишком короткий ({title_len} символов)"'),
    ('"title": "Short <title>"', '"title": "Слишком короткий тег <title>"'),
    ('"description": f"Title: {title_len} chars."', '"description": f"Длина title: {title_len} символов. Рекомендуется 30–60 символов для SEO."'),
    ('"recommendation": "Use 30-60 chars."', '"recommendation": "Увеличьте title до 30–60 символов, включив ключевые слова."'),
    ('"details": "Missing"', '"details": "Тег <title> отсутствует"'),
    ('"title": "Missing <title>"', '"title": "Отсутствует тег <title>"'),
    ('"description": "Critical for SEO."', '"description": "Страница не имеет тега <title>. Это критично для SEO и отображения в поисковой выдаче."'),
    ('"recommendation": "Add <title>."', '"recommendation": "Добавьте уникальный тег <title> длиной 30–60 символов."'),

    # Meta description
    ('"title": "Meta description"', '"title": "Meta description"'),
    ('"details": f"Description ({desc_len} chars)"', '"details": f"Description ({desc_len} символов)"'),

    # Viewport
    ('"title": "Viewport (mobile)"', '"title": "Viewport (мобильная адаптация)"'),
    ('"details": "Present"', '"details": "Viewport meta-тег присутствует"'),
    ('"details": "Missing - may not be mobile-friendly"', '"details": "Viewport meta-тег отсутствует — сайт может быть не адаптирован под мобильные"'),

    # Favicon
    ('"title": "Favicon"', '"title": "Favicon"'),
    ('"details": "Found"', '"details": "Favicon найден"'),
    ('"details": "Not found"', '"details": "Favicon не найден"'),

    # Charset
    ('"title": "Charset"', '"title": "Кодировка (charset)"'),
    ('"details": "Specified"', '"details": "Кодировка указана"'),
    ('"details": "Not specified"', '"details": "Кодировка не указана явно"'),

    # H1
    ('"title": "H1 heading"', '"title": "Заголовок H1"'),
    ('"details": f"H1: {h1_tags[0].get_text(strip=True)[:80]}"', '"details": f"H1: {h1_tags[0].get_text(strip=True)[:80]}"'),
    ('"details": f"Multiple H1 ({len(h1_tags)})"', '"details": f"Найдено несколько H1 ({len(h1_tags)}) — должен быть один"'),
    ('"details": "Missing"', '"details": "H1 отсутствует"'),

    # Open Graph
    ('"title": "Open Graph"', '"title": "Open Graph разметка"'),
    ('"details": f"OG tags: {og_count}/3"', '"details": f"OG-теги: {og_count}/3 (title, description, image)"'),
    ('"details": "No OG tags"', '"details": "Open Graph теги отсутствуют — превью в соцсетях не настроены"'),

    # Images alt
    ('"title": "Image alt attributes"', '"title": "Alt-атрибуты изображений"'),
    ('"details": f"Alt on {images_with_alt}/{len(images)} images"', '"details": f"Alt у {images_with_alt}/{len(images)} изображений"'),
    ('"details": "No images"', '"details": "Изображения не найдены"'),

    # Robots
    ('"title": "robots.txt"', '"title": "Файл robots.txt"'),
    ('"details": "Available"', '"details": "robots.txt доступен"'),
    ('"details": "Not available"', '"details": "robots.txt недоступен"'),

    # Sitemap
    ('"title": "sitemap.xml"', '"title": "Файл sitemap.xml"'),
    ('"details": "Available"', '"details": "sitemap.xml доступен"'),
    ('"details": "Not available"', '"details": "sitemap.xml недоступен"'),

    # Server Location
    ('"title": "Server Localization (152-FZ)"', '"title": "Локализация серверов (152-ФЗ)"'),
    ('"details": f"Server in Russia ({geo_country})"', '"details": f"Сервер находится в России ({geo_country})"'),
    ('"details": f"Server outside RF ({geo_country}). Personal data of RF citizens must be stored in Russia per 152-FZ Art. 18.5."', '"details": f"Сервер находится за пределами РФ ({geo_country}). Для обработки персональных данных граждан РФ требуется перенос серверов в Россию."'),
    ('"title": "Server outside Russian Federation"', '"title": "Сервер находится за пределами РФ"'),
    ('"description": f"Server IP ({server_ip}) located in {geo_country}. Art. 18.5 of 152-FZ requires recording, systematization, accumulation, storage, clarification and extraction of personal data of RF citizens to be done using databases located in Russia."', '"description": f"IP-адрес сервера ({server_ip}) геолоцируется в стране {geo_country}. Согласно ч. 5 ст. 18 ФЗ-152 «О персональных данных», запись, систематизация, накопление, хранение, уточнение и извлечение персональных данных граждан РФ должны осуществляться с использованием баз данных, находящихся на территории России."'),
    ('"recommendation": "Move servers/databases to Russia. Use Russian hosting providers (Selectel, DataLine, Rostelecom-DPC, etc.)."', '"recommendation": "Перенесите серверы/базы данных на территорию РФ. Используйте российских хостинг-провайдеров (Selectel, DataLine, Ростелеком-ЦОД и др.)."'),
    ('"details": "Could not determine server location. Verify manually."', '"details": "Не удалось определить местоположение сервера. Рекомендуется проверить вручную."'),
    ('"title": "Server location unknown"', '"title": "Не удалось определить геолокацию сервера"'),
    ('"description": "Could not determine server country. Verify manually for 152-FZ compliance."', '"description": "Не удалось определить страну размещения сервера. Для соблюдения 152-ФЗ необходимо убедиться, что серверы находятся в РФ."'),
    ('"recommendation": "Check server geolocation via whois. Ensure hosting in Russia."', '"recommendation": "Проверьте геолокацию сервера вручную через whois-сервисы. Убедитесь, что хостинг-провайдер предоставляет серверы в РФ."'),

    # RKN
    ('"title": "RKN Notification (152-FZ Art. 22)"', '"title": "Уведомление Роскомнадзора (ст. 22 ФЗ-152)"'),
    ('"details": "RKN registration mention found"', '"details": "Найдено упоминание регистрации в РКН"'),
    ('"details": "No RKN registration info found"', '"details": "Не найдено информации о регистрации в реестре операторов ПДн"'),
    ('"title": "No Roskomnadzor notification info"', '"title": "Отсутствует информация об уведомлении Роскомнадзора"'),
    ('"description": "Per Art. 22 of 152-FZ, personal data operators must notify Roskomnadzor before processing begins. Absence of this info on site may indicate violation."', '"description": "Согласно ст. 22 ФЗ-152, оператор персональных данных обязан уведомить Роскомнадзор о начале обработки персональных данных. Отсутствие информации об этом на сайте может означать нарушение."'),
    ('"recommendation": "Submit notification to RKN via pd.rkn.gov.ru and publish registration info on site."', '"recommendation": "Подайте уведомление в Роскомнадзор через портал pd.rkn.gov.ru и разместите информацию о регистрации на сайте."'),

    # Full Age Marking
    ('"title": "Age Marking (436-FZ)"', '"title": "Возрастная маркировка (436-ФЗ)"'),
    ('"details": "Age marking present"', '"details": "Возрастная маркировка присутствует"'),
    ('"details": "No age marking found. Required by 436-FZ for all public websites in Russia."', '"details": "Возрастная маркировка не найдена. Требуется по 436-ФЗ для всех сайтов в РФ."'),
    ('"title": "Missing age marking (436-FZ)"', '"title": "Отсутствует возрастная маркировка (436-ФЗ)"'),
    ('"description": "Federal Law 436-FZ \'On Protection of Children from Harmful Information\' requires all websites accessible in Russia to display age category marking (0+, 6+, 12+, 16+ or 18+)."', '"description": "ФЗ-436 «О защите детей от информации, причиняющей вред их здоровью и развитию» требует от всех сайтов, доступных в РФ, размещать знак возрастной категории (0+, 6+, 12+, 16+ или 18+)."'),
    ('"recommendation": "Add age marking (e.g., \'16+\') in footer or header of every page."', '"recommendation": "Добавьте возрастную маркировку (например, «16+») в футер или хедер каждой страницы."'),

    # Domain Requirements
    ('"title": "Domain Zone Requirements"', '"title": "Требования к доменной зоне"'),
    ('"details": "Not a .ru/.rf domain - no special requirements"', '"details": "Не домен .ru/.рф — особых требований нет"'),
    ('"title": "Domain Zone Requirements (.ru/.rf)"', '"title": "Требования к доменной зоне (.ru/.рф)"'),
    ('"details": "Site owner info found"', '"details": "Информация о владельце сайта найдена"'),
    ('"details": ".ru/.rf domain: site owner info not found on site. Required by domain registry rules."', '"details": "Домен .ru/.рф: информация о владельце сайта не найдена. Требуется правилами регистратуры."'),
    ('"title": "Missing site owner info for .ru/.rf domain"', '"title": "Отсутствует информация о владельце для домена .ru/.рф"'),
    ('"description": ".ru and .rf domain registry rules require publishing administrator/owner contact information on the website."', '"description": "Правила регистратуры доменов .ru и .рф требуют публикации контактной информации администратора/владельца на сайте."'),
    ('"recommendation": "Add site administrator contact info on the website."', '"recommendation": "Добавьте контактную информацию администратора сайта."'),

    # Self-Employed
    ('"title": "Self-Employed / IP Marking"', '"title": "Маркировка ИП / самозанятых"'),
    ('"details": "No IE/self-employed indicators"', '"details": "Признаки ИП/самозанятого не обнаружены"'),
    ('"details": "IE details found"', '"details": "Данные ИП найдены"'),
    ('"details": "IE indicators found but details incomplete"', '"details": "Признаки ИП найдены, но данные неполные"'),
    ('"title": "Incomplete IE/self-employed info"', '"title": "Неполные данные ИП/самозанятого"'),
    ('"description": "Individual entrepreneur or self-employed indicators found but full name and OGRNIP not provided. Required by consumer protection law."', '"description": "Обнаружены признаки ИП или самозанятого, но ФИО и ОГРНИП не указаны. Требуется законом о защите прав потребителей."'),
    ('"recommendation": "Add full name of IE and OGRNIP number on the website."', '"recommendation": "Добавьте ФИО ИП и номер ОГРНИП на сайт."'),
]

count = 0
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        count += 1
    else:
        print(f'MISS: {old[:80]}...')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f'Done: {count}/{len(replacements)} replacements')
