import { ScanCreateResponse, ScanJob } from '@/types/scan'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function createScan(url: string): Promise<ScanCreateResponse> {
  const res = await fetch(`${API_URL}/api/scans`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data?.detail || `Ошибка сервера: ${res.status}`)
  }

  return res.json()
}

export async function getScan(scanId: string): Promise<ScanJob> {
  const res = await fetch(`${API_URL}/api/scans/${scanId}`, {
    cache: 'no-store',
  })

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data?.detail || `Ошибка сервера: ${res.status}`)
  }

  return res.json()
}

export function getPdfUrl(scanId: string): string {
  return `${API_URL}/api/scans/${scanId}/pdf`
}
