import Header from '@/components/ui/Header'
import Footer from '@/components/ui/Footer'

export default function OfferPage() {
  return (
    <>
      <Header />
      <main className="bg-slate-50 min-h-screen">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-16">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Публичная оферта</h1>
          <p className="text-slate-400 text-sm mb-8">Последнее обновление: 1 января 2025 г.</p>

          <div className="space-y-6">
            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">1. Предмет оферты</h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                Настоящая публичная оферта является предложением SiteGuard («Исполнитель») заключить
                договор на оказание информационных услуг по автоматическому анализу сайтов на
                соответствие требованиям законодательства.
              </p>
            </div>

            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">2. Акцепт оферты</h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                Акцептом настоящей оферты является использование сервиса, в том числе запуск
                проверки сайта. Использование сервиса означает полное и безоговорочное принятие
                условий настоящей оферты.
              </p>
            </div>

            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">3. Услуги</h2>
              <p className="text-slate-600 text-sm leading-relaxed mb-2">
                Исполнитель оказывает следующие информационные услуги:
              </p>
              <ul className="text-slate-600 text-sm space-y-1 list-disc list-inside">
                <li>Автоматический анализ публично доступных страниц сайта</li>
                <li>Формирование информационного отчёта о выявленных признаках несоответствия</li>
                <li>Предоставление рекомендаций по устранению выявленных признаков</li>
                <li>Генерация PDF-отчёта</li>
              </ul>
            </div>

            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">4. Ограничение ответственности</h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                Все отчёты носят исключительно информационный характер. Исполнитель не несёт
                ответственности за решения, принятые на основании отчётов. Отчёты не являются
                юридическим заключением. Исполнитель не гарантирует полноту и точность автоматического
                анализа.
              </p>
            </div>

            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">5. Запрещённое использование</h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                Запрещается использовать сервис для проверки сайтов без согласия их владельцев
                в целях причинения вреда, а также для автоматизированного массового сбора данных.
                Запрещается проверка сайтов, содержащих незаконный контент.
              </p>
            </div>

            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">6. Контакты</h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                По вопросам, связанным с условиями оферты: legal@siteguard.ru
              </p>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  )
}
