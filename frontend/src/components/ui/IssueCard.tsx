import { Issue } from '@/types/scan'

interface IssueCardProps {
  issue: Issue
  compact?: boolean
}

const severityConfig = {
  high: { label: 'Высокий', className: 'badge-failed', border: 'border-red-200 bg-red-50' },
  medium: { label: 'Средний', className: 'badge-warning', border: 'border-amber-200 bg-amber-50' },
  low: { label: 'Низкий', className: 'badge-passed', border: 'border-emerald-200 bg-emerald-50' },
}

const categoryLabels: Record<string, string> = {
  personal_data: 'Персональные данные',
  cookies: 'Cookie',
  ads: 'Реклама',
  company_info: 'Реквизиты компании',
  consumer_rights: 'Права потребителей',
  technical: 'Технические',
  age_marking: 'Возрастная маркировка',
  copyright: 'Копирайт',
  payment_security: 'Безопасность платежей',
  contacts: 'Контакты',
  user_agreement: 'Пользовательское соглашение',
  server_location: 'Серверы (152-ФЗ)',
  rkn: 'Роскомнадзор',
  domain: 'Доменные требования',
}

export default function IssueCard({ issue, compact = false }: IssueCardProps) {
  const cfg = severityConfig[issue.severity]

  return (
    <div className={`rounded-xl border p-4 ${cfg.border}`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-slate-500">{categoryLabels[issue.category] || issue.category}</span>
        </div>
        <span className={`${cfg.className} flex-shrink-0`}>{cfg.label} риск</span>
      </div>
      <h4 className="font-semibold text-sm text-slate-800 mb-1">{issue.title}</h4>
      {!compact && (
        <>
          <p className="text-xs text-slate-600 mb-2">{issue.description}</p>
          <div className="text-xs text-teal-700 font-medium">
            Рекомендация: {issue.recommendation}
          </div>
          {issue.possible_fine && (
            <div className="mt-1.5 text-xs text-red-600 font-medium">
              Возможный штраф: до {issue.possible_fine.toLocaleString('ru-RU')} ₽
            </div>
          )}
        </>
      )}
    </div>
  )
}
