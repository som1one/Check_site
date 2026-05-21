import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-400 text-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2 font-bold text-lg text-white mb-3">
              <span className="w-7 h-7 rounded-lg bg-teal-600 flex items-center justify-center text-white text-xs font-bold">
                SG
              </span>
              <span>
                Site<span className="text-teal-400">Guard</span>
              </span>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed max-w-xs">
              Автоматическая проверка сайтов на юридико-технические риски. Отчёт носит информационный
              характер и не является юридическим заключением.
            </p>
          </div>

          <div>
            <div className="font-semibold text-white mb-3">Сервис</div>
            <ul className="space-y-2">
              <li><Link href="/#how-it-works" className="hover:text-teal-400 transition-colors">Как работает</Link></li>
              <li><Link href="/#checks" className="hover:text-teal-400 transition-colors">Что проверяем</Link></li>
              <li><Link href="/pricing" className="hover:text-teal-400 transition-colors">Тарифы</Link></li>
              <li><Link href="/about" className="hover:text-teal-400 transition-colors">О сервисе</Link></li>
            </ul>
          </div>

          <div>
            <div className="font-semibold text-white mb-3">Документы</div>
            <ul className="space-y-2">
              <li><Link href="/privacy" className="hover:text-teal-400 transition-colors">Политика конфиденциальности</Link></li>
              <li><Link href="/offer" className="hover:text-teal-400 transition-colors">Публичная оферта</Link></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-slate-800 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>© {new Date().getFullYear()} SiteGuard. Все права защищены.</p>
          <p className="text-xs text-slate-500 text-center sm:text-right">
            Отчёты носят информационный характер и не являются юридическим заключением.
          </p>
        </div>
      </div>
    </footer>
  )
}
