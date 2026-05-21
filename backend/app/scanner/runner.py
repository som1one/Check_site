import asyncio

from app.scanner.checks import (
    fetch_page,
    fetch_page_playwright,
    fetch_sitemap_links,
    extract_all_internal_links,
    detect_site_type,
    SITE_TYPE_LABELS,
    check_https_detailed,
    check_privacy_policy,
    check_form_consent,
    check_server_location,
    check_rkn_notification,
    check_cookie_banner,
    check_advertising_marking,
    check_company_requisites,
    check_consumer_rights,
    check_age_marking,
    check_contacts,
    check_payment_security,
    check_technical,
    check_robots_sitemap,
    calculate_score,
    TIMEOUT,
)
from app.core.url_utils import normalize_url


async def run_full_scan(url: str, progress_callback=None) -> dict:
    """
    Главная точка входа сканера. Возвращает dict с полями:
    checks, issues, score, risk_level, pages_checked, recommendations, meta.
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

    await update_progress(20, "Главная страница загружена")

    pages_html: dict[str, str] = {final_url: html}

    # Внутренние ссылки + sitemap
    links = extract_all_internal_links(html, final_url)
    sitemap_urls = await fetch_sitemap_links(final_url)
    for s_url in sitemap_urls:
        if s_url not in links and len(links) < 20:
            links.append(s_url)

    await update_progress(35, f"Найдено {len(links)} страниц для проверки")

    # Загрузка дополнительных страниц (приоритет — по anchor text)
    fetch_tasks = [fetch_page(link, TIMEOUT) for link in links[:12]]
    results = await asyncio.gather(*fetch_tasks, return_exceptions=True)
    for link, result in zip(links[:12], results):
        if isinstance(result, Exception):
            continue
        page_html, page_url = result
        if page_html:
            pages_html[page_url or link] = page_html

    await update_progress(55, f"Загружено {len(pages_html)} страниц")

    # Определяем тип сайта по содержимому
    site_type, site_type_signals = detect_site_type(pages_html)
    site_type_label = SITE_TYPE_LABELS.get(site_type, site_type)

    # robots.txt + sitemap.xml
    robots_ok, sitemap_ok = await check_robots_sitemap(final_url)

    all_checks = []
    all_issues = []

    # 1. HTTPS
    https_check, https_issues = await check_https_detailed(final_url)
    all_checks.append(https_check); all_issues.extend(https_issues)
    await update_progress(60, "Проверка HTTPS")

    # 2. 152-ФЗ — политика обработки ПДн
    pp_check, pp_issues = check_privacy_policy(pages_html, links)
    all_checks.append(pp_check); all_issues.extend(pp_issues)
    await update_progress(65, "Проверка политики обработки ПДн")

    # 3. 152-ФЗ — согласие в формах
    fc_check, fc_issues = check_form_consent(pages_html)
    all_checks.append(fc_check); all_issues.extend(fc_issues)
    await update_progress(70, "Проверка форм сбора данных")

    # 4. 152-ФЗ — локализация серверов
    loc_check, loc_issues = await check_server_location(final_url)
    all_checks.append(loc_check); all_issues.extend(loc_issues)
    await update_progress(75, "Проверка локализации серверов")

    # 5. 152-ФЗ — уведомление РКН
    rkn_check, rkn_issues = check_rkn_notification(pages_html)
    all_checks.append(rkn_check); all_issues.extend(rkn_issues)

    # 6. Cookie-баннер
    cb_check, cb_issues = check_cookie_banner(pages_html)
    all_checks.append(cb_check); all_issues.extend(cb_issues)
    await update_progress(80, "Проверка cookie-баннера")

    # 7. 38-ФЗ — маркировка рекламы
    ad_check, ad_issues = check_advertising_marking(pages_html)
    all_checks.append(ad_check); all_issues.extend(ad_issues)

    # 8. 149-ФЗ — реквизиты
    req_check, req_issues = check_company_requisites(pages_html)
    all_checks.append(req_check); all_issues.extend(req_issues)
    await update_progress(85, "Проверка реквизитов компании")

    # 9. ЗоЗПП — документы для потребителей (зависит от типа сайта)
    cr_check, cr_issues = check_consumer_rights(pages_html, links, site_type)
    all_checks.append(cr_check); all_issues.extend(cr_issues)

    # 10. 436-ФЗ — возрастная маркировка
    age_check, age_issues = check_age_marking(pages_html)
    all_checks.append(age_check); all_issues.extend(age_issues)

    # 11. Контакты
    contacts_check, contacts_issues = check_contacts(pages_html)
    all_checks.append(contacts_check); all_issues.extend(contacts_issues)

    # 12. Безопасность платежей
    pay_check, pay_issues = check_payment_security(pages_html)
    all_checks.append(pay_check); all_issues.extend(pay_issues)

    # 13. Технические
    tech_checks, tech_issues = check_technical(html, final_url, robots_ok, sitemap_ok)
    all_checks.extend(tech_checks); all_issues.extend(tech_issues)

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
        "site_type": site_type,
        "site_type_label": site_type_label,
        "site_type_signals": site_type_signals,
        "pages_count": len(pages_html),
        "links_found": len(links),
        "robots_txt": robots_ok,
        "sitemap_xml": sitemap_ok,
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
