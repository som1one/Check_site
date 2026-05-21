import Header from '@/components/ui/Header'
import Footer from '@/components/ui/Footer'

export default function AboutPage() {
  return (
    <>
      <Header />
      <main className="bg-slate-50 min-h-screen">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-16">
          <h1 className="text-4xl font-bold text-slate-900 mb-6">О сервисе SiteGuard</h1>

          <div className="card mb-6">
            <h2 className="text-xl font-bold text-slate-900 mb-3">Что такое SiteGuard?</h2>
            <p className="text-slate-600 leading-relaxed">
              SiteGuard — это автоматический сервис проверки сайтов на соответствие требованиям
              российского законодательства в области защиты персональных данных, прав потребителей
              и интернет-рекламы.
            </p>
          </div>

          <div className="card mb-6">
            <h2 className="text-xl font-bold text-slate-900 mb-3">Как работает проверка?</h2>
            <p className="text-slate-600 leading-relaxed mb-3">
              Сервис автоматически обходит страницы сайта, анализирует HTML-код, текстовое содержимое,
              структуру ссылок и технические параметры. На основе анализа формируется отчёт с оценкой
              рисков и рекомендациями.
            </p>
            <p className="text-slate-600 leading-relaxed">
              Проверка занимает 30–60 секунд и не требует установки дополнительного ПО или регистрации.
            </p>
          </div>

          <div className="card mb-6">
            <h2 className="text-xl font-bold text-slate-900 mb-3">Что проверяется?</h2>
            <ul className="space-y-2 text-slate-600">
              {[
                'Политика обработки персональных данных (152-ФЗ)',
                'Согласие на обработку данных в формах (152-ФЗ, ст. 9)',
                'Локализация серверов с ПДн в РФ (152-ФЗ, ст. 18.5)',
                'Уведомление Роскомнадзора об обработке ПДн (152-ФЗ, ст. 22)',
                'Cookie-баннер с возможностью отказа',
                'Маркировка рекламных материалов ERID (38-ФЗ)',
                'Реквизиты компании: ИНН, ОГРН, адрес (149-ФЗ)',
                'Документы для потребителей: оферта, возврат, доставка, оплата (ЗоЗПП)',
              ].map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-teal-500 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="card border-amber-200 bg-amber-50">
            <h2 className="text-lg font-bold text-amber-900 mb-2">Важное уведомление</h2>
            <p className="text-amber-800 text-sm leading-relaxed">
              Все отчёты SiteGuard носят исключительно информационный характер и основаны на
              автоматическом анализе открытых данных сайта. Отчёты не являются юридическим
              заключением и не могут использоваться в качестве официального документа.
              Для получения юридической консультации обратитесь к квалифицированному специалисту.
            </p>
          </div>
        </div>
      </main>
      <Footer />
    </>
  )
}
