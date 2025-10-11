import { Inter } from 'next/font/google'
import { Providers } from '@/components/providers'
import { Toaster } from 'sonner'
import './globals.css'  // Make sure this import is here!

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'AI Code Review Assistant',
  description: 'AI-powered code review assistant for modern development teams',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  )
}
