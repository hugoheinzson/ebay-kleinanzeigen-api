import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Kleinanzeigen-Helfer',
  description: 'Intelligente Suche für Kleinanzeigen mit erweiterten Filtern und Echtzeit-Ergebnissen',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de" className="h-full bg-gray-50">
      <body className="h-full">
        {children}
      </body>
    </html>
  )
}
