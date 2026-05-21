import Header from '@/components/ui/Header'
import Footer from '@/components/ui/Footer'

export default function PrivacyPage() {
  return (
    <>
      <Header />
      <main className="bg-slate-50 min-h-screen">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 py-16">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">Политика конфиденциальности</h1>
          <p className="text-slate-400 text-sm mb-8">Последнее обновление: 1 января 2025 г.</p>

          <div className="space-y-6">
            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">1. Общие положения</h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                Настоящая политика конфиденциальности описывает, как SiteGuard («Сервис», «мы») собирает,
                использует и защищает информацию, которую вы предоставляете при использовании сервиса.
                Используя сервис, вы соглашаетесь с условиями настоящей политики.
              </p>
            </div>

            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">2. Собираемые данные</h2>
              <p className="text-slate-600 text-sm leading-relaxed mb-2">
                При использовании сервиса мы можем собирать следующие данные:
              </p>
              <ul className="text-slate-600 text-sm space-y-1 list-disc list-inside">
                <li>URL-адреса сайтов, переданных на проверку</li>
                <li>IP-адрес пользователя (для защиты от злоупотреблений)</li>
                <li>Технические данные браузера (User-Agent, язык)</li>
                <li>Результаты автоматического анализа сайтов</li>
              </ul>
            </div>

            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">3. Использование данных</h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                Собранные данные используются исключительно для предоставления услуг сервиса:
                выполнения проверок, формирования отчётов и защиты от злоупотреблений.
                Мы не передаём персональные данные третьим лицам и не используем их в рекламных целях.
              </p>
            </div>

            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">4. Хранение данных</h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                Результаты проверок хранятся в течение 30 дней с момента создания, после чего
                автоматически удаляются. HTML-снимки страниц не хранятся постоянно.
                IP-адреса хранятся не более 24 часов.
              </p>
            </div>

            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">5. Cookie</h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                Сервис использует технические cookie, необходимые для корректной работы.
                Аналитические cookie используются только с вашего согласия.
              </p>
            </div>

            <div className="card">
              <h2 className="text-lg font-bold text-slate-900 mb-3">6. Контакты</h2>
              <p className="text-slate-600 text-sm leading-relaxed">
                По вопросам, связанным с обработкой персональных данных, обращайтесь:
                privacy@siteguard.ru
              </p>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </>
  )
}
