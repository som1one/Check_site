import re
import socket
import httpx
from bs4 import BeautifulSoup
from typing import Optional, List, Tuple
from urllib.parse import urljoin, urlparse

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MAX_PAGES = 12
TIMEOUT = 15


# ============================================================================
# Загрузка страниц
# ============================================================================

async def fetch_page(url: str, timeout: int = TIMEOUT) -> Tuple[Optional[str], Optional[str]]:
    """HTTP-запрос с фолбэком на verify=False (для самоподписанных)."""
    try:
        async with httpx.AsyncClient(
            headers=HEADERS, follow_redirects=True, timeout=timeout, verify=True,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text, str(resp.url)
    except httpx.ConnectError:
        try:
            async with httpx.AsyncClient(
                headers=HEADERS, follow_redirects=True, timeout=timeout, verify=False,
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.text, str(resp.url)
        except Exception:
            return None, None
    except Exception:
        return None, None


async def fetch_page_playwright(url: str, timeout: int = TIMEOUT) -> Optional[str]:
    """Фолбэк через Playwright для SPA-сайтов."""
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page()
            await page.set_extra_http_headers(HEADERS)
            await page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)
            html = await page.content()
            await browser.close()
            return html
    except Exception:
        return None


async def fetch_sitemap_links(base_url: str, timeout: int = TIMEOUT) -> List[str]:
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    links = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=timeout, verify=False) as client:
            r = await client.get(f"{base}/sitemap.xml")
            if r.status_code == 200:
                try:
                    soup = BeautifulSoup(r.text, "lxml-xml")
                except Exception:
                    soup = BeautifulSoup(r.text, "html.parser")
                for loc in soup.find_all("loc"):
                    href = loc.get_text(strip=True)
                    if href:
                        links.append(href)
    except Exception:
        pass
    return links[:MAX_PAGES * 2]


def extract_all_internal_links(html: str, base_url: str) -> List[str]:
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc
    seen = set()
    important = []
    normal = []

    priority_selectors = [
        "footer a", "header a", "nav a", ".footer a", ".header a",
        ".menu a", ".navbar a", "[class*=footer] a", "[class*=header] a",
        "[class*=menu] a", "[class*=nav] a",
    ]

    def process_tag(tag, is_priority: bool):
        href = (tag.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            return
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.netloc != base_domain:
            return
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            clean += f"?{parsed.query}"
        if clean in seen:
            return
        seen.add(clean)
        if is_priority:
            important.append(clean)
        else:
            normal.append(clean)

    for selector in priority_selectors:
        for tag in soup.select(selector):
            process_tag(tag, True)

    for tag in soup.find_all("a", href=True):
        process_tag(tag, False)

    result = important + [u for u in normal if u not in set(important)]
    return result[:MAX_PAGES]


# ============================================================================
# Вспомогательные функции
# ============================================================================

def _all_text(pages_html: dict) -> str:
    combined = ""
    for html in pages_html.values():
        soup = BeautifulSoup(html, "lxml")
        combined += " " + soup.get_text(" ", strip=True)
    return combined.lower()


def _all_html(pages_html: dict) -> str:
    return " ".join(pages_html.values()).lower()


def _find_link_by_keywords(pages_html: dict, links: List[str], keywords: List[str]) -> Optional[str]:
    """Ищем URL, в пути которого есть одно из ключевых слов."""
    for url in pages_html:
        u = url.lower()
        if any(kw in u for kw in keywords):
            return url
    for link in links:
        if any(kw in link.lower() for kw in keywords):
            return link
    return None


# ============================================================================
# 1. HTTPS / SSL
# ============================================================================

async def check_https_detailed(final_url: str, timeout: int = TIMEOUT) -> Tuple[dict, list]:
    is_https = final_url.startswith("https://")
    hsts = False
    redirect_ok = False
    evidence = [f"Итоговый URL: {final_url}"]

    if is_https:
        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=timeout, verify=False) as client:
                resp = await client.get(final_url)
                hsts = "strict-transport-security" in {k.lower() for k in resp.headers.keys()}
                if hsts:
                    evidence.append("Заголовок HSTS присутствует")
                else:
                    evidence.append("Заголовок HSTS не найден")
        except Exception:
            pass

        http_url = final_url.replace("https://", "http://", 1)
        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=timeout, follow_redirects=True, verify=False) as client:
                r = await client.get(http_url)
                if str(r.url).startswith("https://"):
                    redirect_ok = True
                    evidence.append("Редирект HTTP → HTTPS работает")
                else:
                    evidence.append("Редирект HTTP → HTTPS не настроен")
        except Exception:
            pass

    if is_https and hsts and redirect_ok:
        return {
            "code": "https", "title": "Защищённое соединение HTTPS",
            "status": "passed",
            "details": "HTTPS настроен, HSTS включён, редирект с HTTP работает",
            "evidence": evidence,
        }, []

    if is_https and not hsts:
        return {
            "code": "https", "title": "Защищённое соединение HTTPS",
            "status": "warning",
            "details": "HTTPS работает, но HSTS не настроен" + ("" if redirect_ok else "; редирект с HTTP не настроен"),
            "evidence": evidence,
        }, [{
            "code": "no_hsts", "title": "Не настроен HSTS",
            "severity": "low", "category": "technical",
            "description": "Заголовок Strict-Transport-Security отсутствует. Без HSTS возможны атаки с понижением протокола до HTTP.",
            "recommendation": "Добавьте заголовок Strict-Transport-Security: max-age=31536000; includeSubDomains в конфигурацию веб-сервера.",
            "evidence": evidence, "possible_fine": None,
        }]

    if is_https:
        return {
            "code": "https", "title": "Защищённое соединение HTTPS",
            "status": "warning",
            "details": "HTTPS работает, но редирект с HTTP не настроен",
            "evidence": evidence,
        }, [{
            "code": "no_http_redirect", "title": "Нет редиректа с HTTP на HTTPS",
            "severity": "low", "category": "technical",
            "description": "При обращении по HTTP браузер не перенаправляется на HTTPS, что снижает уровень защиты.",
            "recommendation": "Настройте 301-редирект с http:// на https:// для всех страниц.",
            "evidence": evidence, "possible_fine": None,
        }]

    return {
        "code": "https", "title": "Защищённое соединение HTTPS",
        "status": "failed",
        "details": "Сайт работает по незащищённому протоколу HTTP",
        "evidence": evidence,
    }, [{
        "code": "no_https", "title": "Сайт не использует HTTPS",
        "severity": "high", "category": "technical",
        "description": "Сайт работает по незащищённому протоколу HTTP. Данные пользователей (пароли, личная информация) передаются в открытом виде и могут быть перехвачены.",
        "recommendation": "Установите SSL-сертификат (Let's Encrypt — бесплатно) и настройте редирект с HTTP на HTTPS.",
        "evidence": evidence, "possible_fine": None,
    }]


# ============================================================================
# 2. 152-ФЗ — Политика обработки персональных данных
# ============================================================================

PRIVACY_PAGE_KW = [
    "policy", "privacy", "personal-data", "personal_data", "pdn",
    "политик", "конфиденциал", "персональн", "данн", "обработк",
]

PRIVACY_SECTION_KW = {
    "Цели обработки": [
        "цели обработки", "цель обработки", "цели сбора", "цели использования",
        "purposes of processing", "purpose of processing",
    ],
    "Перечень данных": [
        "перечень персональных данных", "категории персональных данных",
        "состав персональных данных", "какие данные мы собираем",
        "list of personal data", "data categories",
    ],
    "Сроки хранения": [
        "срок хранения", "сроки хранения", "период хранения", "уничтожение",
        "хранятся в течение", "retention period", "storage period",
    ],
    "Права субъектов": [
        "права субъекта", "права пользователя", "вы имеете право",
        "отозвать согласие", "отзыв согласия", "withdraw consent",
    ],
    "Меры защиты": [
        "меры защиты", "обеспечение безопасности", "шифрование",
        "защита персональных данных", "data protection", "security measures",
    ],
    "Передача третьим лицам": [
        "третьим лицам", "третьи лица", "передача данных", "раскрытие",
        "third parties",
    ],
}


def check_privacy_policy(pages_html: dict, links: List[str]) -> Tuple[dict, list]:
    all_text = _all_text(pages_html)

    found_sections = {name: any(kw in all_text for kw in kws) for name, kws in PRIVACY_SECTION_KW.items()}
    sections_found = sum(found_sections.values())
    total = len(PRIVACY_SECTION_KW)
    missing_sections = [name for name, ok in found_sections.items() if not ok]

    policy_url = _find_link_by_keywords(pages_html, links, PRIVACY_PAGE_KW)

    evidence = []
    if policy_url:
        evidence.append(f"Страница политики: {policy_url}")
    for name, ok in found_sections.items():
        evidence.append(f"Раздел «{name}»: " + ("найден" if ok else "не найден"))

    if sections_found >= 5 and policy_url:
        return {
            "code": "privacy_policy", "title": "152-ФЗ — Политика обработки персональных данных",
            "status": "passed",
            "details": f"Политика найдена, раскрыто {sections_found} из {total} обязательных разделов",
            "evidence": evidence,
        }, []

    if sections_found >= 3 and policy_url:
        return {
            "code": "privacy_policy", "title": "152-ФЗ — Политика обработки персональных данных",
            "status": "warning",
            "details": f"Политика найдена, но раскрыта не полностью ({sections_found}/{total}). Не хватает: {', '.join(missing_sections)}",
            "evidence": evidence,
        }, [{
            "code": "incomplete_privacy_policy",
            "title": "Политика обработки персональных данных раскрыта не полностью",
            "severity": "medium", "category": "personal_data",
            "description": (
                f"В политике найдено только {sections_found} из {total} обязательных разделов. "
                f"Отсутствуют: {', '.join(missing_sections)}. Согласно ст. 18.1 ФЗ-152 политика "
                "должна содержать сведения о целях обработки, перечне ПДн, сроках хранения, правах субъектов, "
                "мерах защиты и передаче третьим лицам."
            ),
            "recommendation": "Дополните политику недостающими разделами согласно требованиям ФЗ-152 «О персональных данных».",
            "evidence": evidence, "possible_fine": 150000,
        }]

    if policy_url:
        return {
            "code": "privacy_policy", "title": "152-ФЗ — Политика обработки персональных данных",
            "status": "warning",
            "details": f"Страница политики найдена, но содержание минимальное ({sections_found}/{total} разделов)",
            "evidence": evidence,
        }, [{
            "code": "minimal_privacy_policy",
            "title": "Политика обработки данных содержит минимум информации",
            "severity": "high", "category": "personal_data",
            "description": (
                f"Страница политики найдена, но раскрыто только {sections_found} из {total} обязательных разделов. "
                f"Отсутствуют: {', '.join(missing_sections)}. Это нарушение ст. 18.1 ФЗ-152."
            ),
            "recommendation": "Разработайте полноценную политику обработки персональных данных с обязательными разделами.",
            "evidence": evidence, "possible_fine": 300000,
        }]

    return {
        "code": "privacy_policy", "title": "152-ФЗ — Политика обработки персональных данных",
        "status": "failed",
        "details": "Политика обработки персональных данных не найдена",
        "evidence": evidence,
    }, [{
        "code": "missing_privacy_policy",
        "title": "Отсутствует политика обработки персональных данных",
        "severity": "high", "category": "personal_data",
        "description": (
            "На сайте не найдена политика обработки персональных данных. "
            "Это прямое нарушение ст. 18.1 ФЗ-152 «О персональных данных». "
            "Документ обязателен для любого сайта, который собирает любые персональные данные пользователей."
        ),
        "recommendation": (
            "Разместите политику обработки персональных данных. Документ должен быть доступен по прямой ссылке "
            "с любой страницы сайта (обычно в футере) и содержать: цели обработки, перечень данных, сроки хранения, "
            "права субъектов, меры защиты, информацию о передаче третьим лицам."
        ),
        "evidence": evidence, "possible_fine": 300000,
    }]


# ============================================================================
# 3. 152-ФЗ — Согласие на обработку данных в формах
# ============================================================================

CONSENT_KW = [
    "согласие на обработку", "согласен на обработку", "согласна на обработку",
    "обработку персональных данных", "политику конфиденциальности",
    "политикой конфиденциальности", "пользовательским соглашением",
    "consent to processing", "i consent", "i agree", "privacy policy",
]
PERSONAL_INPUT_TYPES = {"email", "tel", "phone", "number"}
PERSONAL_INPUT_NAMES = [
    "email", "phone", "tel", "name", "fio", "firstname", "lastname",
    "username", "имя", "фио", "телефон", "почта",
]


def check_form_consent(pages_html: dict) -> Tuple[dict, list]:
    forms_total = 0
    forms_with_consent = 0
    forms_with_checkbox = 0
    evidence = []

    for url, html in pages_html.items():
        soup = BeautifulSoup(html, "lxml")
        for form in soup.find_all("form"):
            inputs = form.find_all("input")
            has_personal = False
            for inp in inputs:
                itype = (inp.get("type") or "").lower()
                iname = (inp.get("name") or inp.get("id") or inp.get("placeholder") or "").lower()
                if itype in PERSONAL_INPUT_TYPES or any(n in iname for n in PERSONAL_INPUT_NAMES):
                    has_personal = True
                    break
            if not has_personal:
                continue

            forms_total += 1
            form_text = form.get_text(" ", strip=True).lower()
            parent_text = (form.parent.get_text(" ", strip=True).lower() if form.parent else "")
            combined = form_text + " " + parent_text

            checkbox_consent = False
            for cb in form.find_all("input", type="checkbox"):
                cb_name = (cb.get("name") or "").lower()
                cb_parent = (cb.parent.get_text(" ", strip=True).lower() if cb.parent else "")
                if any(kw in (cb_name + " " + cb_parent) for kw in CONSENT_KW):
                    checkbox_consent = True
                    break
            if checkbox_consent:
                forms_with_checkbox += 1

            if any(kw in combined for kw in CONSENT_KW) or checkbox_consent:
                forms_with_consent += 1
                evidence.append(f"Форма на {url}: согласие найдено" + (" (чекбокс)" if checkbox_consent else ""))
            else:
                evidence.append(f"Форма на {url}: согласие НЕ найдено")

    if forms_total == 0:
        return {
            "code": "form_consent", "title": "152-ФЗ — Согласие на обработку данных в формах",
            "status": "passed",
            "details": "Формы сбора персональных данных не обнаружены",
            "evidence": [],
        }, []

    if forms_with_consent >= forms_total:
        extra = f", в том числе {forms_with_checkbox} с чекбоксом" if forms_with_checkbox else ""
        return {
            "code": "form_consent", "title": "152-ФЗ — Согласие на обработку данных в формах",
            "status": "passed",
            "details": f"Во всех {forms_total} формах с персональными данными найдено согласие{extra}",
            "evidence": evidence,
        }, []

    missing = forms_total - forms_with_consent
    status = "failed" if missing == forms_total else "warning"
    return {
        "code": "form_consent", "title": "152-ФЗ — Согласие на обработку данных в формах",
        "status": status,
        "details": f"В {missing} из {forms_total} форм не найдено согласие на обработку персональных данных",
        "evidence": evidence,
    }, [{
        "code": "missing_form_consent",
        "title": "Не получается согласие на обработку ПДн в формах",
        "severity": "high", "category": "personal_data",
        "description": (
            f"В {missing} из {forms_total} форм с персональными данными отсутствует чекбокс или текст согласия. "
            "Это нарушение ст. 9 ФЗ-152: обработка персональных данных без согласия субъекта недопустима."
        ),
        "recommendation": (
            "Добавьте в каждую форму чекбокс «Я согласен на обработку персональных данных» со ссылкой "
            "на политику конфиденциальности. Без отметки чекбокса кнопка отправки должна быть неактивна."
        ),
        "evidence": evidence, "possible_fine": 150000,
    }]


# ============================================================================
# 4. 152-ФЗ — Локализация серверов (ст. 18.5)
# ============================================================================

async def check_server_location(final_url: str, timeout: int = TIMEOUT) -> Tuple[dict, list]:
    parsed = urlparse(final_url)
    hostname = parsed.netloc

    server_ip = None
    try:
        server_ip = socket.gethostbyname(hostname)
    except Exception:
        pass

    geo_country = None
    geo_country_full = None
    geo_org = None
    if server_ip:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"http://ip-api.com/json/{server_ip}?fields=country,countryCode,org")
                if r.status_code == 200:
                    data = r.json()
                    geo_country = data.get("countryCode")
                    geo_country_full = data.get("country")
                    geo_org = data.get("org")
        except Exception:
            pass

    evidence = []
    if server_ip:
        evidence.append(f"IP-адрес сервера: {server_ip}")
    if geo_country_full:
        evidence.append(f"Страна расположения: {geo_country_full} ({geo_country})")
    if geo_org:
        evidence.append(f"Хостинг-провайдер: {geo_org}")

    if geo_country == "RU":
        return {
            "code": "server_location", "title": "152-ФЗ — Локализация серверов (ст. 18.5)",
            "status": "passed",
            "details": f"Сервер расположен в России ({geo_country_full})",
            "evidence": evidence,
        }, []

    if server_ip and geo_country:
        return {
            "code": "server_location", "title": "152-ФЗ — Локализация серверов (ст. 18.5)",
            "status": "warning",
            "details": f"Сервер находится за пределами РФ (страна: {geo_country_full}). Это нарушение ст. 18.5 ФЗ-152",
            "evidence": evidence,
        }, [{
            "code": "server_not_in_russia", "title": "Сервер расположен за пределами РФ",
            "severity": "high", "category": "personal_data",
            "description": (
                f"IP-адрес сервера ({server_ip}) находится в стране {geo_country_full}. "
                "Согласно ст. 18.5 ФЗ-152, запись, систематизация, накопление, хранение, уточнение и извлечение "
                "персональных данных граждан РФ должны осуществляться с использованием баз данных, "
                "находящихся на территории Российской Федерации."
            ),
            "recommendation": (
                "Перенесите серверы и базу данных с персональными данными в Россию. "
                "Используйте российских хостинг-провайдеров (Selectel, Timeweb, REG.RU, Beget, Yandex Cloud, VK Cloud)."
            ),
            "evidence": evidence, "possible_fine": 6000000,
        }]

    return {
        "code": "server_location", "title": "152-ФЗ — Локализация серверов (ст. 18.5)",
        "status": "warning",
        "details": "Не удалось определить местоположение сервера. Требуется ручная проверка",
        "evidence": evidence,
    }, [{
        "code": "server_location_unknown", "title": "Не удалось определить страну сервера",
        "severity": "medium", "category": "personal_data",
        "description": (
            "Не удалось автоматически определить страну, в которой расположен сервер сайта. "
            "Согласно ст. 18.5 ФЗ-152, базы данных с ПДн граждан РФ должны находиться в России. "
            "Требуется ручная проверка."
        ),
        "recommendation": "Проверьте местоположение сервера через whois IP. Убедитесь, что хостинг находится в РФ.",
        "evidence": evidence, "possible_fine": None,
    }]


# ============================================================================
# 5. 152-ФЗ — Уведомление РКН (ст. 22)
# ============================================================================

RKN_KW = [
    "роскомнадзор", "rkn", "rkn.gov", "pd.rkn.gov",
    "реестр операторов", "реестр оператор", "оператор персональных данных",
    "оператор по обработке персональных данных", "уведомление об обработке",
    "уведомили роскомнадзор", "регистрационный номер оператора",
    "номер в реестре",
]


def check_rkn_notification(pages_html: dict) -> Tuple[dict, list]:
    all_text = _all_text(pages_html)
    found = [kw for kw in RKN_KW if kw in all_text]

    if found:
        return {
            "code": "rkn_notification", "title": "152-ФЗ — Уведомление Роскомнадзора (ст. 22)",
            "status": "passed",
            "details": "На сайте найдено упоминание о регистрации в реестре операторов ПДн",
            "evidence": [f"Найдено: {kw}" for kw in found[:3]],
        }, []

    return {
        "code": "rkn_notification", "title": "152-ФЗ — Уведомление Роскомнадзора (ст. 22)",
        "status": "warning",
        "details": "На сайте не найдено упоминание о регистрации оператора ПДн в реестре Роскомнадзора",
        "evidence": [],
    }, [{
        "code": "no_rkn_notification",
        "title": "Нет упоминания об уведомлении Роскомнадзора",
        "severity": "high", "category": "personal_data",
        "description": (
            "Согласно ст. 22 ФЗ-152, оператор персональных данных обязан уведомить Роскомнадзор "
            "о намерении осуществлять обработку ПДн до начала такой обработки. "
            "На сайте не найдено упоминаний о подаче такого уведомления."
        ),
        "recommendation": (
            "Подайте уведомление через pd.rkn.gov.ru, получите регистрационный номер в реестре "
            "операторов и укажите его в политике обработки персональных данных."
        ),
        "evidence": [], "possible_fine": 300000,
    }]


# ============================================================================
# 6. Cookie-баннер
# ============================================================================

COOKIE_KW = ["cookie", "cookies", "куки", "файлы cookie", "файлами cookie"]
COOKIE_ACCEPT_KW = [
    "принять", "принимаю", "согласен", "хорошо", "понятно", "ок ",
    "accept", "agree", "ok ", "got it", "understood",
]
COOKIE_REJECT_KW = [
    "отклонить", "отказаться", "отказ", "настройки", "настроить",
    "reject", "decline", "settings", "customize", "preferences",
]


def check_cookie_banner(pages_html: dict) -> Tuple[dict, list]:
    for url, html in pages_html.items():
        text_lower = html.lower()
        if not any(kw in text_lower for kw in COOKIE_KW):
            continue
        has_accept = any(kw in text_lower for kw in COOKIE_ACCEPT_KW)
        has_reject = any(kw in text_lower for kw in COOKIE_REJECT_KW)

        if has_accept and has_reject:
            return {
                "code": "cookie_banner", "title": "Cookie-баннер",
                "status": "passed",
                "details": "Баннер с кнопками принять/отклонить найден",
                "evidence": [url],
            }, []

        if has_accept:
            return {
                "code": "cookie_banner", "title": "Cookie-баннер",
                "status": "warning",
                "details": "Баннер найден, но кнопки отказа нет",
                "evidence": [url],
            }, [{
                "code": "cookie_no_reject", "title": "В cookie-баннере нет кнопки отказа",
                "severity": "low", "category": "cookies",
                "description": (
                    "Cookie-баннер найден, но в нём нет явной кнопки «Отклонить» или «Настроить». "
                    "Принцип GDPR/ФЗ-152: согласие должно быть свободно отзываемым, а отказ — таким же простым, как и принятие."
                ),
                "recommendation": "Добавьте в баннер кнопку «Отклонить» или «Настроить» рядом с кнопкой «Принять».",
                "evidence": [url], "possible_fine": None,
            }]

        return {
            "code": "cookie_banner", "title": "Cookie-баннер",
            "status": "warning",
            "details": "Упоминание cookie на странице найдено, но баннера с кнопками нет",
            "evidence": [url],
        }, [{
            "code": "cookie_no_banner", "title": "Нет интерактивного cookie-баннера",
            "severity": "low", "category": "cookies",
            "description": "На странице есть упоминание cookie, но интерактивный баннер с кнопкой принятия не найден.",
            "recommendation": "Добавьте всплывающий cookie-баннер с кнопками «Принять» и «Отклонить».",
            "evidence": [url], "possible_fine": None,
        }]

    return {
        "code": "cookie_banner", "title": "Cookie-баннер",
        "status": "warning",
        "details": "Cookie-баннер не найден",
        "evidence": [],
    }, [{
        "code": "missing_cookie_banner", "title": "Отсутствует cookie-баннер",
        "severity": "medium", "category": "cookies",
        "description": (
            "На сайте не найден баннер уведомления об использовании cookie. "
            "Согласно практике РКН, посетитель должен быть проинформирован об использовании cookie "
            "и иметь возможность отказаться от необязательных."
        ),
        "recommendation": "Добавьте cookie-баннер с информацией об использовании cookie и кнопками «Принять» / «Отклонить».",
        "evidence": [], "possible_fine": 60000,
    }]


# ============================================================================
# 7. 38-ФЗ — Маркировка рекламы (ERID)
# ============================================================================

ERID_PATTERN = re.compile(r"erid\s*[:=]?\s*[a-zA-Z0-9]{8,}", re.IGNORECASE)
AD_LABEL_PATTERN = re.compile(r"\bреклама\b|\bна правах рекламы\b|\badvertisement\b", re.IGNORECASE)


def check_advertising_marking(pages_html: dict) -> Tuple[dict, list]:
    has_ads = False
    has_erid = False
    evidence = []

    for url, html in pages_html.items():
        if AD_LABEL_PATTERN.search(html):
            has_ads = True
            evidence.append(f"Метка «Реклама» найдена на {url}")
        if ERID_PATTERN.search(html):
            has_erid = True
            evidence.append(f"Токен ERID найден на {url}")

    if not has_ads:
        return {
            "code": "advertising_marking", "title": "38-ФЗ — Маркировка рекламы (ERID)",
            "status": "passed",
            "details": "Рекламные блоки на сайте не обнаружены",
            "evidence": [],
        }, []

    if has_erid:
        return {
            "code": "advertising_marking", "title": "38-ФЗ — Маркировка рекламы (ERID)",
            "status": "passed",
            "details": "На сайте есть реклама и она промаркирована ERID-токеном",
            "evidence": evidence,
        }, []

    return {
        "code": "advertising_marking", "title": "38-ФЗ — Маркировка рекламы (ERID)",
        "status": "failed",
        "details": "На сайте есть реклама, но ERID-токен не найден",
        "evidence": evidence,
    }, [{
        "code": "missing_erid", "title": "Реклама без ERID-токена",
        "severity": "high", "category": "ads",
        "description": (
            "На сайте обнаружены метки «Реклама», но ERID-токен не найден. "
            "Согласно ст. 18.1 ФЗ «О рекламе» (38-ФЗ), вся интернет-реклама с 1 сентября 2022 года должна "
            "содержать ERID-токен и сведения о рекламодателе."
        ),
        "recommendation": (
            "Зарегистрируйтесь в одном из ОРД (Яндекс, VK, ОРД-А, МедиаСкаут, Сбер ОРД, Первый ОРД), "
            "получите ERID-токены для каждого рекламного материала и добавьте их в разметку."
        ),
        "evidence": evidence, "possible_fine": 500000,
    }]


# ============================================================================
# 8. 149-ФЗ — Реквизиты компании
# ============================================================================

INN_PATTERN = re.compile(r"\bИНН\s*:?\s*\d{10,12}\b", re.IGNORECASE)
OGRN_PATTERN = re.compile(r"\bОГРН(ИП)?\s*:?\s*\d{13,15}\b", re.IGNORECASE)
KPP_PATTERN = re.compile(r"\bКПП\s*:?\s*\d{9}\b", re.IGNORECASE)
ADDRESS_PATTERN = re.compile(
    r"(юридическ[а-я]+ адрес|фактическ[а-я]+ адрес|почтов[а-я]+ адрес|"
    r"место нахождения|г\.\s*[А-ЯЁ][а-яё]+|ул\.\s*[А-ЯЁ])",
    re.IGNORECASE,
)
DIRECTOR_PATTERN = re.compile(
    r"(генеральн[а-я]+ директор|директор|руководитель|управляющ[а-я]+|глава)\s*[:.]?\s*\S",
    re.IGNORECASE,
)
COMPANY_FORM_PATTERN = re.compile(
    r"\b(ООО|АО|ПАО|ОАО|ЗАО|ИП|самозанят)",
    re.IGNORECASE,
)


def check_company_requisites(pages_html: dict) -> Tuple[dict, list]:
    found = {
        "Форма организации (ООО/ИП/АО)": False,
        "ИНН": False,
        "ОГРН/ОГРНИП": False,
        "Юридический/фактический адрес": False,
        "Руководитель/директор": False,
    }
    evidence = []

    for html in pages_html.values():
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)

        if not found["Форма организации (ООО/ИП/АО)"] and COMPANY_FORM_PATTERN.search(text):
            found["Форма организации (ООО/ИП/АО)"] = True
            evidence.append("Найдена форма организации (ООО/ИП/АО)")
        if not found["ИНН"] and INN_PATTERN.search(text):
            found["ИНН"] = True
            evidence.append("ИНН найден")
        if not found["ОГРН/ОГРНИП"] and OGRN_PATTERN.search(text):
            found["ОГРН/ОГРНИП"] = True
            evidence.append("ОГРН/ОГРНИП найден")
        if not found["Юридический/фактический адрес"] and ADDRESS_PATTERN.search(text):
            found["Юридический/фактический адрес"] = True
            evidence.append("Адрес организации найден")
        if not found["Руководитель/директор"] and DIRECTOR_PATTERN.search(text):
            found["Руководитель/директор"] = True
            evidence.append("Руководитель указан")

    score = sum(found.values())
    total = len(found)
    missing = [k for k, v in found.items() if not v]

    if score >= 4:
        return {
            "code": "company_requisites", "title": "149-ФЗ — Реквизиты компании",
            "status": "passed",
            "details": f"Указаны основные реквизиты ({score}/{total})" + (f". Не хватает: {', '.join(missing)}" if missing else ""),
            "evidence": evidence,
        }, []

    if score >= 2:
        return {
            "code": "company_requisites", "title": "149-ФЗ — Реквизиты компании",
            "status": "warning",
            "details": f"Реквизиты указаны частично ({score}/{total}). Не хватает: {', '.join(missing)}",
            "evidence": evidence,
        }, [{
            "code": "incomplete_requisites", "title": "Реквизиты компании указаны не полностью",
            "severity": "medium", "category": "company_info",
            "description": (
                f"На сайте указано только {score} из {total} обязательных реквизитов. "
                f"Не хватает: {', '.join(missing)}. Согласно ч. 2 ст. 10 ФЗ-149 владелец сайта обязан "
                "разместить достоверную информацию о себе."
            ),
            "recommendation": "Добавьте на страницу «Контакты» или в футер: ИНН, ОГРН, юридический адрес, ФИО руководителя.",
            "evidence": evidence, "possible_fine": 50000,
        }]

    if score >= 1:
        return {
            "code": "company_requisites", "title": "149-ФЗ — Реквизиты компании",
            "status": "warning",
            "details": f"Реквизиты практически отсутствуют ({score}/{total}). Не хватает: {', '.join(missing)}",
            "evidence": evidence,
        }, [{
            "code": "minimal_requisites", "title": "Минимум информации о компании",
            "severity": "high", "category": "company_info",
            "description": (
                f"Найдено только {score} из {total} обязательных реквизитов. "
                f"Не хватает: {', '.join(missing)}. Это нарушение ч. 2 ст. 10 ФЗ-149."
            ),
            "recommendation": "Создайте отдельную страницу «Реквизиты» с полной информацией о юридическом лице или ИП.",
            "evidence": evidence, "possible_fine": 100000,
        }]

    return {
        "code": "company_requisites", "title": "149-ФЗ — Реквизиты компании",
        "status": "failed",
        "details": "Реквизиты компании на сайте не найдены",
        "evidence": [],
    }, [{
        "code": "missing_requisites", "title": "Отсутствуют реквизиты компании",
        "severity": "high", "category": "company_info",
        "description": (
            "На сайте не найдена информация о владельце: ни ИНН, ни ОГРН, ни юридический адрес, "
            "ни данные руководителя. Это нарушение ч. 2 ст. 10 ФЗ-149 «Об информации»."
        ),
        "recommendation": "Создайте страницу «Реквизиты» и добавьте ссылку в футер.",
        "evidence": [], "possible_fine": 100000,
    }]


# ============================================================================
# 9. ЗоЗПП — Документы для потребителей
# ============================================================================

CONSUMER_DOCS = {
    "Оферта/договор": ["оферта", "публичная оферта", "договор", "договор-оферта"],
    "Возврат/обмен": ["возврат", "обмен товара", "возврата", "вернуть товар"],
    "Доставка": ["доставка", "способы доставки", "условия доставки"],
    "Оплата": ["оплата", "способы оплаты", "способ оплаты"],
    "Гарантия": ["гарантия", "гарантийн", "срок гарантии"],
}


def check_consumer_rights(pages_html: dict, links: List[str]) -> Tuple[dict, list]:
    all_text = _all_text(pages_html)
    for link in links:
        all_text += " " + link.lower()

    found = {}
    evidence = []
    for doc, keywords in CONSUMER_DOCS.items():
        is_found = any(kw in all_text for kw in keywords)
        found[doc] = is_found
        if is_found:
            evidence.append(f"Найдено: {doc}")

    found_count = sum(found.values())
    total = len(CONSUMER_DOCS)
    missing = [k for k, v in found.items() if not v]

    if found_count >= 4:
        return {
            "code": "consumer_rights", "title": "ЗоЗПП — Документы для потребителей",
            "status": "passed",
            "details": f"Документы для потребителей найдены ({found_count}/{total})" + (f". Не хватает: {', '.join(missing)}" if missing else ""),
            "evidence": evidence,
        }, []

    if found_count >= 2:
        return {
            "code": "consumer_rights", "title": "ЗоЗПП — Документы для потребителей",
            "status": "warning",
            "details": f"Часть документов отсутствует ({found_count}/{total}). Не хватает: {', '.join(missing)}",
            "evidence": evidence,
        }, [{
            "code": "missing_consumer_docs",
            "title": f"Не хватает документов: {', '.join(missing)}",
            "severity": "medium", "category": "consumer_rights",
            "description": (
                f"На сайте найдено только {found_count} из {total} обязательных для интернет-магазинов документов. "
                f"Не хватает: {', '.join(missing)}. Это нарушение Закона «О защите прав потребителей»."
            ),
            "recommendation": f"Добавьте отдельные страницы: {', '.join(missing)}.",
            "evidence": evidence, "possible_fine": 50000,
        }]

    return {
        "code": "consumer_rights", "title": "ЗоЗПП — Документы для потребителей",
        "status": "failed",
        "details": f"Большинство потребительских документов отсутствует ({found_count}/{total}). Не хватает: {', '.join(missing)}",
        "evidence": evidence,
    }, [{
        "code": "missing_consumer_docs_critical",
        "title": "Критическое отсутствие документов для потребителей",
        "severity": "high", "category": "consumer_rights",
        "description": (
            f"На сайте найдено только {found_count} из {total} обязательных документов: {', '.join(missing)} отсутствуют. "
            "Для интернет-магазина это серьёзное нарушение ЗоЗПП."
        ),
        "recommendation": "Срочно разработайте и разместите все обязательные документы (оферта, возврат, доставка, оплата, гарантия).",
        "evidence": evidence, "possible_fine": 100000,
    }]


# ============================================================================
# 10. 436-ФЗ — Возрастная маркировка
# ============================================================================

AGE_MARK_PATTERN = re.compile(r"\b(?:0\+|6\+|12\+|16\+|18\+)\b")
ADULT_KW = [
    "казино", "ставк", "букмекер", "алкогол", "табак", "вейп", "сигарет",
    "эротик", "порно", "18+", "взрослый контент", "только для взрослых",
]


def check_age_marking(pages_html: dict) -> Tuple[dict, list]:
    all_text = _all_text(pages_html)
    all_html = _all_html(pages_html)

    has_adult = any(kw in all_text for kw in ADULT_KW)
    age_marks = set(AGE_MARK_PATTERN.findall(all_html))

    if age_marks:
        marks_str = ", ".join(sorted(age_marks))
        if has_adult and "18+" not in age_marks:
            return {
                "code": "age_marking", "title": "436-ФЗ — Возрастная маркировка",
                "status": "warning",
                "details": f"Маркировка ({marks_str}) есть, но при контенте 18+ ожидается метка 18+",
                "evidence": [f"Найденные метки: {marks_str}"],
            }, [{
                "code": "wrong_age_marking", "title": "Возрастная маркировка не соответствует контенту",
                "severity": "medium", "category": "age_marking",
                "description": "Найден контент категории 18+ (алкоголь/ставки/казино/прочее), но метка 18+ на сайте не выставлена.",
                "recommendation": "Добавьте маркировку 18+ в шапку или футер сайта.",
                "evidence": [f"Найденные метки: {marks_str}"], "possible_fine": 50000,
            }]
        return {
            "code": "age_marking", "title": "436-ФЗ — Возрастная маркировка",
            "status": "passed",
            "details": f"Возрастная маркировка указана: {marks_str}",
            "evidence": [f"Найденные метки: {marks_str}"],
        }, []

    if has_adult:
        return {
            "code": "age_marking", "title": "436-ФЗ — Возрастная маркировка",
            "status": "failed",
            "details": "На сайте есть контент 18+, но возрастная маркировка отсутствует",
            "evidence": [],
        }, [{
            "code": "missing_age_marking_adult", "title": "Контент 18+ без возрастной маркировки",
            "severity": "high", "category": "age_marking",
            "description": (
                "Найден контент категории 18+ (алкоголь, ставки, табак, казино или подобное), "
                "при этом метка возрастной категории на сайте не выставлена. Нарушение 436-ФЗ."
            ),
            "recommendation": "Добавьте маркировку 18+ в шапку или футер сайта.",
            "evidence": [], "possible_fine": 50000,
        }]

    return {
        "code": "age_marking", "title": "436-ФЗ — Возрастная маркировка",
        "status": "warning",
        "details": "Возрастная маркировка не найдена. По 436-ФЗ рекомендуется указывать категорию (0+, 6+, 12+, 16+ или 18+)",
        "evidence": [],
    }, [{
        "code": "missing_age_marking", "title": "Не указана возрастная маркировка",
        "severity": "low", "category": "age_marking",
        "description": (
            "На сайте не найдена маркировка возрастной категории (0+, 6+, 12+, 16+ или 18+). "
            "Согласно 436-ФЗ «О защите детей от информации, причиняющей вред их здоровью», маркировка рекомендуется для всех общедоступных сайтов."
        ),
        "recommendation": "Добавьте знак возрастной категории (например, 6+ или 16+) в футер сайта.",
        "evidence": [], "possible_fine": 50000,
    }]


# ============================================================================
# 11. Контактная информация (доступность для пользователей)
# ============================================================================

PHONE_PATTERN = re.compile(r"(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}")
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
SCHEDULE_PATTERN = re.compile(
    r"(режим работы|время работы|график|часы работы|пн[\-–]пт|круглосуточно|ежедневно)",
    re.IGNORECASE,
)
MAP_PATTERN = re.compile(r"(yandex\.ru/maps|google\.com/maps|2gis|maps\.api)", re.IGNORECASE)


def check_contacts(pages_html: dict) -> Tuple[dict, list]:
    found = {
        "Телефон": False,
        "Email": False,
        "Режим работы": False,
        "Карта": False,
    }
    evidence = []

    for html in pages_html.values():
        if not found["Телефон"] and PHONE_PATTERN.search(html):
            found["Телефон"] = True
            evidence.append("Телефон найден")
        if not found["Email"] and EMAIL_PATTERN.search(html):
            found["Email"] = True
            evidence.append("Email найден")
        if not found["Режим работы"] and SCHEDULE_PATTERN.search(html):
            found["Режим работы"] = True
            evidence.append("Режим работы указан")
        if not found["Карта"] and MAP_PATTERN.search(html):
            found["Карта"] = True
            evidence.append("Карта (Яндекс/Google/2ГИС) найдена")

    score = sum(found.values())
    total = len(found)
    missing = [k for k, v in found.items() if not v]

    if score >= 3:
        return {
            "code": "contacts", "title": "Контактная информация",
            "status": "passed",
            "details": f"Контактные данные указаны ({score}/{total})" + (f". Не хватает: {', '.join(missing)}" if missing else ""),
            "evidence": evidence,
        }, []

    if score >= 1:
        return {
            "code": "contacts", "title": "Контактная информация",
            "status": "warning",
            "details": f"Контакты указаны частично ({score}/{total}). Не хватает: {', '.join(missing)}",
            "evidence": evidence,
        }, [{
            "code": "incomplete_contacts", "title": "Контактные данные указаны не полностью",
            "severity": "medium", "category": "contacts",
            "description": f"На сайте не найдено: {', '.join(missing)}. Это снижает доверие пользователей и затрудняет связь.",
            "recommendation": "Создайте страницу «Контакты» с телефоном, email, адресом, режимом работы и картой проезда.",
            "evidence": evidence, "possible_fine": 30000,
        }]

    return {
        "code": "contacts", "title": "Контактная информация",
        "status": "failed",
        "details": "Контактная информация на сайте не найдена",
        "evidence": [],
    }, [{
        "code": "missing_contacts", "title": "Нет контактной информации",
        "severity": "high", "category": "contacts",
        "description": "На сайте не найдены ни телефон, ни email, ни адрес. Серьёзное нарушение требований к информации для потребителей.",
        "recommendation": "Добавьте страницу «Контакты» с телефоном, email и адресом.",
        "evidence": [], "possible_fine": 50000,
    }]


# ============================================================================
# 12. Безопасность платежей
# ============================================================================

PAYMENT_KW = [
    "оплата картой", "оплатить", "корзина", "checkout", "касса",
    "mastercard", "visa", "мир ", "юmoney", "юкасса", "yookassa",
    "robokassa", "робокасса", "tinkoff", "сбербанк", "stripe", "paypal",
]
PAYMENT_SECURITY_KW = [
    "безопасн", "ssl", "pci dss", "3-d secure", "3d secure",
    "защищён", "шифрование", "https",
]


def check_payment_security(pages_html: dict) -> Tuple[dict, list]:
    all_text = _all_text(pages_html)
    has_payment = any(kw in all_text for kw in PAYMENT_KW)
    has_security = any(kw in all_text for kw in PAYMENT_SECURITY_KW)

    if not has_payment:
        return {
            "code": "payment_security", "title": "Безопасность платежей",
            "status": "passed",
            "details": "Формы приёма платежей не обнаружены",
            "evidence": [],
        }, []

    if has_security:
        return {
            "code": "payment_security", "title": "Безопасность платежей",
            "status": "passed",
            "details": "На сайте принимаются платежи и есть информация об их безопасности",
            "evidence": ["Найдено упоминание SSL/PCI DSS/3-D Secure/шифрования"],
        }, []

    return {
        "code": "payment_security", "title": "Безопасность платежей",
        "status": "warning",
        "details": "На сайте принимаются платежи, но информации об их безопасности не найдено",
        "evidence": [],
    }, [{
        "code": "no_payment_security_info", "title": "Нет информации о безопасности платежей",
        "severity": "medium", "category": "payment_security",
        "description": "Сайт принимает платежи, но не указано, как обеспечивается их безопасность (SSL, PCI DSS, 3-D Secure).",
        "recommendation": "На странице оплаты или в FAQ укажите: используется SSL, поддержка 3-D Secure, соответствие PCI DSS платёжной системы.",
        "evidence": [], "possible_fine": None,
    }]


# ============================================================================
# 13. Технические проверки (title, meta, viewport, h1, OG, alt, robots, sitemap)
# ============================================================================

def check_technical(main_html: str, final_url: str, robots_ok: bool, sitemap_ok: bool) -> Tuple[List[dict], list]:
    checks = []
    issues = []
    soup = BeautifulSoup(main_html, "lxml")

    # title
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    title_len = len(title_text)
    if title_len == 0:
        checks.append({"code": "meta_title", "title": "Тег <title>", "status": "failed",
                       "details": "Тег <title> отсутствует", "evidence": []})
        issues.append({"code": "missing_title", "title": "Не задан тег <title>",
                       "severity": "medium", "category": "technical",
                       "description": "Тег <title> отсутствует. Это критично для SEO и отображения в браузере.",
                       "recommendation": "Добавьте тег <title> с описанием содержимого страницы (30–60 символов).",
                       "evidence": [], "possible_fine": None})
    elif 10 <= title_len <= 120:
        checks.append({"code": "meta_title", "title": "Тег <title>", "status": "passed",
                       "details": f"Заголовок: «{title_text[:80]}» ({title_len} символов)", "evidence": []})
    else:
        checks.append({"code": "meta_title", "title": "Тег <title>", "status": "warning",
                       "details": f"Заголовок длиной {title_len} символов (рекомендуется 30–60)", "evidence": []})
        issues.append({"code": "bad_title_length", "title": "Длина <title> вне рекомендованного диапазона",
                       "severity": "low", "category": "technical",
                       "description": f"Длина <title>: {title_len} символов. Оптимум — 30–60.",
                       "recommendation": "Сократите/расширьте <title> до 30–60 символов.",
                       "evidence": [], "possible_fine": None})

    # meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    desc_content = (meta_desc.get("content", "").strip()) if meta_desc else ""
    desc_len = len(desc_content)
    if desc_len == 0:
        checks.append({"code": "meta_description", "title": "Meta description", "status": "warning",
                       "details": "Meta description не задан", "evidence": []})
    elif 50 <= desc_len <= 300:
        checks.append({"code": "meta_description", "title": "Meta description", "status": "passed",
                       "details": f"Описание: {desc_len} символов", "evidence": []})
    else:
        checks.append({"code": "meta_description", "title": "Meta description", "status": "warning",
                       "details": f"Описание длиной {desc_len} символов (рекомендуется 50–160)", "evidence": []})

    # viewport
    viewport = soup.find("meta", attrs={"name": "viewport"})
    has_viewport = bool(viewport and viewport.get("content", ""))
    checks.append({"code": "viewport", "title": "Mobile viewport",
                   "status": "passed" if has_viewport else "warning",
                   "details": "Тег viewport задан — сайт адаптирован под мобильные" if has_viewport
                       else "Тег viewport не задан — возможны проблемы на мобильных",
                   "evidence": []})

    # favicon
    favicon = soup.find("link", rel=lambda r: r and "icon" in r) or \
              soup.find("link", href=lambda h: h and "favicon" in h)
    checks.append({"code": "favicon", "title": "Favicon",
                   "status": "passed" if favicon else "warning",
                   "details": "Favicon найден" if favicon else "Favicon не найден",
                   "evidence": []})

    # charset
    charset = soup.find("meta", attrs={"charset": True}) or \
              soup.find("meta", attrs={"http-equiv": lambda v: v and "content-type" in v.lower()})
    checks.append({"code": "charset", "title": "Кодировка",
                   "status": "passed" if charset else "warning",
                   "details": "Кодировка указана" if charset else "Кодировка не указана",
                   "evidence": []})

    # h1
    h1_tags = soup.find_all("h1")
    if len(h1_tags) == 1:
        checks.append({"code": "h1", "title": "Заголовок <h1>", "status": "passed",
                       "details": f"H1: «{h1_tags[0].get_text(strip=True)[:80]}»", "evidence": []})
    elif len(h1_tags) > 1:
        checks.append({"code": "h1", "title": "Заголовок <h1>", "status": "warning",
                       "details": f"Найдено {len(h1_tags)} тегов <h1> — должен быть один",
                       "evidence": []})
    else:
        checks.append({"code": "h1", "title": "Заголовок <h1>", "status": "warning",
                       "details": "Тег <h1> отсутствует", "evidence": []})

    # Open Graph
    og_title = soup.find("meta", property="og:title")
    og_desc = soup.find("meta", property="og:description")
    og_image = soup.find("meta", property="og:image")
    og_count = sum(1 for t in [og_title, og_desc, og_image] if t and t.get("content", "").strip())
    if og_count >= 2:
        checks.append({"code": "open_graph", "title": "Open Graph", "status": "passed",
                       "details": f"OG-теги заданы ({og_count}/3)", "evidence": []})
    elif og_count > 0:
        checks.append({"code": "open_graph", "title": "Open Graph", "status": "warning",
                       "details": f"OG-теги заданы частично ({og_count}/3)", "evidence": []})
    else:
        checks.append({"code": "open_graph", "title": "Open Graph", "status": "warning",
                       "details": "OG-теги не заданы — нет красивого превью при шеринге", "evidence": []})

    # alt у картинок
    images = soup.find_all("img")
    images_with_alt = sum(1 for img in images if img.get("alt"))
    if not images:
        checks.append({"code": "img_alt", "title": "Alt у изображений", "status": "passed",
                       "details": "Изображений на странице нет", "evidence": []})
    else:
        ratio = images_with_alt / len(images)
        if ratio >= 0.7:
            checks.append({"code": "img_alt", "title": "Alt у изображений", "status": "passed",
                           "details": f"Alt задан у {images_with_alt} из {len(images)} изображений",
                           "evidence": []})
        else:
            checks.append({"code": "img_alt", "title": "Alt у изображений", "status": "warning",
                           "details": f"Alt задан только у {images_with_alt} из {len(images)} изображений",
                           "evidence": []})

    # robots.txt
    checks.append({"code": "robots_txt", "title": "robots.txt",
                   "status": "passed" if robots_ok else "warning",
                   "details": "Файл robots.txt доступен" if robots_ok else "Файл robots.txt недоступен или пуст",
                   "evidence": []})

    # sitemap.xml
    checks.append({"code": "sitemap_xml", "title": "sitemap.xml",
                   "status": "passed" if sitemap_ok else "warning",
                   "details": "Файл sitemap.xml доступен" if sitemap_ok else "Файл sitemap.xml не найден",
                   "evidence": []})

    return checks, issues


# ============================================================================
# robots.txt + sitemap.xml
# ============================================================================

async def check_robots_sitemap(base_url: str, timeout: int = TIMEOUT) -> Tuple[bool, bool]:
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    robots_ok = False
    sitemap_ok = False

    try:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=timeout, verify=False) as client:
            try:
                r = await client.get(f"{base}/robots.txt")
                robots_ok = r.status_code == 200 and len(r.text) > 10
            except Exception:
                pass
            try:
                r = await client.get(f"{base}/sitemap.xml")
                sitemap_ok = r.status_code == 200
            except Exception:
                pass
    except Exception:
        pass

    return robots_ok, sitemap_ok


# ============================================================================
# Скоринг
# ============================================================================

def calculate_score(issues: list) -> Tuple[int, str]:
    score = 100
    for issue in issues:
        severity = issue.get("severity", "low")
        if severity == "high":
            score -= 25
        elif severity == "medium":
            score -= 12
        elif severity == "low":
            score -= 5

    score = max(0, score)

    if score >= 80:
        risk = "green"
    elif score >= 50:
        risk = "yellow"
    else:
        risk = "red"

    return score, risk
