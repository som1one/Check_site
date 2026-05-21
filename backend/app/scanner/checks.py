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


# -- Crawler --

async def fetch_page(url: str, timeout: int = TIMEOUT) -> Tuple[Optional[str], Optional[str]]:
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
                soup = BeautifulSoup(r.text, "lxml-xml") or BeautifulSoup(r.text, "html.parser")
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
        if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
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


# -- Helpers --

def _all_text(pages_html: dict) -> str:
    combined = ""
    for html in pages_html.values():
        soup = BeautifulSoup(html, "lxml")
        combined += " " + soup.get_text(" ", strip=True)
    return combined.lower()


def _all_html(pages_html: dict) -> str:
    return " ".join(pages_html.values()).lower()
# -- 1. HTTPS --

async def check_https_detailed(final_url: str, timeout: int = TIMEOUT) -> Tuple[dict, list]:
    is_https = final_url.startswith("https://")
    hsts = False
    evidence = [final_url]

    if is_https:
        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=timeout, verify=False) as client:
                resp = await client.get(final_url)
                hsts = "strict-transport-security" in {k.lower() for k in resp.headers.keys()}
                if hsts:
                    evidence.append("HSTS header present")
        except Exception:
            pass

        http_url = final_url.replace("https://", "http://", 1)
        try:
            async with httpx.AsyncClient(headers=HEADERS, timeout=timeout, follow_redirects=True, verify=False) as client:
                r = await client.get(http_url)
                if r.url.startswith("https://"):
                    evidence.append("HTTP->HTTPS redirect works")
        except Exception:
            pass

    if is_https and hsts:
        return {"code": "https", "title": "HTTPS", "status": "passed",
                "details": "HTTPS + HSTS", "evidence": evidence}, []

    if is_https:
        return {"code": "https", "title": "HTTPS", "status": "warning",
                "details": "HTTPS OK, no HSTS", "evidence": evidence}, [{
            "code": "no_hsts", "title": "No HSTS", "severity": "low", "category": "technical",
            "description": "Strict-Transport-Security missing.",
            "recommendation": "Add HSTS header.", "evidence": evidence, "possible_fine": None}]

    return {"code": "https", "title": "HTTPS", "status": "failed",
            "details": "No HTTPS", "evidence": evidence}, [{
        "code": "no_https", "title": "No HTTPS", "severity": "high", "category": "technical",
        "description": "Data transmitted in plain text.",
        "recommendation": "Install SSL certificate.", "evidence": evidence, "possible_fine": None}]


# -- 2. Privacy Policy --

def check_privacy_policy(pages_html: dict, links: List[str]) -> Tuple[dict, list]:
    all_text = _all_text(pages_html)
    required_sections = {
        "purposes": ["goals of processing", "purpose of processing", "for what", "purposes of collection"],
        "data_list": ["list", "data categories", "we collect", "what data"],
        "retention": ["retention period", "storage period", "stored", "destruction"],
        "rights": ["subject rights", "user rights", "you have the right", "revoke", "withdrawal of consent"],
        "protection": ["protection measures", "security", "data protection", "encryption"],
        "third_parties": ["third parties", "to third parties", "data transfer", "disclosure"],
    }
    found_sections = {k: any(kw in all_text for kw in v) for k, v in required_sections.items()}

    policy_url = None
    policy_kw = ["policy", "privacy", "personal data", "data processing"]
    for url in pages_html:
        if any(kw in url.lower() for kw in policy_kw):
            policy_url = url; break
    if not policy_url:
        for link in links:
            if any(kw in link.lower() for kw in policy_kw):
                policy_url = link; break

    sections_found = sum(found_sections.values())
    total = len(required_sections)
    evidence = ([policy_url] if policy_url else []) + [
        f"Section '{k}': {'found' if v else 'missing'}" for k, v in found_sections.items()]

    if sections_found >= 5 and policy_url:
        return {"code": "privacy_policy", "title": "Privacy Policy",
                "status": "passed", "details": f"Found ({sections_found}/{total} sections)",
                "evidence": evidence}, []

    if sections_found >= 3 and policy_url:
        return {"code": "privacy_policy", "title": "Privacy Policy",
                "status": "warning", "details": f"Incomplete ({sections_found}/{total})",
                "evidence": evidence}, [{
            "code": "incomplete_privacy_policy", "title": "Incomplete privacy policy",
            "severity": "medium", "category": "personal_data",
            "description": f"Only {sections_found}/{total} sections found.",
            "recommendation": "Complete the policy per 152-FZ.",
            "evidence": evidence, "possible_fine": 150000}]

    if policy_url:
        return {"code": "privacy_policy", "title": "Privacy Policy",
                "status": "warning", "details": "Minimal content", "evidence": evidence}, [{
            "code": "minimal_privacy_policy", "title": "Minimal privacy policy",
            "severity": "high", "category": "personal_data",
            "description": "Key sections missing per 152-FZ.",
            "recommendation": "Develop a full privacy policy.",
            "evidence": evidence, "possible_fine": 300000}]

    return {"code": "privacy_policy", "title": "Privacy Policy",
            "status": "failed", "details": "Not found", "evidence": []}, [{
        "code": "missing_privacy_policy", "title": "Missing privacy policy",
        "severity": "high", "category": "personal_data",
        "description": "Violation of Art. 18.1 152-FZ.",
        "recommendation": "Publish a privacy policy.", "evidence": [], "possible_fine": 300000}]


# -- 3. User Agreement --

def check_user_agreement(pages_html: dict, links: List[str]) -> Tuple[dict, list]:
    all_text = _all_text(pages_html)
    keywords = ["user agreement", "terms of use", "terms of service", "terms and conditions"]

    found_url = None
    for url in pages_html:
        if any(kw in url.lower() for kw in ["agreement", "terms", "conditions"]):
            found_url = url; break
    if not found_url:
        for link in links:
            if any(kw in link.lower() for kw in ["agreement", "terms", "conditions"]):
                found_url = link; break

    if found_url:
        return {"code": "user_agreement", "title": "User Agreement",
                "status": "passed", "details": f"Found: {found_url}", "evidence": [found_url]}, []

    if any(kw in all_text for kw in keywords):
        return {"code": "user_agreement", "title": "User Agreement",
                "status": "warning", "details": "Mentioned, no dedicated page", "evidence": []}, [{
            "code": "no_user_agreement_page", "title": "No dedicated agreement page",
            "severity": "low", "category": "user_agreement",
            "description": "Harder to access.",
            "recommendation": "Create a dedicated page.", "evidence": [], "possible_fine": None}]

    return {"code": "user_agreement", "title": "User Agreement",
            "status": "warning", "details": "Not found", "evidence": []}, [{
        "code": "missing_user_agreement", "title": "Missing user agreement",
        "severity": "medium", "category": "user_agreement",
        "description": "Required for sites with registration/payments.",
        "recommendation": "Create and publish.", "evidence": [], "possible_fine": 50000}]


# -- 4. Form Consent --

def check_form_consent(pages_html: dict) -> Tuple[dict, list]:
    consent_kw = ["consent to processing", "agree to processing", "i consent",
                  "personal data", "privacy policy", "i agree", "accept terms"]
    personal_types = {"email", "tel", "phone", "number"}
    personal_names = ["email", "phone", "tel", "name", "fio", "firstname", "lastname", "username"]

    forms_found = 0
    consent_found = 0
    has_checkbox = False
    evidence = []

    for url, html in pages_html.items():
        soup = BeautifulSoup(html, "lxml")
        for form in soup.find_all("form"):
            inputs = form.find_all("input")
            has_personal = False
            for inp in inputs:
                itype = (inp.get("type") or "").lower()
                iname = (inp.get("name") or inp.get("id") or inp.get("placeholder") or "").lower()
                if itype in personal_types or any(n in iname for n in personal_names):
                    has_personal = True; break
            if not has_personal:
                continue

            forms_found += 1
            form_text = form.get_text(" ", strip=True).lower()

            for cb in form.find_all("input", type="checkbox"):
                cb_name = (cb.get("name") or "").lower()
                parent_text = (cb.parent.get_text(" ", strip=True).lower() if cb.parent else "")
                if any(kw in (cb_name + " " + parent_text) for kw in consent_kw):
                    has_checkbox = True; break

            parent_text = (form.parent.get_text(" ", strip=True).lower() if form.parent else "")
            combined = form_text + " " + parent_text
            if any(kw in combined for kw in consent_kw):
                consent_found += 1
                evidence.append(f"Form at {url}: consent found")
            else:
                evidence.append(f"Form at {url}: consent MISSING")

    if forms_found == 0:
        return {"code": "form_consent", "title": "Form Consent", "status": "passed",
                "details": "No personal data forms found", "evidence": []}, []

    if consent_found >= forms_found:
        extra = ", has checkbox" if has_checkbox else ""
        return {"code": "form_consent", "title": "Form Consent", "status": "passed",
                "details": f"All {forms_found} forms have consent{extra}", "evidence": evidence}, []

    missing = forms_found - consent_found
    return {"code": "form_consent", "title": "Form Consent",
            "status": "failed" if missing == forms_found else "warning",
            "details": f"{missing}/{forms_found} forms lack consent", "evidence": evidence}, [{
        "code": "missing_form_consent", "title": "Missing form consent",
        "severity": "high", "category": "personal_data",
        "description": f"{missing} forms lack consent. Violation of Art. 9 152-FZ.",
        "recommendation": "Add consent checkbox with link to privacy policy.",
        "evidence": evidence, "possible_fine": 150000}]


# -- 5. Cookie Banner --

def check_cookie_banner(pages_html: dict) -> Tuple[dict, list]:
    cookie_kw = ["cookie", "cookies"]
    accept_kw = ["accept", "agree", "ok", "got it", "understood"]
    reject_kw = ["reject", "decline", "settings", "customize", "preferences"]

    for url, html in pages_html.items():
        text_lower = html.lower()
        if not any(kw in text_lower for kw in cookie_kw):
            continue
        has_accept = any(kw in text_lower for kw in accept_kw)
        has_reject = any(kw in text_lower for kw in reject_kw)

        if has_accept and has_reject:
            return {"code": "cookie_banner", "title": "Cookie Banner", "status": "passed",
                    "details": "Banner with accept/reject", "evidence": [url]}, []
        if has_accept:
            return {"code": "cookie_banner", "title": "Cookie Banner", "status": "warning",
                    "details": "Banner without reject option", "evidence": [url]}, [{
                "code": "cookie_no_reject", "title": "No reject button",
                "severity": "low", "category": "cookies",
                "description": "Banner lacks explicit reject.",
                "recommendation": "Add reject button.", "evidence": [url], "possible_fine": None}]
        return {"code": "cookie_banner", "title": "Cookie Banner", "status": "warning",
                "details": "Cookie mention without banner", "evidence": [url]}, [{
            "code": "cookie_no_banner", "title": "No explicit banner",
            "severity": "low", "category": "cookies",
            "description": "Cookies mentioned without banner.",
            "recommendation": "Add cookie banner.", "evidence": [url], "possible_fine": None}]

    return {"code": "cookie_banner", "title": "Cookie Banner", "status": "warning",
            "details": "Not found", "evidence": []}, [{
        "code": "missing_cookie_banner", "title": "Missing cookie notice",
        "severity": "medium", "category": "cookies",
        "description": "Recommended to inform about cookies.",
        "recommendation": "Add cookie banner.", "evidence": [], "possible_fine": 60000}]


# -- 6. Advertising Marking --

def check_advertising_marking(pages_html: dict) -> Tuple[dict, list]:
    erid_pat = re.compile(r"erid\s*[:=]?\s*[a-zA-Z0-9]{8,}", re.IGNORECASE)
    ad_label_pat = re.compile(r"advertisement\b|ad\b", re.IGNORECASE)
    token_pat = re.compile(r"token\s*(ad)?\s*[:=]?\s*[a-zA-Z0-9]{8,}", re.IGNORECASE)

    has_ads = False; has_erid = False; evidence = []

    for url, html in pages_html.items():
        if ad_label_pat.search(html):
            has_ads = True; evidence.append(f"Ad label on {url}")
        if erid_pat.search(html) or token_pat.search(html):
            has_erid = True; evidence.append(f"ERID on {url}")

    if not has_ads:
        return {"code": "advertising_marking", "title": "Ad Marking (ERID)",
                "status": "passed", "details": "No ads detected", "evidence": []}, []

    if has_erid:
        return {"code": "advertising_marking", "title": "Ad Marking (ERID)",
                "status": "passed", "details": "ERID present", "evidence": evidence}, []

    return {"code": "advertising_marking", "title": "Ad Marking (ERID)",
            "status": "failed", "details": "Ads without ERID", "evidence": evidence}, [{
        "code": "missing_erid", "title": "Missing ERID marking",
        "severity": "high", "category": "ads",
        "description": "Ads detected without ERID token. Violation of 347-FZ.",
        "recommendation": "Register with ORD and get ERID tokens.",
        "evidence": evidence, "possible_fine": 500000}]


# -- 7. Company Requisites --

def check_company_requisites(pages_html: dict) -> Tuple[dict, list]:
    inn_pat = re.compile(r"\bINN\s*:?\s*\d{10,12}\b", re.IGNORECASE)
    ogrn_pat = re.compile(r"\b(OGRN|OGRNIP)\s*:?\s*\d{13,15}\b", re.IGNORECASE)
    kpp_pat = re.compile(r"\bKPP\s*:?\s*\d{9}\b", re.IGNORECASE)
    phone_pat = re.compile(r"(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}")
    email_pat = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    address_pat = re.compile(r"(legal|physical|postal)\s*address", re.IGNORECASE)
    director_pat = re.compile(r"(general\s*director|director|CEO|head)\s*[:.]?\s*\S", re.IGNORECASE)

    found = {"inn": False, "ogrn": False, "kpp": False, "phone": False,
             "email": False, "address": False, "director": False}
    evidence = []

    for url, html in pages_html.items():
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)

        if inn_pat.search(text) and not found["inn"]:
            found["inn"] = True; evidence.append("INN found")
        if ogrn_pat.search(text) and not found["ogrn"]:
            found["ogrn"] = True; evidence.append("OGRN found")
        if kpp_pat.search(text) and not found["kpp"]:
            found["kpp"] = True; evidence.append("KPP found")
        if phone_pat.search(text) and not found["phone"]:
            found["phone"] = True; evidence.append("Phone found")
        if email_pat.search(text) and not found["email"]:
            found["email"] = True; evidence.append("Email found")
        if address_pat.search(text) and not found["address"]:
            found["address"] = True; evidence.append("Address found")
        if director_pat.search(text) and not found["director"]:
            found["director"] = True; evidence.append("Director found")

    score = sum(found.values())

    if score >= 5:
        return {"code": "company_requisites", "title": "Company Requisites",
                "status": "passed", "details": f"Found ({score}/7)", "evidence": evidence}, []

    if score >= 3:
        missing_items = [k for k, v in found.items() if not v]
        return {"code": "company_requisites", "title": "Company Requisites",
                "status": "warning", "details": f"Partial ({score}/7). Missing: {', '.join(missing_items)}",
                "evidence": evidence}, [{
            "code": "incomplete_requisites", "title": "Incomplete requisites",
            "severity": "medium", "category": "company_info",
            "description": f"Missing: {', '.join(missing_items)}.",
            "recommendation": "Add missing company details.",
            "evidence": evidence, "possible_fine": 50000}]

    if score >= 1:
        return {"code": "company_requisites", "title": "Company Requisites",
                "status": "warning", "details": f"Minimal ({score}/7)", "evidence": evidence}, [{
            "code": "minimal_requisites", "title": "Minimal requisites",
            "severity": "high", "category": "company_info",
            "description": f"Only {score}/7 found.",
            "recommendation": "Add full company details.",
            "evidence": evidence, "possible_fine": 100000}]

    return {"code": "company_requisites", "title": "Company Requisites",
            "status": "failed", "details": "Not found", "evidence": []}, [{
        "code": "missing_requisites", "title": "Missing requisites",
        "severity": "high", "category": "company_info",
        "description": "No company details found.",
        "recommendation": "Create a requisites page.", "evidence": [], "possible_fine": 100000}]


# -- 8. Consumer Rights --

def check_consumer_rights(pages_html: dict, links: List[str]) -> Tuple[dict, list]:
    all_text = _all_text(pages_html)
    for link in links:
        all_text += " " + link.lower()

    docs = {
        "offer/contract": ["offer", "contract", "public offer"],
        "returns/exchange": ["return", "exchange", "refund", "returns policy"],
        "delivery": ["delivery", "shipping", "delivery method"],
        "payment": ["payment", "payment method", "price"],
        "warranty": ["warranty", "guarantee", "warranty period"],
    }

    found = {}
    evidence = []
    for doc, keywords in docs.items():
        found[doc] = any(kw in all_text for kw in keywords)
        if found[doc]:
            evidence.append(f"Found: {doc}")

    found_count = sum(found.values())

    if found_count >= 4:
        return {"code": "consumer_rights", "title": "Consumer Documents",
                "status": "passed", "details": f"Found ({found_count}/5)", "evidence": evidence}, []

    missing = [k for k, v in found.items() if not v]

    if found_count >= 2:
        return {"code": "consumer_rights", "title": "Consumer Documents",
                "status": "warning", "details": f"Missing: {', '.join(missing)}", "evidence": evidence}, [{
            "code": "missing_consumer_docs", "title": f"Missing: {', '.join(missing)}",
            "severity": "medium", "category": "consumer_rights",
            "description": f"Missing documents: {', '.join(missing)}.",
            "recommendation": f"Add pages for: {', '.join(missing)}.",
            "evidence": evidence, "possible_fine": 50000}]

    return {"code": "consumer_rights", "title": "Consumer Documents",
            "status": "failed", "details": f"Most missing ({found_count}/5)", "evidence": evidence}, [{
        "code": "missing_consumer_docs_critical", "title": "Critical lack of consumer docs",
        "severity": "high", "category": "consumer_rights",
        "description": f"Only {found_count}/5 documents found.",
        "recommendation": "Add all required consumer documents urgently.",
        "evidence": evidence, "possible_fine": 100000}]
# -- 9. Age Marking (18+) --

def check_age_marking(pages_html: dict) -> Tuple[dict, list]:
    age_patterns = [
        re.compile(r"18\+", re.IGNORECASE),
        re.compile(r"adult\s*content", re.IGNORECASE),
        re.compile(r"age\s*restriction", re.IGNORECASE),
    ]
    adult_kw = ["casino", "betting", "bookmaker", "alcohol", "tobacco", "vape",
                "adult content", "18+", "erotic", "porn"]

    all_text = _all_text(pages_html)
    all_html = _all_html(pages_html)

    has_adult = any(kw in all_text for kw in adult_kw)
    has_age_mark = any(p.search(all_html) for p in age_patterns)

    if not has_adult:
        return {"code": "age_marking", "title": "Age Marking (18+)",
                "status": "passed", "details": "No adult content", "evidence": []}, []

    if has_age_mark:
        return {"code": "age_marking", "title": "Age Marking (18+)",
                "status": "passed", "details": "Age marking present", "evidence": ["18+ marking found"]}, []

    return {"code": "age_marking", "title": "Age Marking (18+)",
            "status": "failed", "details": "Adult content without marking", "evidence": []}, [{
        "code": "missing_age_marking", "title": "Missing 18+ marking",
        "severity": "high", "category": "age_marking",
        "description": "Adult content without age marking. Violation of 436-FZ.",
        "recommendation": "Add 18+ marking.", "evidence": [], "possible_fine": 50000}]


# -- 10. Copyright --

def check_copyright(pages_html: dict) -> Tuple[dict, list]:
    patterns = [
        re.compile(r"\u00a9\s*\d{4}", re.IGNORECASE),
        re.compile(r"copyright\s*\d{4}", re.IGNORECASE),
        re.compile(r"all\s*rights\s*reserved", re.IGNORECASE),
    ]
    all_html = _all_html(pages_html)
    found = any(p.search(all_html) for p in patterns)

    if found:
        return {"code": "copyright", "title": "Copyright", "status": "passed",
                "details": "Copyright found", "evidence": ["Copyright present"]}, []

    return {"code": "copyright", "title": "Copyright", "status": "warning",
            "details": "Not found", "evidence": []}, [{
        "code": "missing_copyright", "title": "Missing copyright",
        "severity": "low", "category": "copyright",
        "description": "No copyright notice.",
        "recommendation": "Add copyright in footer.", "evidence": [], "possible_fine": None}]


# -- 11. Contacts --

def check_contacts(pages_html: dict) -> Tuple[dict, list]:
    phone_pat = re.compile(r"(\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}")
    email_pat = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    address_hint = re.compile(r"(address|location|office|store)", re.IGNORECASE)
    schedule_pat = re.compile(r"(working hours|schedule|mon|tue|wed|thu|fri|sat|sun|daily)", re.IGNORECASE)
    map_pat = re.compile(r"(map|google\.maps|yandex\.maps|2gis)", re.IGNORECASE)

    found = {"phone": False, "email": False, "address": False, "schedule": False, "map": False}
    evidence = []

    for url, html in pages_html.items():
        soup = BeautifulSoup(html, "lxml")
        text = soup.get_text(" ", strip=True)

        if phone_pat.search(text) and not found["phone"]:
            found["phone"] = True; evidence.append("Phone found")
        if email_pat.search(text) and not found["email"]:
            found["email"] = True; evidence.append("Email found")
        if address_hint.search(text) and not found["address"]:
            found["address"] = True; evidence.append("Address found")
        if schedule_pat.search(text) and not found["schedule"]:
            found["schedule"] = True; evidence.append("Schedule found")
        if map_pat.search(text) and not found["map"]:
            found["map"] = True; evidence.append("Map found")

    score = sum(found.values())

    if score >= 4:
        return {"code": "contacts", "title": "Contact Info", "status": "passed",
                "details": f"Found ({score}/5)", "evidence": evidence}, []

    if score >= 2:
        missing = [k for k, v in found.items() if not v]
        return {"code": "contacts", "title": "Contact Info", "status": "warning",
                "details": f"Partial ({score}/5). Missing: {', '.join(missing)}", "evidence": evidence}, [{
            "code": "incomplete_contacts", "title": "Incomplete contacts",
            "severity": "medium", "category": "contacts",
            "description": f"Missing: {', '.join(missing)}.",
            "recommendation": "Add missing contact info.", "evidence": evidence, "possible_fine": 30000}]

    return {"code": "contacts", "title": "Contact Info", "status": "failed",
            "details": "Almost no contacts", "evidence": evidence}, [{
        "code": "missing_contacts", "title": "Missing contacts",
        "severity": "high", "category": "contacts",
        "description": "No contact information found.",
        "recommendation": "Add phone, email, address.", "evidence": [], "possible_fine": 50000}]


# -- 12. Payment Security --

def check_payment_security(pages_html: dict) -> Tuple[dict, list]:
    payment_kw = ["card payment", "pay", "checkout", "cart", "mastercard", "visa", "mir",
                  "stripe", "paypal", "yookassa", "robokassa"]
    security_kw = ["secure payment", "payment security", "ssl", "pci dss",
                   "3d secure", "encryption", "data protected"]

    all_text = _all_text(pages_html)
    has_payment = any(kw in all_text for kw in payment_kw)
    has_security = any(kw in all_text for kw in security_kw)

    if not has_payment:
        return {"code": "payment_security", "title": "Payment Security",
                "status": "passed", "details": "No payment forms", "evidence": []}, []

    if has_security:
        return {"code": "payment_security", "title": "Payment Security",
                "status": "passed", "details": "Security info present", "evidence": ["Security mention found"]}, []

    return {"code": "payment_security", "title": "Payment Security",
            "status": "warning", "details": "Payments without security info", "evidence": []}, [{
        "code": "no_payment_security_info", "title": "No payment security info",
        "severity": "medium", "category": "payment_security",
        "description": "Site accepts payments without security disclosure.",
        "recommendation": "Add SSL, PCI DSS, 3D Secure info.", "evidence": [], "possible_fine": None}]


# -- 13. Technical --

def check_technical(main_html: str, final_url: str, robots_ok: bool, sitemap_ok: bool) -> Tuple[List[dict], list]:
    checks = []
    issues = []
    soup = BeautifulSoup(main_html, "lxml")

    # Title
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True) if title_tag else ""
    has_title = bool(title_text)
    title_len = len(title_text)
    title_ok = has_title and 10 <= title_len <= 120

    if title_ok:
        checks.append({"code": "meta_title", "title": "<title>", "status": "passed",
                       "details": f"Title: {title_text[:80]}", "evidence": []})
    elif has_title:
        checks.append({"code": "meta_title", "title": "<title>", "status": "warning",
                       "details": f"Too short ({title_len} chars)", "evidence": []})
        issues.append({"code": "short_title", "title": "Short <title>", "severity": "low",
                       "category": "technical", "description": f"Title: {title_len} chars.",
                       "recommendation": "Use 30-60 chars.", "evidence": [], "possible_fine": None})
    else:
        checks.append({"code": "meta_title", "title": "<title>", "status": "failed",
                       "details": "Missing", "evidence": []})
        issues.append({"code": "missing_title", "title": "Missing <title>", "severity": "medium",
                       "category": "technical", "description": "Critical for SEO.",
                       "recommendation": "Add <title>.", "evidence": [], "possible_fine": None})

    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    desc_content = (meta_desc.get("content", "").strip()) if meta_desc else ""
    has_meta = bool(desc_content)
    desc_len = len(desc_content)
    desc_ok = has_meta and 50 <= desc_len <= 300
    checks.append({"code": "meta_description", "title": "Meta description",
                   "status": "passed" if desc_ok else "warning",
                   "details": f"Description ({desc_len} chars)" if has_meta else "Missing", "evidence": []})

    # Viewport
    viewport = soup.find("meta", attrs={"name": "viewport"})
    has_viewport = bool(viewport and viewport.get("content", ""))
    checks.append({"code": "viewport", "title": "Viewport (mobile)",
                   "status": "passed" if has_viewport else "warning",
                   "details": "Present" if has_viewport else "Missing - may not be mobile-friendly", "evidence": []})

    # Favicon
    favicon = soup.find("link", rel=lambda r: r and "icon" in r) or soup.find("link", href=lambda h: h and "favicon" in h)
    checks.append({"code": "favicon", "title": "Favicon",
                   "status": "passed" if favicon else "warning",
                   "details": "Found" if favicon else "Not found", "evidence": []})

    # Charset
    charset = soup.find("meta", attrs={"charset": True}) or soup.find("meta", attrs={"http-equiv": lambda v: v and "content-type" in v.lower()})
    checks.append({"code": "charset", "title": "Charset",
                   "status": "passed" if charset else "warning",
                   "details": "Specified" if charset else "Not specified", "evidence": []})

    # H1
    h1_tags = soup.find_all("h1")
    if len(h1_tags) == 1:
        checks.append({"code": "h1", "title": "H1 heading", "status": "passed",
                       "details": f"H1: {h1_tags[0].get_text(strip=True)[:80]}", "evidence": []})
    elif len(h1_tags) > 1:
        checks.append({"code": "h1", "title": "H1 heading", "status": "warning",
                       "details": f"Multiple H1 ({len(h1_tags)})", "evidence": []})
    else:
        checks.append({"code": "h1", "title": "H1 heading", "status": "warning",
                       "details": "Missing", "evidence": []})

    # Open Graph
    og_title = soup.find("meta", property="og:title")
    og_desc = soup.find("meta", property="og:description")
    og_image = soup.find("meta", property="og:image")
    og_count = sum(1 for t in [og_title, og_desc, og_image] if t and t.get("content", "").strip())
    checks.append({"code": "open_graph", "title": "Open Graph",
                   "status": "passed" if og_count >= 2 else "warning",
                   "details": f"OG tags: {og_count}/3" if og_count > 0 else "No OG tags", "evidence": []})

    # Images alt
    images = soup.find_all("img")
    images_with_alt = sum(1 for img in images if img.get("alt"))
    alt_ratio = images_with_alt / len(images) if images else 1.0
    checks.append({"code": "img_alt", "title": "Image alt attributes",
                   "status": "passed" if alt_ratio >= 0.7 else "warning",
                   "details": f"Alt on {images_with_alt}/{len(images)} images" if images else "No images", "evidence": []})

    # Robots.txt
    checks.append({"code": "robots_txt", "title": "robots.txt",
                   "status": "passed" if robots_ok else "warning",
                   "details": "Available" if robots_ok else "Not available", "evidence": []})

    # Sitemap
    checks.append({"code": "sitemap_xml", "title": "sitemap.xml",
                   "status": "passed" if sitemap_ok else "warning",
                   "details": "Available" if sitemap_ok else "Not available", "evidence": []})

    return checks, issues


# -- 14. Server Location (152-FZ localization) --

async def check_server_location(final_url: str, timeout: int = TIMEOUT) -> Tuple[dict, list]:
    parsed = urlparse(final_url)
    hostname = parsed.netloc

    server_ip = None
    try:
        server_ip = socket.gethostbyname(hostname)
    except Exception:
        pass

    hosting_hints = []
    try:
        async with httpx.AsyncClient(headers=HEADERS, timeout=timeout, verify=False) as client:
            resp = await client.get(final_url)
            headers_lower = {k.lower(): v for k, v in resp.headers.items()}
            server_header = headers_lower.get("server", "")
            powered_by = headers_lower.get("x-powered-by", "")

            ru_hosting = ["nginx", "apache", "bitrix", "1c-bitrix", "umi", "netcat",
                          "hostland", "reg.ru", "nic.ru", "beget", "timeweb", "sprinthost",
                          "masterhost", "spaceweb", "majordomo", "jino", "ihc.ru"]
            for h in ru_hosting:
                if h in server_header.lower() or h in powered_by.lower():
                    hosting_hints.append(f"Header: {server_header or powered_by}")
                    break
    except Exception:
        pass

    geo_country = None
    geo_org = None
    if server_ip:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"http://ip-api.com/json/{server_ip}?fields=country,countryCode,org")
                if r.status_code == 200:
                    data = r.json()
                    geo_country = data.get("countryCode", "")
                    geo_org = data.get("org", "")
        except Exception:
            pass

    evidence = []
    if server_ip:
        evidence.append(f"Server IP: {server_ip}")
    if geo_country:
        evidence.append(f"Server country: {geo_country}")
    if geo_org:
        evidence.append(f"Provider: {geo_org}")
    evidence.extend(hosting_hints)

    is_russian_ip = geo_country == "RU"

    if is_russian_ip:
        return {"code": "server_location", "title": "Server Localization (152-FZ)",
                "status": "passed", "details": f"Server in Russia ({geo_country})", "evidence": evidence}, []

    if server_ip and geo_country:
        return {"code": "server_location", "title": "Server Localization (152-FZ)",
                "status": "warning",
                "details": f"Server outside RF ({geo_country}). Personal data of RF citizens must be stored in Russia per 152-FZ Art. 18.5.",
                "evidence": evidence}, [{
            "code": "server_not_in_russia", "title": "Server outside Russian Federation",
            "severity": "high", "category": "personal_data",
            "description": f"Server IP ({server_ip}) located in {geo_country}. Art. 18.5 of 152-FZ requires recording, systematization, accumulation, storage, clarification and extraction of personal data of RF citizens to be done using databases located in Russia.",
            "recommendation": "Move servers/databases to Russia. Use Russian hosting providers (Selectel, DataLine, Rostelecom-DPC, etc.).",
            "evidence": evidence, "possible_fine": 1000000}]

    return {"code": "server_location", "title": "Server Localization (152-FZ)",
            "status": "warning", "details": "Could not determine server location. Verify manually.",
            "evidence": evidence}, [{
        "code": "server_location_unknown", "title": "Server location unknown",
        "severity": "medium", "category": "personal_data",
        "description": "Could not determine server country. Verify manually for 152-FZ compliance.",
        "recommendation": "Check server geolocation via whois. Ensure hosting in Russia.",
        "evidence": evidence, "possible_fine": 1000000}]


# -- 15. RKN Notification (Personal Data Operator Registry) --

def check_rkn_notification(pages_html: dict) -> Tuple[dict, list]:
    all_text = _all_text(pages_html)
    rkn_kw = ["roskomnadzor", "rkn", "notification to roskomnadzor",
              "personal data operator registry", "personal data operator",
              "processing notification", "registered in registry",
              "operator registration number", "rkn registry number"]

    found = [kw for kw in rkn_kw if kw in all_text]

    if found:
        return {"code": "rkn_notification", "title": "RKN Notification (152-FZ Art. 22)",
                "status": "passed", "details": "RKN registration mention found", "evidence": found[:3]}, []

    return {"code": "rkn_notification", "title": "RKN Notification (152-FZ Art. 22)",
            "status": "warning", "details": "No RKN registration info found", "evidence": []}, [{
        "code": "no_rkn_notification", "title": "No Roskomnadzor notification info",
        "severity": "high", "category": "personal_data",
        "description": "Per Art. 22 of 152-FZ, personal data operators must notify Roskomnadzor before processing begins. Absence of this info on site may indicate violation.",
        "recommendation": "Submit notification to RKN via pd.rkn.gov.ru and publish registration info on site.",
        "evidence": [], "possible_fine": 300000}]


# -- 16. Full Age Marking (436-FZ) --

def check_age_marking_full(pages_html: dict) -> Tuple[dict, list]:
    all_html = _all_html(pages_html)
    age_patterns = {
        "0+": re.compile(r"0\+|\(0\+\)|РґР»СЏ Р»СЋР±РѕР№ Р°СѓРґРёС‚РѕСЂРёРё|Р±РµР· РѕРіСЂР°РЅРёС‡РµРЅРёР№", re.IGNORECASE),
        "6+": re.compile(r"6\+|\(6\+\)|РґР»СЏ РґРµС‚РµР№ СЃС‚Р°СЂС€Рµ 6", re.IGNORECASE),
        "12+": re.compile(r"12\+|\(12\+\)|РґР»СЏ РґРµС‚РµР№ СЃС‚Р°СЂС€Рµ 12", re.IGNORECASE),
        "16+": re.compile(r"16\+|\(16\+\)|РґР»СЏ РґРµС‚РµР№ СЃС‚Р°СЂС€Рµ 16", re.IGNORECASE),
        "18+": re.compile(r"18\+|\(18\+\)|РґР»СЏ РІР·СЂРѕСЃР»С‹С…|Р·Р°РїСЂРµС‰РµРЅРѕ РґР»СЏ РґРµС‚РµР№", re.IGNORECASE),
    }

    found_any = False
    evidence = []
    for label, pat in age_patterns.items():
        if pat.search(all_html):
            found_any = True
            evidence.append(f"Age marking {label} found")

    if found_any:
        return {"code": "age_marking_full", "title": "Age Marking (436-FZ)",
                "status": "passed", "details": "Age marking present", "evidence": evidence}, []

    return {"code": "age_marking_full", "title": "Age Marking (436-FZ)",
            "status": "warning", "details": "No age marking found. Required by 436-FZ for all public websites in Russia.",
            "evidence": []}, [{
        "code": "missing_age_marking_full", "title": "Missing age marking (436-FZ)",
        "severity": "medium", "category": "age_marking",
        "description": "Federal Law 436-FZ 'On Protection of Children from Harmful Information' requires all websites accessible in Russia to display age category marking (0+, 6+, 12+, 16+ or 18+).",
        "recommendation": "Add age marking (e.g., '16+') in footer or header of every page.",
        "evidence": [], "possible_fine": 50000}]


# -- 17. Domain Zone Requirements --

def check_domain_requirements(final_url: str, pages_html: dict) -> Tuple[dict, list]:
    parsed = urlparse(final_url)
    domain = parsed.netloc.lower()
    is_ru = domain.endswith(".ru") or domain.endswith(".ru.") or domain.endswith(".xn--p1ai")

    if not is_ru:
        return {"code": "domain_requirements", "title": "Domain Zone Requirements",
                "status": "passed", "details": "Not a .ru/.rf domain - no special requirements", "evidence": []}, []

    all_text = _all_text(pages_html)
    owner_kw = ["site owner", "domain administrator", "site administrator",
                "contact person", "responsible person"]
    has_owner = any(kw in all_text for kw in owner_kw)

    if has_owner:
        return {"code": "domain_requirements", "title": "Domain Zone Requirements (.ru/.rf)",
                "status": "passed", "details": "Site owner info found", "evidence": ["Owner info present"]}, []

    return {"code": "domain_requirements", "title": "Domain Zone Requirements (.ru/.rf)",
            "status": "warning", "details": ".ru/.rf domain: site owner info not found on site. Required by domain registry rules.",
            "evidence": []}, [{
        "code": "no_domain_owner_info", "title": "Missing site owner info for .ru/.rf domain",
        "severity": "low", "category": "company_info",
        "description": ".ru and .rf domain registry rules require publishing administrator/owner contact information on the website.",
        "recommendation": "Add site administrator contact info on the website.",
        "evidence": [], "possible_fine": None}]


# -- 18. Self-Employed / IP Marking --

def check_self_employed_marking(pages_html: dict) -> Tuple[dict, list]:
    all_text = _all_text(pages_html)
    ip_kw = ["individual entrepreneur", "IE", "sole proprietor",
             "self-employed", "professional income tax", "NPD"]
    ogrnip_pat = re.compile(r"\bOGRNIP\s*:?\s*\d{15}\b", re.IGNORECASE)

    has_ip = any(kw in all_text for kw in ip_kw) or bool(ogrnip_pat.search(all_text))

    if not has_ip:
        return {"code": "self_employed_marking", "title": "Self-Employed / IP Marking",
                "status": "passed", "details": "No IE/self-employed indicators", "evidence": []}, []

    has_full_name = re.compile(r"(IE|IP|individual entrepreneur)\s+[A-Z][a-z]+\s+[A-Z]", re.IGNORECASE).search(all_text)
    has_ogrnip = bool(ogrnip_pat.search(all_text))

    if has_full_name or has_ogrnip:
        return {"code": "self_employed_marking", "title": "Self-Employed / IP Marking",
                "status": "passed", "details": "IE details found", "evidence": ["IE info present"]}, []

    return {"code": "self_employed_marking", "title": "Self-Employed / IP Marking",
            "status": "warning", "details": "IE indicators found but details incomplete", "evidence": []}, [{
        "code": "incomplete_ip_info", "title": "Incomplete IE/self-employed info",
        "severity": "medium", "category": "company_info",
        "description": "Individual entrepreneur or self-employed indicators found but full name and OGRNIP not provided. Required by consumer protection law.",
        "recommendation": "Add full name of IE and OGRNIP number on the website.",
        "evidence": [], "possible_fine": 30000}]


# -- Robots & Sitemap --

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


# -- Score --

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
