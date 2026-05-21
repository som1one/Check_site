'use client'

import Link from 'next/link'
import { useState } from 'react'

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur border-b border-slate-100">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl text-slate-900">
          <span className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white text-sm font-bold">
            SG
          </span>
          <span>
            Site<span className="text-teal-600">Guard</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-600">
          <Link href="/#how-it-works" className="hover:text-teal-600 transition-colors">
            Как работает
          </Link>
          <Link href="/#checks" className="hover:text-teal-600 transition-colors">
            Что проверяем
          </Link>
          <Link href="/pricing" className="hover:text-teal-600 transition-colors">
            Тарифы
          </Link>
          <Link href="/about" className="hover:text-teal-600 transition-colors">
            О сервисе
          </Link>
        </nav>

        <div className="hidden md:flex items-center gap-3">
          <Link href="/#hero" className="btn-primary text-sm py-2 px-4">
            Проверить сайт
          </Link>
        </div>

        {/* Mobile burger */}
        <button
          className="md:hidden p-2 rounded-lg hover:bg-slate-100 transition-colors"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Меню"
        >
          <div className="w-5 h-0.5 bg-slate-700 mb-1" />
          <div className="w-5 h-0.5 bg-slate-700 mb-1" />
          <div className="w-5 h-0.5 bg-slate-700" />
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden bg-white border-t border-slate-100 px-4 py-4 flex flex-col gap-3 text-sm font-medium text-slate-700">
          <Link href="/#how-it-works" onClick={() => setMenuOpen(false)} className="hover:text-teal-600">
            Как работает
          </Link>
          <Link href="/#checks" onClick={() => setMenuOpen(false)} className="hover:text-teal-600">
            Что проверяем
          </Link>
          <Link href="/pricing" onClick={() => setMenuOpen(false)} className="hover:text-teal-600">
            Тарифы
          </Link>
          <Link href="/about" onClick={() => setMenuOpen(false)} className="hover:text-teal-600">
            О сервисе
          </Link>
          <Link href="/#hero" onClick={() => setMenuOpen(false)} className="btn-primary text-sm py-2 px-4 w-fit">
            Проверить сайт
          </Link>
        </div>
      )}
    </header>
  )
}
