import { Check } from '@/types/scan'

interface ChecksListProps {
  checks: Check[]
}

const statusConfig = {
  passed: { label: 'Пройдено', className: 'badge-passed', icon: '✓' },
  warning: { label: 'Предупреждение', className: 'badge-warning', icon: '!' },
  failed: { label: 'Не пройдено', className: 'badge-failed', icon: '✗' },
}

export default function ChecksList({ checks }: ChecksListProps) {
  if (!checks.length) return null

  return (
    <div className="space-y-2">
      {checks.map((check) => {
        const cfg = statusConfig[check.status]
        return (
           <div
             key={check.code}
             className="flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100"
           >
             <div className="min-w-0">
               <div className="font-medium text-sm text-slate-800">{check.title}</div>
               <div className="text-xs text-slate-500 mt-0.5">{check.details}</div>
             </div>
             <span className={`${cfg.className} flex-shrink-0`}>
               {cfg.icon} {cfg.label}
             </span>
           </div>
        )
      })}
    </div>
  )
}
