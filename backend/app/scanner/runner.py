import asyncio
from app.scanner.checks import (
    fetch_page,
    fetch_page_playwright,
    fetch_sitemap_links,
    extract_all_internal_links,
    check_https_detailed,
    check_privacy_policy,
    check_user_agreement,
    check_form_consent,
    check_cookie_banner,
    check_advertising_marking,
    check_company_requisites,
    check_consumer_rights,
    check_age_marking,
    check_copyright,
    check_contacts,
    check_payment_security,
    check_technical,
    check_robots_sitemap,
    check_server_location,
    check_rkn_notification,
    check_age_marking_full,
    check_domain_requirements,
    check_self_employed_marking,
    calculate_score,
    TIMEOUT,
)
from app.core.url_utils import normalize_url


async def run_full_scan(url: str, progress_callback=None) -> dict:
    """
    Main scanner entry point.
    Returns dict with: checks, issues, score, risk_level, pages_checked, meta
    """

    async def update_progress(pct: int, msg: str = ""):
        if progress_callback:
            await progress_callback(pct, msg)

    await update_progress(5, "Начало проверки")

    normalized, err = normalize_url(url)
    if err:
        raise ValueError(err)

    # Fetch main page
    html, final_url = await fetch_page(normalized, TIMEOUT)

    if not html:
        html = await fetch_page_playwright(normalized)
        final_url = normalized
        if not html:
            raise ConnectionError(f"Не удалось загрузить страницу: {normalized}")

    await update_progress(20, "Главная страница загружена")

    pages_html: dict[str, str] = {final_url: html}

    # Discover internal links (ALL links, not just keyword-matched)
    links = extract_all_internal_links(html, final_url)

    # Also try sitemap for additional URLs
    sitemap_urls = await fetch_sitemap_links(final_url)
    for s_url in sitemap_urls:
        if s_url not in links and len(links) < 20:
            links.append(s_url)

    await update_progress(35, f"Найдено {len(links)} страниц для проверки")

    # Fetch linked pages (up to limit)
    fetch_tasks = [fetch_page(link, TIMEOUT) for link in links[:10]]
    results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

    for link, result in zip(links[:10], results):
        if isinstance(result, Exception):
            continue
        page_html, page_url = result
        if page_html:
            pages_html[page_url or link] = page_html

    await update_progress(55, f"Загружено {len(pages_html)} страниц")

    # Check robots.txt and sitemap.xml
    robots_ok, sitemap_ok = await check_robots_sitemap(final_url)

    # Run all checks
    all_checks = []
    all_issues = []

    # 1. HTTPS (detailed)
    https_check, https_issues = await check_https_detailed(final_url)
    all_checks.append(https_check)
    all_issues.extend(https_issues)
    await update_progress(60, "Проверка HTTPS")

    # 2. Privacy Policy
    pp_check, pp_issues = check_privacy_policy(pages_html, links)
    all_checks.append(pp_check)
    all_issues.extend(pp_issues)
    await update_progress(65, "Проверка политики конфиденциальности")

    # 3. User Agreement
    ua_check, ua_issues = check_user_agreement(pages_html, links)
    all_checks.append(ua_check)
    all_issues.extend(ua_issues)

    # 4. Form Consent
    fc_check, fc_issues = check_form_consent(pages_html)
    all_checks.append(fc_check)
    all_issues.extend(fc_issues)
    await update_progress(70, "Проверка форм сбора данных")

    # 5. Cookie Banner
    cb_check, cb_issues = check_cookie_banner(pages_html)
    all_checks.append(cb_check)
    all_issues.extend(cb_issues)

    # 6. Advertising Marking
    ad_check, ad_issues = check_advertising_marking(pages_html)
    all_checks.append(ad_check)
    all_issues.extend(ad_issues)
    await update_progress(75, "Проверка маркировки рекламы")

    # 7. Company Requisites
    req_check, req_issues = check_company_requisites(pages_html)
    all_checks.append(req_check)
    all_issues.extend(req_issues)

    # 8. Consumer Rights
    cr_check, cr_issues = check_consumer_rights(pages_html, links)
    all_checks.append(cr_check)
    all_issues.extend(cr_issues)
    await update_progress(80, "Проверка документов для потребителей")

    # 9. Age Marking
    age_check, age_issues = check_age_marking(pages_html)
    all_checks.append(age_check)
    all_issues.extend(age_issues)

    # 10. Copyright
    copy_check, copy_issues = check_copyright(pages_html)
    all_checks.append(copy_check)
    all_issues.extend(copy_issues)

    # 11. Contacts
    contacts_check, contacts_issues = check_contacts(pages_html)
    all_checks.append(contacts_check)
    all_issues.extend(contacts_issues)

    # 12. Payment Security
    pay_check, pay_issues = check_payment_security(pages_html)
    all_checks.append(pay_check)
    all_issues.extend(pay_issues)

    # 13. Technical checks
    tech_checks, tech_issues = check_technical(html, final_url, robots_ok, sitemap_ok)
    all_checks.extend(tech_checks)
    all_issues.extend(tech_issues)

    # 14. Server Location (152-FZ)
    loc_check, loc_issues = await check_server_location(final_url)
    all_checks.append(loc_check)
    all_issues.extend(loc_issues)
    await update_progress(85, "Проверка локализации серверов")

    # 15. RKN Notification
    rkn_check, rkn_issues = check_rkn_notification(pages_html)
    all_checks.append(rkn_check)
    all_issues.extend(rkn_issues)

    # 16. Full Age Marking (436-FZ)
    age_full_check, age_full_issues = check_age_marking_full(pages_html)
    all_checks.append(age_full_check)
    all_issues.extend(age_full_issues)

    # 17. Domain Requirements
    dom_check, dom_issues = check_domain_requirements(final_url, pages_html)
    all_checks.append(dom_check)
    all_issues.extend(dom_issues)

    # 18. Self-Employed / IP Marking
    se_check, se_issues = check_self_employed_marking(pages_html)
    all_checks.append(se_check)
    all_issues.extend(se_issues)

    await update_progress(90, "Все проверки завершены")

    # Calculate score
    score, risk_level = calculate_score(all_issues)

    # Build recommendations (deduplicated from issues)
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
