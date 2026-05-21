import asyncio

from app.scanner.checks import (
    fetch_page,
    fetch_page_playwright,
    fetch_sitemap_links,
    extract_all_internal_links,
    detect_site_type,
    detect_language,
    SITE_TYPE_LABELS,
    check_privacy_policy,
    check_form_consent,
    check_server_location,
    check_rkn_notification,
    check_cookie_banner,
    check_advertising_marking,
    check_company_requisites,
    check_consumer_rights,
    calculate_score,
    TIMEOUT,
)
from app.core.url_utils import normalize_url


async def run_full_scan(url: str, progress_callback=None) -> dict:
    """
    Главная точка входа сканера. Возвращает dict с полями:
    checks, issues, score, risk_level, pages_checked, recommendations, meta.

    Набор проверок (по требованию РКН и законодательству РФ):
      1. 152-ФЗ — Политика обработки персональных данных
      2. 152-ФЗ — Согласие на обработку данных в формах
      3. 152-ФЗ — Локализация серверов (ст. 18.5)
      4. 152-ФЗ — Уведомление Роскомнадзора (ст. 22)
      5. Cookie-баннер
      6. 38-ФЗ — Маркировка рекламы (ERID)
      7. 149-ФЗ — Реквизиты компании
      8. ЗоЗПП — Документы для потребителей
    """

    async def update_progress(pct: int, msg: str = ""):
        if progress_callback:
            await progress_callback(pct, msg)

    await update_progress(5, "Начало проверки")

    normalized, err = normalize_url(url)
    if err:
        raise ValueError(err)

    # Загрузка главной страницы
    html, final_url = await fetch_page(normalized, TIMEOUT)
    if not html:
        html = await fetch_page_playwright(normalized)
        final_url = normalized
        if not html:
            raise ConnectionError(f"Не удалось загрузить страницу: {normalized}")
    else:
        SPA_MARKERS = [
            "не работает без javascript", "включите javascript",
            "javascript должен быть включен", "javascript is required",
            "you need to enable javascript", "please enable javascript",
        ]
        try:
            from bs4 import BeautifulSoup as _BS
            text_only = _BS(html, "lxml").get_text(" ", strip=True)
        except Exception:
            text_only = html
        text_lower = text_only.lower()
        is_spa = (
            len(text_only) < 500
            or any(m in text_lower for m in SPA_MARKERS)
        )
        if is_spa:
            await update_progress(15, "Похоже на SPA, рендерим через Playwright")
            pw_html = await fetch_page_playwright(normalized)
            if pw_html and len(pw_html) > len(html):
                html = pw_html
                final_url = final_url or normalized

    await update_progress(20, "Главная страница загружена")

    pages_html: dict[str, str] = {final_url: html}

    # Внутренние ссылки + sitemap
    links = extract_all_internal_links(html, final_url)
    sitemap_urls = await fetch_sitemap_links(final_url)
    for s_url in sitemap_urls:
        if s_url not in links and len(links) < 20:
            links.append(s_url)

    await update_progress(35, f"Найдено {len(links)} страниц для проверки")

    # Загрузка дополнительных страниц
    fetch_tasks = [fetch_page(link, TIMEOUT) for link in links[:12]]
    results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
    for link, result in zip(links[:12], results):
        if isinstance(result, Exception):
            continue
        page_html, page_url = result
        if page_html:
            pages_html[page_url or link] = page_html

    await update_progress(55, f"Загружено {len(pages_html)} страниц")

    # Принудительно загружаем legal-страницы (включая cross-domain)
    LEGAL_HINTS = [
        "/polic", "/privac", "/personal", "/конфиденциал", "/персональн", "/pdn",
        "/offer", "/оферт", "/договор", "/соглашен", "/terms", "/agreement",
        "/contact", "/контакт", "/rekvizit", "/реквизит",
        "/cookie", "/куки",
        "/доставк", "/delivery", "/оплат", "/payment", "/возврат", "/return", "/refund",
    ]
    LEGAL_EXCLUDE = ["dashboard", "advisor", "settings", "account", "myactivity", "controls"]

    from bs4 import BeautifulSoup as _BS
    cross_domain_legal = []
    seen_extra = set(pages_html.keys())
    for src_html in list(pages_html.values()):
        try:
            soup = _BS(src_html, "lxml")
        except Exception:
            continue
        for a in soup.find_all("a", href=True):
            href = (a.get("href") or "").strip()
            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            full = href if href.startswith(("http://", "https://")) else None
            if not full:
                continue
            low = full.lower()
            if any(ex in low for ex in LEGAL_EXCLUDE):
                continue
            if any(h in low for h in LEGAL_HINTS) and full not in seen_extra:
                seen_extra.add(full)
                cross_domain_legal.append(full)
            if len(cross_domain_legal) >= 6:
                break
        if len(cross_domain_legal) >= 6:
            break

    extra_urls = list(cross_domain_legal)
    for link in links:
        low = link.lower()
        if link in pages_html or link in seen_extra:
            continue
        if any(ex in low for ex in LEGAL_EXCLUDE):
            continue
        if any(h in low for h in LEGAL_HINTS):
            seen_extra.add(link)
            extra_urls.append(link)
        if len(extra_urls) >= 8:
            break
    if extra_urls:
        extra_results = await asyncio.gather(*(fetch_page(u, TIMEOUT) for u in extra_urls), return_exceptions=True)
        for src, res in zip(extra_urls, extra_results):
            if isinstance(res, Exception):
                continue
            page_html, page_url = res
            if page_html:
                pages_html[page_url or src] = page_html
        await update_progress(58, f"Догружено legal-страниц: +{len(extra_urls)}")

    # Тип сайта и язык
    site_type, site_type_signals = detect_site_type(pages_html)
    site_type_label = SITE_TYPE_LABELS.get(site_type, site_type)
    language = detect_language(pages_html)

    from urllib.parse import urlparse as _urlparse
    domain = _urlparse(final_url).netloc.lower()
    is_ru_domain = domain.endswith(".ru") or domain.endswith(".рф") or domain.endswith(".xn--p1ai")
    is_russian_audience = (language == "ru") or is_ru_domain

    all_checks = []
    all_issues = []

    # 0. Сводка: язык / аудитория (служебная — определяет, применяются ли проверки)
    if not is_russian_audience:
        all_checks.append({
            "code": "audience",
            "title": "Целевая аудитория",
            "status": "warning",
            "details": (
                f"Сайт не на русском языке (язык: {language}) и домен не .ru/.рф. "
                "Требования российского законодательства могут быть нерелевантны. "
                "Проверки выполнены справочно."
            ),
            "evidence": [f"Домен: {domain}", f"Язык контента: {language}"],
        })
    else:
        all_checks.append({
            "code": "audience",
            "title": "Целевая аудитория",
            "status": "passed",
            "details": (
                f"Сайт ориентирован на российскую аудиторию (язык: {language}, домен: {domain}). "
                "Применяются требования российского законодательства."
            ),
            "evidence": [f"Домен: {domain}", f"Язык контента: {language}"],
        })

    def _na_check(code: str, title: str) -> dict:
        return {
            "code": code, "title": title,
            "status": "passed",
            "details": "Не применимо: сайт не для российской аудитории",
            "evidence": [],
        }

    # 1. 152-ФЗ — Политика обработки персональных данных
    if is_russian_audience:
        pp_check, pp_issues = check_privacy_policy(pages_html, links)
        all_checks.append(pp_check); all_issues.extend(pp_issues)
    else:
        all_checks.append(_na_check("privacy_policy", "152-ФЗ — Политика обработки персональных данных"))
    await update_progress(60, "Проверка политики обработки ПДн")

    # 2. 152-ФЗ — Согласие на обработку данных в формах
    fc_check, fc_issues = check_form_consent(pages_html)
    all_checks.append(fc_check)
    if is_russian_audience:
        all_issues.extend(fc_issues)
    await update_progress(70, "Проверка форм сбора данных")

    # 3. 152-ФЗ — Локализация серверов (ст. 18.5) — «Сервер в РФ»
    if is_russian_audience:
        loc_check, loc_issues = await check_server_location(final_url)
        all_checks.append(loc_check); all_issues.extend(loc_issues)
    else:
        all_checks.append(_na_check("server_location", "152-ФЗ — Локализация серверов (ст. 18.5)"))
    await update_progress(78, "Проверка локализации серверов")

    # 4. 152-ФЗ — Уведомление Роскомнадзора (ст. 22)
    if is_russian_audience:
        rkn_check, rkn_issues = check_rkn_notification(pages_html)
        all_checks.append(rkn_check); all_issues.extend(rkn_issues)
    else:
        all_checks.append(_na_check("rkn_notification", "152-ФЗ — Уведомление Роскомнадзора (ст. 22)"))

    # 5. Cookie-баннер / Cookie-политика
    cb_check, cb_issues = check_cookie_banner(pages_html)
    all_checks.append(cb_check)
    if is_russian_audience:
        all_issues.extend(cb_issues)
    await update_progress(85, "Проверка cookie-баннера")

    # 6. 38-ФЗ — Маркировка рекламы (ERID)
    if is_russian_audience:
        ad_check, ad_issues = check_advertising_marking(pages_html)
        all_checks.append(ad_check); all_issues.extend(ad_issues)
    else:
        all_checks.append(_na_check("advertising_marking", "38-ФЗ — Маркировка рекламы (ERID)"))

    # 7. 149-ФЗ — Реквизиты компании
    if is_russian_audience:
        req_check, req_issues = check_company_requisites(pages_html)
        all_checks.append(req_check); all_issues.extend(req_issues)
    else:
        all_checks.append(_na_check("company_requisites", "149-ФЗ — Реквизиты компании"))

    # 8. ЗоЗПП — Документы для потребителей
    if is_russian_audience:
        cr_check, cr_issues = check_consumer_rights(pages_html, links, site_type)
        all_checks.append(cr_check); all_issues.extend(cr_issues)
    else:
        all_checks.append(_na_check("consumer_rights", "ЗоЗПП — Документы для потребителей"))

    await update_progress(90, "Все проверки завершены")

    score, risk_level = calculate_score(all_issues)

    # Рекомендации (без дублей)
    recommendations = []
    seen_codes = set()
    for issue in all_issues:
        if issue["code"] not in seen_codes:
            seen_codes.add(issue["code"])
            recommendations.append({
                "code": issue["code"],
                "title": issue["title"],
                "recommendation": issue["recommendation"],
                "severity": issue["severity"],
            })

    meta = {
        "final_url": final_url,
        "domain": domain,
        "language": language,
        "is_russian_audience": is_russian_audience,
        "site_type": site_type,
        "site_type_label": site_type_label,
        "site_type_signals": site_type_signals,
        "pages_count": len(pages_html),
        "links_found": len(links),
        "checks_count": len(all_checks),
        "issues_count": len(all_issues),
    }

    await update_progress(100, "Готово")

    return {
        "checks": all_checks,
        "issues": all_issues,
        "score": score,
        "risk_level": risk_level,
        "pages_checked": list(pages_html.keys()),
        "recommendations": recommendations,
        "meta": meta,
        "raw_html_snapshot": html[:50000] if html else None,
    }
