import { RiskLevel } from '@/types/scan'

interface ScoreBadgeProps {
  score: number
  riskLevel: RiskLevel
  size?: 'sm' | 'md' | 'lg'
}

const riskConfig = {
  green: {
    label: 'Низкий риск',
    bg: 'bg-emerald-500',
    ring: 'ring-emerald-200',
    text: 'text-emerald-700',
    lightBg: 'bg-emerald-50',
  },
  yellow: {
    label: 'Средний риск',
    bg: 'bg-amber-500',
    ring: 'ring-amber-200',
    text: 'text-amber-700',
    lightBg: 'bg-amber-50',
  },
  red: {
    label: 'Высокий риск',
    bg: 'bg-red-500',
    ring: 'ring-red-200',
    text: 'text-red-700',
    lightBg: 'bg-red-50',
  },
}

export default function ScoreBadge({ score, riskLevel, size = 'md' }: ScoreBadgeProps) {
  const config = riskConfig[riskLevel]

  const sizeClasses = {
    sm: 'w-14 h-14 text-xl',
    md: 'w-20 h-20 text-2xl',
    lg: 'w-28 h-28 text-4xl',
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={`${sizeClasses[size]} ${config.bg} rounded-full flex items-center justify-center text-white font-bold ring-4 ${config.ring}`}
      >
        {score}
      </div>
      <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${config.lightBg} ${config.text}`}>
        {config.label}
      </span>
    </div>
  )
}
