from datetime import datetime
from jinja2 import Environment

PDF_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Отчёт SiteGuard — {{ url }}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a2e; background: #fff; font-size: 13px; line-height: 1.5; }
  .page { max-width: 800px; margin: 0 auto; padding: 40px 48px; }
  .header { display: flex; align-items: center; justify-content: space-between; border-bottom: 2px solid #0d9488; padding-bottom: 20px; margin-bottom: 32px; }
  .logo { font-size: 22px; font-weight: 700; color: #0d9488; letter-spacing: -0.5px; }
  .logo span { color: #1a1a2e; }
  .header-meta { text-align: right; font-size: 11px; color: #6b7280; }
  .section { margin-bottom: 28px; }
  .section-title { font-size: 15px; font-weight: 600; color: #1a1a2e; border-left: 3px solid #0d9488; padding-left: 10px; margin-bottom: 14px; }
  .score-block { display: flex; align-items: center; gap: 24px; background: #f8fafc; border-radius: 10px; padding: 20px 24px; margin-bottom: 24px; }
  .score-circle { width: 72px; height: 72px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: 700; color: #fff; flex-shrink: 0; }
  .score-green { background: #10b981; }
  .score-yellow { background: #f59e0b; }
  .score-red { background: #ef4444; }
  .score-info h2 { font-size: 18px; font-weight: 700; margin-bottom: 4px; }
  .score-info p { font-size: 12px; color: #6b7280; }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
  .badge-green { background: #d1fae5; color: #065f46; }
  .badge-yellow { background: #fef3c7; color: #92400e; }
  .badge-red { background: #fee2e2; color: #991b1b; }
  .badge-passed { background: #d1fae5; color: #065f46; }
  .badge-warning { background: #fef3c7; color: #92400e; }
  .badge-failed { background: #fee2e2; color: #991b1b; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { background: #f1f5f9; text-align: left; padding: 8px 10px; font-weight: 600; color: #374151; border-bottom: 1px solid #e2e8f0; }
  td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  .issue-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; }
  .issue-title { font-weight: 600; font-size: 13px; margin-bottom: 4px; }
  .issue-desc { font-size: 12px; color: #4b5563; margin-bottom: 6px; }
  .issue-rec { font-size: 12px; color: #0d9488; }
  .issue-fine { font-size: 11px; color: #ef4444; margin-top: 4px; }
  .disclaimer { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px 16px; font-size: 11px; color: #6b7280; margin-top: 32px; }
  .url-block { background: #f0fdfa; border: 1px solid #99f6e4; border-radius: 6px; padding: 8px 14px; font-size: 12px; color: #0f766e; margin-bottom: 20px; word-break: break-all; }
  @media print { body { -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
</style>
</head>
<body>
<div class="page">
  <div class="header">
    <div class="logo">Site<span>Guard</span></div>
    <div class="header-meta">
      <div>Автоматический аудит сайта</div>
      <div>{{ date }}</div>
    </div>
  </div>

  <div class="url-block">Проверяемый сайт: <strong>{{ url }}</strong></div>

  <div class="score-block">
    <div class="score-circle score-{{ risk_level }}">{{ score }}</div>
    <div class="score-info">
      <h2>
        {% if risk_level == 'green' %}Низкий уровень риска
        {% elif risk_level == 'yellow' %}Средний уровень риска
        {% else %}Высокий уровень риска{% endif %}
      </h2>
      <p>Итоговый балл: {{ score }} / 100 &nbsp;
        <span class="badge badge-{{ risk_level }}">
          {% if risk_level == 'green' %}Зелёный{% elif risk_level == 'yellow' %}Жёлтый{% else %}Красный{% endif %}
        </span>
      </p>
      <p style="margin-top:6px;">Проверено страниц: {{ pages_count }} &nbsp;|&nbsp; Нарушений: {{ issues_count }}</p>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Результаты проверок</div>
    <table>
      <thead>
        <tr>
          <th>Проверка</th>
          <th>Статус</th>
          <th>Детали</th>
        </tr>
      </thead>
      <tbody>
        {% for check in checks %}
        <tr>
          <td>{{ check.title }}</td>
          <td><span class="badge badge-{{ check.status }}">
            {% if check.status == 'passed' %}Пройдено
            {% elif check.status == 'warning' %}Предупреждение
            {% else %}Не пройдено{% endif %}
          </span></td>
          <td>{{ check.details }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  {% if issues %}
  <div class="section">
    <div class="section-title">Выявленные нарушения ({{ issues|length }})</div>
    {% for issue in issues %}
    <div class="issue-card">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
        <span class="badge badge-{% if issue.severity == 'high' %}failed{% elif issue.severity == 'medium' %}warning{% else %}passed{% endif %}">
          {% if issue.severity == 'high' %}Высокий{% elif issue.severity == 'medium' %}Средний{% else %}Низкий{% endif %}
        </span>
        <span class="issue-title">{{ issue.title }}</span>
      </div>
      <div class="issue-desc">{{ issue.description }}</div>
      <div class="issue-rec">Рекомендация: {{ issue.recommendation }}</div>
      {% if issue.possible_fine %}
      <div class="issue-fine">Возможный штраф: до {{ "{:,}".format(issue.possible_fine) }} ₽</div>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}

  {% if recommendations %}
  <div class="section">
    <div class="section-title">Рекомендации</div>
    <table>
      <thead>
        <tr><th>#</th><th>Рекомендация</th><th>Приоритет</th></tr>
      </thead>
      <tbody>
        {% for rec in recommendations %}
        <tr>
          <td>{{ loop.index }}</td>
          <td>{{ rec.recommendation }}</td>
          <td><span class="badge badge-{% if rec.severity == 'high' %}failed{% elif rec.severity == 'medium' %}warning{% else %}passed{% endif %}">
            {% if rec.severity == 'high' %}Высокий{% elif rec.severity == 'medium' %}Средний{% else %}Низкий{% endif %}
          </span></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  <div class="disclaimer">
    <strong>Важно:</strong> Данный отчёт носит исключительно информационный характер и основан на автоматическом анализе
    открытых данных сайта. Отчёт не является юридическим заключением и не может использоваться в качестве
    официального документа. Для получения юридической консультации обратитесь к квалифицированному специалисту.
    SiteGuard не несёт ответственности за решения, принятые на основании данного отчёта.
  </div>
</div>
</body>
</html>"""


def render_pdf_html(scan_data: dict, result_data: dict) -> str:
    """Render HTML for PDF generation."""
    # autoescape=True prevents XSS from user-controlled fields (url, issue titles, etc.)
    env = Environment(autoescape=True)
    template = env.from_string(PDF_TEMPLATE)

    risk_level = scan_data.get("risk_level", "red")
    score = scan_data.get("score", 0)
    url = scan_data.get("url", "")
    checks = result_data.get("checks", [])
    issues = result_data.get("issues", [])
    recommendations = result_data.get("recommendations", [])
    meta = result_data.get("meta", {})

    return template.render(
        url=url,
        date=datetime.utcnow().strftime("%d.%m.%Y %H:%M UTC"),
        risk_level=risk_level,
        score=score,
        checks=checks,
        issues=issues,
        recommendations=recommendations,
        pages_count=meta.get("pages_count", 1),
        issues_count=len(issues),
    )


async def generate_pdf(scan_data: dict, result_data: dict) -> bytes:
    """Generate PDF bytes using Playwright."""
    from playwright.async_api import async_playwright

    html_content = render_pdf_html(scan_data, result_data)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        pdf_bytes = await page.pdf(
            format="A4",
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            print_background=True,
        )
        await browser.close()

    return pdf_bytes
