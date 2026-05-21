import ScanForm from '@/components/ui/ScanForm'

export default function HeroSection() {
  return (
    <section id="hero" className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-teal-900 py-24 sm:py-32">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-teal-500/10 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-teal-600/10 blur-3xl" />
      </div>

      <div className="relative max-w-4xl mx-auto px-4 sm:px-6 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-teal-500/20 border border-teal-500/30 text-teal-300 text-xs font-medium mb-6">
          <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
          Бесплатная проверка · Без регистрации
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 leading-tight">
          Проверьте сайт на{' '}
          <span className="text-teal-400">юридические риски</span>{' '}
          за 60 секунд
        </h1>

        <p className="text-lg sm:text-xl text-slate-300 mb-10 max-w-2xl mx-auto leading-relaxed">
          Автоматический аудит: политика конфиденциальности, cookie-баннер, реквизиты компании,
          HTTPS, маркировка рекламы и права потребителей.
        </p>

        <ScanForm />

        <div className="mt-10 flex flex-wrap items-center justify-center gap-6 text-sm text-slate-400">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            8 категорий проверок
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Светофор рисков
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            PDF-отчёт
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Рекомендации
          </div>
        </div>
      </div>
    </section>
  )
}
