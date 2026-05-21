import Link from 'next/link'

const plans = [
  {
    name: 'Бесплатно',
    price: '0 ₽',
    period: '',
    desc: 'Базовая проверка для ознакомления',
    features: [
      'Одна проверка',
      'Общий балл и уровень риска',
      'Первые 3 нарушения',
      'Список пройденных проверок',
    ],
    cta: 'Начать бесплатно',
    href: '/#hero',
    highlight: false,
  },
  {
    name: 'Стандарт',
    price: '990 ₽',
    period: '/ месяц',
    desc: 'Для владельцев сайтов и малого бизнеса',
    features: [
      '10 проверок в месяц',
      'Полный отчёт со всеми нарушениями',
      'PDF-отчёт',
      'Детальные рекомендации',
      'История проверок',
    ],
    cta: 'Выбрать план',
    href: '/#hero',
    highlight: true,
  },
  {
    name: 'Бизнес',
    price: '2 990 ₽',
    period: '/ месяц',
    desc: 'Для агентств и команд',
    features: [
      'Неограниченные проверки',
      'Полный отчёт со всеми нарушениями',
      'PDF-отчёт с брендингом',
      'API-доступ',
      'Приоритетная поддержка',
    ],
    cta: 'Выбрать план',
    href: '/#hero',
    highlight: false,
  },
]

export default function PricingSection() {
  return (
    <section id="pricing" className="py-20 bg-slate-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">Тарифы</h2>
          <p className="text-lg text-slate-500 max-w-xl mx-auto">
            Начните бесплатно, перейдите на платный план когда будете готовы
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-2xl border p-6 flex flex-col ${
                plan.highlight
                  ? 'bg-teal-600 border-teal-600 text-white shadow-xl scale-105'
                  : 'bg-white border-slate-100 shadow-card'
              }`}
            >
              <div className="mb-6">
                <div className={`text-sm font-semibold mb-1 ${plan.highlight ? 'text-teal-200' : 'text-teal-600'}`}>
                  {plan.name}
                </div>
                <div className="flex items-baseline gap-1 mb-2">
                  <span className={`text-3xl font-bold ${plan.highlight ? 'text-white' : 'text-slate-900'}`}>
                    {plan.price}
                  </span>
                  {plan.period && (
                    <span className={`text-sm ${plan.highlight ? 'text-teal-200' : 'text-slate-500'}`}>
                      {plan.period}
                    </span>
                  )}
                </div>
                <p className={`text-sm ${plan.highlight ? 'text-teal-100' : 'text-slate-500'}`}>{plan.desc}</p>
              </div>

              <ul className="space-y-2.5 mb-8 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm">
                    <svg
                      className={`w-4 h-4 mt-0.5 flex-shrink-0 ${plan.highlight ? 'text-teal-200' : 'text-teal-500'}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className={plan.highlight ? 'text-teal-50' : 'text-slate-600'}>{f}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={plan.href}
                className={`text-center py-3 px-6 rounded-xl font-semibold text-sm transition-colors ${
                  plan.highlight
                    ? 'bg-white text-teal-700 hover:bg-teal-50'
                    : 'bg-teal-600 text-white hover:bg-teal-700'
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
