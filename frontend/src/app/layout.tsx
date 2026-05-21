import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SiteGuard — Автоматическая проверка сайта',
  description:
    'Бесплатная автоматическая проверка сайта на юридико-технические риски: политика конфиденциальности, cookie, реквизиты, HTTPS и многое другое.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-slate-50 text-slate-900 font-sans antialiased">{children}</body>
    </html>
  )
}
