interface ProgressBarProps {
  progress: number
  status: string
}

const statusMessages: Record<string, string> = {
  queued: 'В очереди...',
  running: 'Анализируем сайт...',
  completed: 'Проверка завершена',
  failed: 'Ошибка проверки',
}

export default function ProgressBar({ progress, status }: ProgressBarProps) {
  const message = statusMessages[status] || 'Обработка...'

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-700">{message}</span>
        <span className="text-sm font-semibold text-teal-600">{progress}%</span>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
        <div
          className="h-2.5 rounded-full bg-gradient-to-r from-teal-500 to-teal-400 transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
      {status === 'running' && (
        <div className="mt-3 flex items-center gap-2 text-xs text-slate-500">
          <svg className="w-3.5 h-3.5 animate-spin text-teal-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Проверяем страницы, формы, документы и технические параметры...
        </div>
      )}
    </div>
  )
}
