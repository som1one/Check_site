const checks = [
  {
    icon: '🛡️',
    title: '152-ФЗ и персональные данные',
    desc: 'Политика обработки ПДн, согласие в формах, уведомление Роскомнадзора.',
    category: 'personal_data',
  },
  {
    icon: '🍪',
    title: 'Cookie-политика',
    desc: 'Наличие cookie-баннера с кнопками принятия и отказа.',
    category: 'cookies',
  },
  {
    icon: '📢',
    title: 'Маркировка рекламы',
    desc: 'ERID-токен и сведения о рекламодателе по 38-ФЗ.',
    category: 'ads',
  },
  {
    icon: '🇷🇺',
    title: 'Сервер в РФ',
    desc: 'Локализация серверов с персональными данными граждан РФ (ст. 18.5).',
    category: 'personal_data',
  },
  {
    icon: '🏢',
    title: 'Реквизиты компании',
    desc: 'ИНН, ОГРН, юридический адрес и руководитель по 149-ФЗ.',
    category: 'company_info',
  },
  {
    icon: '🛒',
    title: 'Права потребителей',
    desc: 'Оферта, возврат, доставка, оплата, гарантия по ЗоЗПП.',
    category: 'consumer_rights',
  },
]

const categoryColors: Record<string, string> = {
  personal_data: 'bg-blue-50 text-blue-600',
  cookies: 'bg-amber-50 text-amber-600',
  ads: 'bg-purple-50 text-purple-600',
  company_info: 'bg-teal-50 text-teal-600',
  consumer_rights: 'bg-emerald-50 text-emerald-600',
}

export default function ChecksSection() {
  return (
    <section id="checks" className="py-20 bg-slate-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">Что проверяем</h2>
          <p className="text-lg text-slate-500 max-w-xl mx-auto">
            Ключевые требования российского законодательства и Роскомнадзора
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {checks.map((check) => (
            <div key={check.title} className="card hover:shadow-card-hover transition-shadow">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-xl mb-3 ${categoryColors[check.category]}`}>
                {check.icon}
              </div>
              <h3 className="font-semibold text-slate-900 text-sm mb-1.5">{check.title}</h3>
              <p className="text-xs text-slate-500 leading-relaxed">{check.desc}</p>
            </div>
          ))}
        </div>

        <p className="text-center text-xs text-slate-400 mt-8">
          Отчёт носит информационный характер и основан на автоматическом анализе открытых данных сайта.
          Не является юридическим заключением.
        </p>
      </div>
    </section>
  )
}
