import Link from 'next/link'

const exampleChecks = [
  { title: 'HTTPS', status: 'passed' },
  { title: 'Политика конфиденциальности', status: 'failed' },
  { title: 'Согласие в формах', status: 'failed' },
  { title: 'Cookie-баннер', status: 'warning' },
  { title: 'Маркировка рекламы', status: 'passed' },
  { title: 'Реквизиты компании', status: 'warning' },
]

const statusConfig = {
  passed: { label: 'Пройдено', cls: 'badge-passed', dot: 'bg-emerald-500' },
  warning: { label: 'Предупреждение', cls: 'badge-warning', dot: 'bg-amber-500' },
  failed: { label: 'Не пройдено', cls: 'badge-failed', dot: 'bg-red-500' },
}

export default function ExampleReportSection() {
  return (
    <section id="example" className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">Пример отчёта</h2>
          <p className="text-lg text-slate-500 max-w-xl mx-auto">
            Так выглядит результат проверки сайта
          </p>
        </div>

        <div className="max-w-2xl mx-auto">
          <div className="card shadow-lg">
            {/* Header */}
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100">
              <div>
                <div className="text-xs text-slate-400 mb-1">Проверяемый сайт</div>
                <div className="font-semibold text-slate-800">example-shop.ru</div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-16 h-16 rounded-full bg-amber-500 flex items-center justify-center text-white text-2xl font-bold ring-4 ring-amber-100">
                  62
                </div>
                <div>
                  <div className="badge-warning">Средний риск</div>
                  <div className="text-xs text-slate-400 mt-1">4 нарушения</div>
                </div>
              </div>
            </div>

            {/* Checks */}
            <div className="space-y-2 mb-6">
              {exampleChecks.map((check) => {
                const cfg = statusConfig[check.status as keyof typeof statusConfig]
                return (
                  <div key={check.title} className="flex items-center justify-between py-2 px-3 rounded-lg bg-slate-50">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                      <span className="text-sm text-slate-700">{check.title}</span>
                    </div>
                    <span className={`${cfg.cls} flex-shrink-0`}>{cfg.label}</span>
                  </div>
                )
              })}
            </div>

            {/* CTA */}
            <div className="bg-teal-50 border border-teal-100 rounded-xl p-4 text-center">
              <p className="text-sm text-teal-800 font-medium mb-3">
                Проверьте свой сайт и получите полный отчёт
              </p>
              <Link href="/#hero" className="btn-primary text-sm py-2 px-5">
                Проверить бесплатно
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
