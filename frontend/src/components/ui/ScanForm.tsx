'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { createScan } from '@/lib/api'

export default function ScanForm() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    const trimmed = url.trim()
    if (!trimmed) {
      setError('Введите адрес сайта')
      return
    }

    setLoading(true)
    try {
      const result = await createScan(trimmed)
      router.push(`/scan/${result.scan_id}`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Произошла ошибка. Попробуйте ещё раз.')
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-2xl mx-auto">
      <div className="flex flex-col sm:flex-row gap-3 bg-white rounded-2xl p-2 shadow-lg border border-slate-100">
        <div className="flex-1 flex items-center gap-3 px-3">
          <svg className="w-5 h-5 text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="example.com или https://example.com"
            className="flex-1 py-2 text-slate-900 placeholder-slate-400 bg-transparent outline-none text-base"
            disabled={loading}
            autoComplete="url"
            spellCheck={false}
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="btn-primary whitespace-nowrap"
        >
          {loading ? (
            <>
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Запускаем...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Проверить сайт
            </>
          )}
        </button>
      </div>
      {error && (
        <div className="mt-3 flex items-center gap-2 text-red-600 text-sm bg-red-50 border border-red-100 rounded-xl px-4 py-2.5">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}
      <p className="mt-3 text-center text-xs text-slate-400">
        Бесплатная проверка · Без регистрации · Результат за 30–60 секунд
      </p>
    </form>
  )
}
