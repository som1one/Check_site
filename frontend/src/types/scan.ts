export interface Issue {
  code: string
  title: string
  severity: 'high' | 'medium' | 'low'
  category: 'personal_data' | 'cookies' | 'ads' | 'company_info' | 'consumer_rights' | 'technical' | 'age_marking' | 'copyright' | 'payment_security' | 'contacts' | 'user_agreement' | 'server_location' | 'rkn' | 'domain'
  description: string
  recommendation: string
  evidence: string[]
  possible_fine?: number | null
}

export interface Check {
  code: string
  title: string
  status: 'passed' | 'warning' | 'failed'
  details: string
  evidence: string[]
}

export type ScanStatus = 'queued' | 'running' | 'completed' | 'failed'
export type RiskLevel = 'green' | 'yellow' | 'red'

export interface ScanJob {
  id: string
  url: string
  status: ScanStatus
  progress: number
  score?: number | null
  risk_level?: RiskLevel | null
  checks: Check[]
  issues: Issue[]
  created_at: string
  finished_at?: string | null
  error?: string | null
}

export interface ScanCreateResponse {
  scan_id: string
  status: string
}
