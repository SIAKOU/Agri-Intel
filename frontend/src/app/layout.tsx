import type { Metadata } from 'next'
import { Inter, Poppins } from 'next/font/google'
import { ThemeProvider } from '@/components/providers/theme-provider'
import { QueryProvider } from '@/components/providers/query-provider'
import { AuthProvider } from '@/components/providers/auth-provider'
import { ToasterProvider } from '@/components/providers/toaster-provider'
import '../styles/globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

const poppins = Poppins({
  subsets: ['latin'],
  variable: '--font-heading',
  weight: ['300', '400', '500', '600', '700', '800'],
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'AgriIntel360 - Plateforme Intelligente de Décision Agricole',
  description: 'Solution complète de business intelligence et d\'analyse prédictive pour l\'agriculture africaine.',
  keywords: [
    'agriculture',
    'afrique',
    'business intelligence',
    'analyse prédictive',
    'données agricoles',
    'rendements',
    'prix',
    'météo',
  ],
  authors: [{ name: 'AgriIntel360 Team' }],
  creator: 'AgriIntel360',
  publisher: 'AgriIntel360',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL('http://localhost:3000'),
  openGraph: {
    type: 'website',
    locale: 'fr_FR',
    url: 'http://localhost:3000',
    siteName: 'AgriIntel360',
    title: 'AgriIntel360 - Intelligence Agricole pour l\'Afrique',
    description: 'Optimisez vos décisions agricoles avec notre plateforme d\'analyse prédictive et de business intelligence.',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'AgriIntel360',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'AgriIntel360 - Intelligence Agricole',
    description: 'Plateforme de business intelligence pour l\'agriculture africaine',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
  manifest: '/site.webmanifest',
}

interface RootLayoutProps {
  children: React.ReactNode
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html 
      lang="fr" 
      className={`${inter.variable} ${poppins.variable}`}
      suppressHydrationWarning
    >
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      </head>
      <body className="min-h-screen bg-background font-sans antialiased">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            <AuthProvider>
              <div className="relative flex min-h-screen flex-col">
                {children}
              </div>
              <ToasterProvider />
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
        
        {/* Global scripts */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              // Prevent flash of unstyled content
              try {
                if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.documentElement.classList.add('dark')
                } else {
                  document.documentElement.classList.remove('dark')
                }
              } catch (_) {}
            `,
          }}
        />
      </body>
    </html>
  )
}