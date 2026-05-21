'use client'

import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { getScan, getPdfUrl } from '@/lib/api'
import { ScanJob } from '@/types/scan'
import Header from '@/components/ui/Header'
import Footer from '@/components/ui/Footer'
import ProgressBar from '@/components/ui/ProgressBar'
import ScoreBadge from '@/components/ui/ScoreBadge'
import ChecksList from '@/components/ui/ChecksList'
import IssueCard from '@/components/ui/IssueCard'

const POLL_INTERVAL = 2500
const MAX_POLLS = 120 // 5 minutes at 2.5s intervals

export default function ScanPage() {
  const params = useParams()
  const scanId = params?.id as string

  const [scan, setScan] = useState<ScanJob | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchScan = useCallback(async () => {
    try {
      const data = await getScan(scanId)
      setScan(data)
      setError(null)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Ошибка загрузки результатов')
    } finally {
      setLoading(false)
    }
  }, [scanId])

  useEffect(() => {
    if (!scanId) return
    fetchScan()
  }, [fetchScan, scanId])

  useEffect(() => {
    if (!scan) return
    if (scan.status === 'completed' || scan.status === 'failed') return

    let pollCount = 0
    const timer = setInterval(() => {
      if (++pollCount >= MAX_POLLS) {
        clearInterval(timer)
        setError('Превышено время ожидания результатов. Попробуйте обновить страницу.')
        return
      }
      fetchScan()
    }, POLL_INTERVAL)
    return () => clearInterval(timer)
  }, [scan, fetchScan])

  const isRunning = scan?.status === 'queued' || scan?.status === 'running'
  const isCompleted = scan?.status === 'completed'
  const isFailed = scan?.status === 'failed'

  return (
    <>
      <Header />
      <main className="min-h-screen bg-slate-50 py-10">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">

          {/* Back link */}
          <Link href="/" className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-teal-600 transition-colors mb-6">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Новая проверка
          </Link>

          {/* Loading skeleton */}
          {loading && (
            <div className="card animate-pulse">
              <div className="h-6 bg-slate-100 rounded w-1/2 mb-4" />
              <div className="h-4 bg-slate-100 rounded w-3/4 mb-2" />
              <div className="h-4 bg-slate-100 rounded w-1/2" />
            </div>
          )}

          {/* Error state */}
          {error && !loading && (
            <div className="card border-red-200 bg-red-50">
              <div className="flex items-center gap-3 text-red-700">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <div className="font-semibold">Ошибка загрузки</div>
                  <div className="text-sm mt-0.5">{error}</div>
                </div>
              </div>
              <Link href="/" className="btn-primary mt-4 text-sm py-2 px-4 w-fit">
                Попробовать снова
              </Link>
            </div>
          )}

          {scan && (
            <>
              {/* Scan header card */}
              <div className="card mb-4">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="min-w-0">
                    <div className="text-xs text-slate-400 mb-1">Проверяемый сайт</div>
                    <div className="font-semibold text-slate-800 break-all">{scan.url}</div>
                    <div className="text-xs text-slate-400 mt-1">
                      ID: {scan.id} · {new Date(scan.created_at).toLocaleString('ru-RU')}
                    </div>
                  </div>
                  {isCompleted && scan.score != null && scan.risk_level && (
                    <ScoreBadge score={scan.score} riskLevel={scan.risk_level} size="md" />
                  )}
                </div>

                {/* Progress */}
                {isRunning && (
                  <div className="mt-5">
                    <ProgressBar progress={scan.progress} status={scan.status} />
                  </div>
                )}

                {/* Failed */}
                {isFailed && (
                  <div className="mt-4 flex items-start gap-2 text-red-600 bg-red-50 border border-red-100 rounded-xl p-3 text-sm">
                    <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div>
                      <div className="font-semibold">Проверка завершилась с ошибкой</div>
                      {scan.error && <div className="mt-0.5 text-red-500">{scan.error}</div>}
                    </div>
                  </div>
                )}
              </div>

              {/* Results */}
              {isCompleted && (
                <>
                  {/* Summary stats */}
                  <div className="grid grid-cols-4 gap-3 mb-4">
                    <div className="card text-center py-4">
                      <div className="text-2xl font-bold text-slate-900">{scan.checks.length}</div>
                      <div className="text-xs text-slate-500 mt-1">Проверок</div>
                    </div>
                    <div className="card text-center py-4">
                      <div className="text-2xl font-bold text-red-500">
                        {scan.issues.filter(i => i.severity === 'high').length}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">Высокий риск</div>
                    </div>
                    <div className="card text-center py-4">
                      <div className="text-2xl font-bold text-amber-500">
                        {scan.issues.filter(i => i.severity === 'medium').length}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">Средний риск</div>
                    </div>
                    <div className="card text-center py-4">
                      <div className="text-2xl font-bold text-emerald-500">
                        {scan.issues.filter(i => i.severity === 'low').length}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">Низкий риск</div>
                    </div>
                  </div>

                  {/* Issues */}
                  {scan.issues.length > 0 && (
                    <div className="card mb-4">
                      <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                        Выявленные нарушения ({scan.issues.length})
                      </h2>
                      <div className="space-y-3">
                        {[...scan.issues].sort((a, b) => { const order = { high: 0, medium: 1, low: 2 }; return order[a.severity] - order[b.severity] }).map((issue) => (
                          <IssueCard key={issue.code} issue={issue} />
                        ))}
                      </div>
                    </div>
                  )}

                  {scan.issues.length === 0 && (
                    <div className="card mb-4 border-emerald-200 bg-emerald-50 text-center py-8">
                      <div className="text-4xl mb-3">🎉</div>
                      <div className="font-bold text-emerald-800 text-lg">Нарушений не обнаружено</div>
                      <div className="text-sm text-emerald-600 mt-1">Сайт прошёл все автоматические проверки</div>
                    </div>
                  )}

                  {/* Checks list */}
                  <div className="card mb-4">
                    <h2 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
                      <svg className="w-5 h-5 text-teal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
                      </svg>
                      Результаты проверок
                    </h2>
                    <ChecksList checks={scan.checks} />
                  </div>

                  {/* PDF CTA */}
                  <div className="card bg-gradient-to-br from-teal-600 to-teal-700 text-white text-center py-8">
                    <div className="text-xl font-bold mb-2">Получить полный PDF-отчёт</div>
                    <p className="text-teal-100 text-sm mb-5 max-w-sm mx-auto">
                      Скачайте подробный отчёт с рекомендациями для передачи разработчикам или юристам
                    </p>
                    <a
                      href={getPdfUrl(scan.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 bg-white text-teal-700 font-semibold py-3 px-6 rounded-xl hover:bg-teal-50 transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      Скачать PDF
                    </a>
                  </div>

                  {/* Disclaimer */}
                  <div className="mt-4 text-xs text-slate-400 text-center leading-relaxed">
                    Отчёт носит информационный характер и основан на автоматическом анализе открытых данных сайта.
                    Не является юридическим заключением.
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </main>
      <Footer />
    </>
  )
}
